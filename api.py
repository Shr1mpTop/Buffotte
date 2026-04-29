from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import asyncio
import logging
import math
import traceback
from contextlib import asynccontextmanager
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pymysql
from datetime import date, datetime
import pytz
from app.core.config import settings
from app.dependencies import (
    get_bufftracker_client,
    get_item_crawler,
    get_item_kline_processor,
    get_kline_processor,
    get_profit_processor,
    get_trade_notes_processor,
    get_user_actions,
    get_user_manager,
)
from app.routers.auth import router as auth_router
from app.routers.bufftracker import router as bufftracker_router
from app.routers.system import router as system_router
from app.routers.users import router as users_router

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Best-effort schema bootstrap without making module import require MySQL."""
    loop = asyncio.get_running_loop()

    def _ensure_tables():
        bootstrappers = [
            ("用户表", user_manager.create_user_table),
            ("追踪表", user_actions.create_track_table),
            ("利润表", profit_processor.ensure_tables),
            ("买卖笔记表", trade_notes_processor.ensure_tables),
        ]
        for label, bootstrap in bootstrappers:
            try:
                bootstrap()
            except Exception:
                logging.exception("%s初始化失败，服务将继续启动", label)

    try:
        await loop.run_in_executor(None, _ensure_tables)
    except Exception:
        logging.exception("核心数据表初始化失败，服务将继续启动并在请求时返回具体错误")

    yield


app = FastAPI(lifespan=lifespan)

# 挂载在线文档 Wiki
from wiki import mount_wiki
mount_wiki(app)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    response = await call_next(request)
    logging.info(f"{request.method} {request.url.path} → {response.status_code}")
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Log stack trace for debugging, but return a safe message to client
    logging.error(f"Unhandled exception while processing {request.method} {request.url} - {exc}")
    logging.error(traceback.format_exc())
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(bufftracker_router)
app.include_router(system_router)
app.include_router(users_router)

user_manager = get_user_manager()
kline_processor = get_kline_processor()
item_kline_processor = get_item_kline_processor()
item_crawler = get_item_crawler()
user_actions = get_user_actions()
profit_processor = get_profit_processor()
trade_notes_processor = get_trade_notes_processor()
bufftracker_client = get_bufftracker_client()

# 延迟建表：不在模块加载时连接数据库，首次请求时再建
_tables_ensured = False

@app.middleware("http")
async def ensure_profit_tables(request: Request, call_next):
    global _tables_ensured
    if not _tables_ensured:
        try:
            profit_processor.ensure_tables()
            _tables_ensured = True
        except Exception:
            pass  # 数据库暂不可用，不阻塞其他请求
    return await call_next(request)

class TrackRequest(BaseModel):
    email: str
    market_hash_name: str


class TradeNoteRequest(BaseModel):
    email: str
    market_hash_name: str
    item_name: Optional[str] = None
    side: str
    platform: str = "BUFF"
    trade_date: Optional[str] = None
    quantity: float
    unit_price: float
    note: Optional[str] = None

@app.get("/api/kline/chart-data")
async def get_chart_data():
    """
    统一的图表数据接口，一次性返回历史K线和预测数据。
    """
    conn = None  # Ensure conn is defined
    try:
        conn = kline_processor.get_db_connection()
        
        # 1. 获取历史数据
        with conn.cursor() as cursor:
            # 获取最新的 1000 条历史数据
            cursor.execute("""
                SELECT timestamp, open_price, high_price, low_price, close_price, volume, turnover 
                FROM (
                    SELECT * FROM kline_data_day ORDER BY timestamp DESC LIMIT 1000
                ) AS sub 
                ORDER BY timestamp ASC
            """)
            rows = cursor.fetchall()
        
        historical_data = []
        for row in rows:
            historical_data.append({
                'timestamp': row[0] ,
                'open': float(row[1]),
                'high': float(row[2]),
                'low': float(row[3]),
                'close': float(row[4]),
                'volume': row[5],
                'turnover': float(row[6])
            })

        # 2. 获取预测数据
        prediction_data = []
        with conn.cursor(pymysql.cursors.DictCursor) as cursor: # 使用 DictCursor 更方便
            # 只获取今天及未来的预测
            cursor.execute("SELECT * FROM kline_data_prediction ORDER BY date")
            predictions = cursor.fetchall()

        for pred in predictions:
            # 将 date 对象转换为毫秒时间戳
            ts = int(datetime.combine(pred['date'], datetime.min.time()).timestamp())
            prediction_data.append({
                "timestamp": ts,
                "predicted_close_price": float(pred['predicted_close_price']) if pred['predicted_close_price'] is not None else None,
                "rolling_std_7": float(pred['rolling_std_7']) if pred['rolling_std_7'] is not None else None,
            })
            
        return {"historical": historical_data, "prediction": prediction_data}

    except pymysql.err.OperationalError as e:
        raise HTTPException(status_code=503, detail=f"数据库不可用: {e}")
    except Exception as e:
        logging.exception("获取图表数据失败")
        raise HTTPException(status_code=500, detail=f"获取图表数据失败: {e}")
    finally:
        if conn and conn.open:
            conn.close()

@app.post("/api/kline/refresh")
async def refresh_kline_data():
    try:
        import subprocess
        import os
        # 获取项目根目录
        base_dir = os.path.dirname(os.path.abspath(__file__))
        # 执行数据更新脚本
        result = subprocess.run(
            ["python", "-m", "db.kline_data_processor"],
            cwd=base_dir,
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            return {"success": True, "message": "数据刷新成功"}
        else:
            raise HTTPException(status_code=500, detail=f"数据刷新失败: {result.stderr}")
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="数据刷新超时")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据刷新失败: {e}")


@app.get("/api/kline/latest")
async def get_kline_latest():
    """
    轻量级接口：仅返回 kline_data_day 最新一条记录。
    用于前端秒级轮询，避免每次传全量数据。
    """
    conn = None
    try:
        conn = kline_processor.get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT timestamp, open_price, high_price, low_price, close_price, volume, turnover
                FROM kline_data_day
                ORDER BY timestamp DESC
                LIMIT 1
            """)
            row = cursor.fetchone()
            if not row:
                return {"success": True, "data": None}
            return {
                "success": True,
                "data": {
                    "timestamp": row[0],
                    "open": float(row[1]),
                    "high": float(row[2]),
                    "low": float(row[3]),
                    "close": float(row[4]),
                    "volume": row[5],
                    "turnover": float(row[6])
                }
            }
    except Exception as e:
        logging.exception("获取最新K线数据失败")
        raise HTTPException(status_code=500, detail=f"获取最新数据失败: {e}")
    finally:
        if conn and conn.open:
            conn.close()


@app.get("/api/kline/market-analysis")
async def get_market_analysis():
    """获取最新的 LLM 大盘分析。"""
    try:
        from db.market_analysis_processor import MarketAnalysisProcessor
        processor = MarketAnalysisProcessor()
        result = processor.get_latest_analysis()
        if result:
            return {
                "success": True,
                "analysis": result['analysis'],
                "date": result['analysis_date'].isoformat() if result['analysis_date'] else None
            }
        return {"success": True, "analysis": "", "date": None}
    except Exception as e:
        logging.exception("获取市场分析失败")
        raise HTTPException(status_code=500, detail=f"获取市场分析失败: {e}")

@app.get("/api/summary/latest")
async def get_latest_summary():
    conn = None
    try:
        conn = user_manager.get_db_connection()
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            # 获取东八区今天的日期
            today_utc8 = datetime.now(pytz.timezone('Asia/Shanghai')).date()
            # 优先按 summary_date 匹配今天，若无则取最近一条
            cursor.execute("""
                SELECT id, summary FROM summary 
                WHERE summary_date = %s
                ORDER BY created_at DESC 
                LIMIT 1
            """, (today_utc8,))
            result = cursor.fetchone()
            if not result:
                # fallback：取最新的一条（兼容旧数据没有 summary_date 的情况）
                cursor.execute("SELECT id, summary FROM summary ORDER BY created_at DESC LIMIT 1")
                result = cursor.fetchone()
            if result:
                return {"summary": result['summary'], "summary_id": result['id']}
            else:
                raise HTTPException(status_code=404, detail="未找到摘要")
    except pymysql.err.OperationalError as e:
        raise HTTPException(status_code=503, detail=f"数据库不可用: {e}")
    except Exception as e:
        logging.exception("获取最新摘要失败")
        raise HTTPException(status_code=500, detail=f"获取最新摘要失败: {e}")
    finally:
        if conn and conn.open:
            conn.close()

@app.get("/api/news")
async def get_news(
    page: int = 1,
    size: int = 10,
    summary_id: int = None,
    category: str = None,
    days: int = None,
):
    conn = None
    try:
        conn = user_manager.get_db_connection()
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            # 构建 WHERE 子句
            conditions = []
            params = []
            if category:
                conditions.append("category = %s")
                params.append(category)
            if days:
                conditions.append("publish_time >= DATE_SUB(NOW(), INTERVAL %s DAY)")
                params.append(days)
            where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""

            offset = (page - 1) * size
            cursor.execute(
                f"SELECT id, title, url, source, publish_time, summary as preview, category "
                f"FROM news {where_clause} ORDER BY publish_time DESC LIMIT %s OFFSET %s",
                (*params, size, offset)
            )
            news_list = cursor.fetchall()
            
            # 如果提供了summary_id，查询关联的新闻ID
            highlighted_news_ids = set()
            if summary_id:
                cursor.execute(
                    "SELECT news_id FROM summary_news_association WHERE summary_id = %s",
                    (summary_id,)
                )
                highlighted_news_ids = {row['news_id'] for row in cursor.fetchall()}
            
            # 标记新闻是否被洞察提及
            for news in news_list:
                news['highlighted'] = news['id'] in highlighted_news_ids
            
            # 获取总数用于分页
            cursor.execute(f"SELECT COUNT(*) as total FROM news {where_clause}", params)
            total = cursor.fetchone()['total']
            
            return {
                "items": news_list,
                "total": total,
                "page": page,
                "size": size
            }
    except pymysql.err.OperationalError as e:
        logging.error(f"Database operational error in get_news: {e}")
        raise HTTPException(status_code=503, detail=f"数据库不可用: {e}")
    except Exception as e:
        logging.exception("获取新闻列表失败")
        raise HTTPException(status_code=500, detail=f"获取新闻列表失败: {e}")
    finally:
        if conn and conn.open:
            conn.close()


@app.get("/api/news/stats")
async def get_news_stats():
    """新闻数据看板统计：分类分布、来源 Top、时间线、总数等。"""
    conn = None
    try:
        conn = user_manager.get_db_connection()
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            # 总数
            cursor.execute("SELECT COUNT(*) as total FROM news")
            total = cursor.fetchone()['total']

            # 分类分布
            cursor.execute(
                "SELECT IFNULL(category, '未分类') as category, COUNT(*) as count "
                "FROM news GROUP BY category ORDER BY count DESC"
            )
            category_dist = cursor.fetchall()

            # 来源 Top 8
            cursor.execute(
                "SELECT source, COUNT(*) as count FROM news "
                "WHERE source IS NOT NULL AND source != '' "
                "GROUP BY source ORDER BY count DESC LIMIT 8"
            )
            source_top = cursor.fetchall()

            # 最近 7 天每天的新闻量
            cursor.execute(
                "SELECT DATE(publish_time) as day, COUNT(*) as count "
                "FROM news WHERE publish_time >= DATE_SUB(NOW(), INTERVAL 7 DAY) "
                "AND publish_time <= NOW() "
                "GROUP BY DATE(publish_time) ORDER BY day"
            )
            daily_trend = cursor.fetchall()

            # 最近新闻时间
            cursor.execute(
                "SELECT MAX(publish_time) as latest, MIN(publish_time) as earliest "
                "FROM news WHERE publish_time BETWEEN '2020-01-01' AND '2030-01-01'"
            )
            time_range = cursor.fetchone()

            # 可用分类列表
            cursor.execute(
                "SELECT DISTINCT category FROM news WHERE category IS NOT NULL AND category != '' ORDER BY category"
            )
            categories = [row['category'] for row in cursor.fetchall()]

            return {
                "total": total,
                "category_distribution": category_dist,
                "source_top": source_top,
                "daily_trend": daily_trend,
                "time_range": {
                    "latest": time_range['latest'].isoformat() if time_range['latest'] else None,
                    "earliest": time_range['earliest'].isoformat() if time_range['earliest'] else None,
                },
                "categories": categories,
            }
    except pymysql.err.OperationalError as e:
        raise HTTPException(status_code=503, detail=f"数据库不可用: {e}")
    except Exception as e:
        logging.exception("获取新闻统计失败")
        raise HTTPException(status_code=500, detail=f"获取新闻统计失败: {e}")
    finally:
        if conn and conn.open:
            conn.close()


@app.get("/api/item-price/{item_id}")
async def get_item_price(item_id: str):
    """
    获取饰品实时价格数据（BUFF平台）
    """
    try:
        # 调用爬虫获取数据
        item_data = item_crawler.fetch_item_details(item_id)

        if not item_data:
            raise HTTPException(status_code=404, detail="无法获取饰品数据")

        if not item_data.get("success"):
            raise HTTPException(status_code=400, detail=f"API返回错误: {item_data.get('errorMsg', '未知错误')}")

        # 获取最新的价格数据（数组中的最后一个元素）
        price_data = item_data.get("data", [])
        if not price_data:
            raise HTTPException(status_code=404, detail="无价格数据")

        # 取最新的价格数据（数组最后一个元素）
        latest_price = price_data[-1] if price_data else None
        if not latest_price:
            raise HTTPException(status_code=404, detail="无最新价格数据")

        # 解析数据格式：[timestamp, price, sell_count, buy_price, buy_count, turnover, volume, total_count]
        try:
            timestamp = int(latest_price[0])
            price = float(latest_price[1])
            sell_count = int(latest_price[2])
            buy_price = float(latest_price[3])
            buy_count = int(latest_price[4])
            turnover = float(latest_price[5]) if latest_price[5] is not None else 0
            volume = int(latest_price[6]) if latest_price[6] is not None else 0
            total_count = int(latest_price[7]) if isinstance(latest_price[7], str) else latest_price[7]
        except (IndexError, ValueError, TypeError) as e:
            logging.error(f"数据解析失败: {latest_price}, 错误: {e}")
            raise HTTPException(status_code=500, detail="价格数据格式错误")

        # 返回格式化的实时价格数据
        return {
            "success": True,
            "data": [{
                "platform": "BUFF",
                "sellPrice": price,
                "sellCount": sell_count,
                "biddingPrice": buy_price,
                "biddingCount": buy_count,
                "turnover": turnover,
                "volume": volume,
                "totalCount": total_count,
                "updateTime": timestamp
            }]
        }

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"获取饰品价格失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取饰品价格失败: {str(e)}")

@app.get("/api/item-price-history/{item_id}")
async def get_item_price_history(item_id: str):
    """
    获取饰品历史价格数据（用于K线图）
    """
    try:
        # 调用爬虫获取数据
        item_data = item_crawler.fetch_item_details(item_id)

        if not item_data:
            raise HTTPException(status_code=404, detail="无法获取饰品数据")

        if not item_data.get("success"):
            raise HTTPException(status_code=400, detail=f"API返回错误: {item_data.get('errorMsg', '未知错误')}")

        # 获取所有历史价格数据
        price_data = item_data.get("data", [])
        if not price_data:
            raise HTTPException(status_code=404, detail="无价格数据")

        # 格式化所有历史数据
        formatted_data = []
        for price_point in price_data:
            try:
                timestamp = int(price_point[0])
                price = float(price_point[1])
                sell_count = int(price_point[2])
                buy_price = float(price_point[3])
                buy_count = int(price_point[4])
                turnover = float(price_point[5]) if price_point[5] is not None else 0
                volume = int(price_point[6]) if price_point[6] is not None else 0
                total_count = int(price_point[7]) if isinstance(price_point[7], str) else price_point[7]

                formatted_data.append({
                    "timestamp": timestamp,
                    "price": price,
                    "sell_count": sell_count,
                    "buy_price": buy_price,
                    "buy_count": buy_count,
                    "turnover": turnover,
                    "volume": volume,
                    "total_count": total_count
                })
            except (IndexError, ValueError, TypeError) as e:
                logging.warning(f"跳过无效数据点: {price_point}, 错误: {e}")
                continue

        return {
            "success": True,
            "data": formatted_data
        }

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"获取饰品历史价格失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取饰品历史价格失败: {str(e)}")

@app.get("/api/item/kline-data/{market_hash_name}")
async def get_item_kline_data(
    market_hash_name: str,
    platform: str = "BUFF",
    type_day: str = "1",
    date_type: int = 3,
):
    try:
        # 根据饰品是否被追踪来决定是否存储数据，并透传查询参数
        kline_data = await item_kline_processor.handle_item_kline_request(
            market_hash_name,
            platform=platform,
            type_day=type_day,
            date_type=date_type,
        )
        return {"success": True, "data": kline_data}
    except HTTPException as e:
        raise e
    except Exception as e:
        logging.exception(f"获取饰品 {market_hash_name} 的 K线数据失败")
        raise HTTPException(status_code=500, detail=f"获取饰品 K线数据失败: {e}")


@app.get("/api/item/kline-cached/{market_hash_name}")
async def get_cached_item_kline(market_hash_name: str):
    """
    快速读取缓存的K线数据，从 item_kline_day 表直接查询。
    用于追踪饰品的首屏加载，毫秒级响应。
    """
    try:
        loop = asyncio.get_event_loop()
        cached_data, last_updated = await loop.run_in_executor(
            None,
            item_kline_processor.get_cached_kline_data,
            market_hash_name
        )
        return {"success": True, "data": cached_data, "source": "cache", "last_updated": last_updated}
    except Exception as e:
        logging.exception(f"读取缓存K线数据失败: {market_hash_name}")
        raise HTTPException(status_code=500, detail=f"读取缓存数据失败: {e}")


@app.post("/api/item/kline-refresh/{market_hash_name}")
async def refresh_item_kline(market_hash_name: str):
    """
    通过 buff-tracker API 获取最新K线数据并存入数据库。
    先检查缓存新鲜度，1小时内不重复抓取。
    """
    try:
        loop = asyncio.get_event_loop()
        # 检查缓存是否新鲜
        is_fresh = await loop.run_in_executor(
            None, item_kline_processor.is_cache_fresh, market_hash_name
        )
        if is_fresh:
            cached_data, last_updated = await loop.run_in_executor(
                None, item_kline_processor.get_cached_kline_data, market_hash_name
            )
            return {"success": True, "data": cached_data, "source": "cache", "last_updated": last_updated}

        # 通过 buff-tracker API 获取并存入数据库
        result = await _fetch_and_store_kline_via_bufftracker(market_hash_name)
        if result:
            return {"success": True, "data": result, "source": "api"}
        else:
            raise HTTPException(status_code=502, detail="获取K线数据失败，外部服务不可用")
    except HTTPException as e:
        raise e
    except Exception as e:
        logging.exception(f"刷新K线数据失败: {market_hash_name}")
        raise HTTPException(status_code=500, detail=f"刷新K线数据失败: {e}")

async def _fetch_and_store_kline_via_bufftracker(name: str):
    """
    通过 buff-tracker API 获取K线数据并存入数据库。
    本地 Playwright 爬虫在容器内 WAF 挑战容易失败，改用 buff-tracker API 更可靠。
    """
    try:
        item_id = item_kline_processor.get_item_id_from_db(name)
        if not item_id:
            logging.error(f"未找到饰品 {name} 的 item_id，跳过K线数据获取。")
            return []

        data = await bufftracker_client.get_item_kline_data(
            name,
            platform="BUFF",
            type_day="1",
            date_type=3,
        )

        if not data.get("success") or not data.get("data"):
            logging.error(f"buff-tracker 返回无效数据: {name}")
            return []

        raw_rows = data["data"]
        parsed = item_kline_processor.parse_item_kline_data(
            {"success": True, "data": raw_rows}, name, item_id
        )
        if not parsed:
            logging.warning(f"解析K线数据为空: {name}")
            return []

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, item_kline_processor._store_parsed_kline, name, parsed)
        logging.info(f"成功为饰品 {name} 获取并存储了 {len(parsed)} 条K线数据。")
        return parsed
    except Exception as e:
        logging.error(f"获取K线数据失败 ({name}): {e}")
        return []


async def _bg_fetch_kline(name: str):
    """追踪饰品后的后台任务：获取并存储K线数据。"""
    await _fetch_and_store_kline_via_bufftracker(name)

@app.post("/api/track/add")
async def add_track(request: TrackRequest):
    # 用 run_in_executor 在线程池中执行同步 pymysql 调用，避免阻塞事件循环
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None, user_actions.add_track_item, request.email, request.market_hash_name
    )
    if result["success"]:
        asyncio.create_task(_bg_fetch_kline(request.market_hash_name))
        return result
    else:
        raise HTTPException(status_code=400, detail=result["message"])

@app.get("/api/track/list/{email}")
async def get_tracked_items(email: str):
    result = user_actions.get_tracked_items_by_email(email)
    if result["success"]:
        return result["data"]
    else:
        raise HTTPException(status_code=400, detail=result["message"])

@app.post("/api/track/remove")
async def remove_track(request: TrackRequest):
    result = user_actions.remove_track_item(request.email, request.market_hash_name)
    if result["success"]:
        return result
    else:
        raise HTTPException(status_code=400, detail=result["message"])


@app.get("/api/trade-notes/{email}/positions")
async def get_trade_note_positions(email: str):
    """获取买卖笔记聚合仓位。"""
    try:
        loop = asyncio.get_event_loop()
        positions = await loop.run_in_executor(
            None, trade_notes_processor.list_positions, email
        )
        return {"success": True, "data": positions}
    except Exception as e:
        logging.exception("获取买卖笔记仓位失败")
        raise HTTPException(status_code=500, detail=f"获取买卖笔记仓位失败: {e}")


@app.get("/api/trade-notes/{email}/entries")
async def get_trade_note_entries(email: str, market_hash_name: Optional[str] = None):
    """获取买卖笔记流水。"""
    try:
        loop = asyncio.get_event_loop()
        entries = await loop.run_in_executor(
            None, trade_notes_processor.list_entries, email, market_hash_name
        )
        return {"success": True, "data": entries}
    except Exception as e:
        logging.exception("获取买卖笔记流水失败")
        raise HTTPException(status_code=500, detail=f"获取买卖笔记流水失败: {e}")


@app.post("/api/trade-notes")
async def add_trade_note_entry(request: TradeNoteRequest):
    """新增买入/卖出流水。"""
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, trade_notes_processor.add_entry, request.dict()
        )
        if result.get("success"):
            return result
        raise HTTPException(status_code=400, detail=result.get("message", "新增失败"))
    except HTTPException:
        raise
    except Exception as e:
        logging.exception("新增买卖笔记失败")
        raise HTTPException(status_code=500, detail=f"新增买卖笔记失败: {e}")


@app.delete("/api/trade-notes/{email}/entries/{entry_id}")
async def delete_trade_note_entry(email: str, entry_id: int):
    """删除一条买卖流水。"""
    try:
        loop = asyncio.get_event_loop()
        deleted = await loop.run_in_executor(
            None, trade_notes_processor.delete_entry, email, entry_id
        )
        if deleted:
            return {"success": True}
        raise HTTPException(status_code=404, detail="记录不存在或无权删除")
    except HTTPException:
        raise
    except Exception as e:
        logging.exception("删除买卖笔记失败")
        raise HTTPException(status_code=500, detail=f"删除买卖笔记失败: {e}")

@app.get("/api/skin/trending")
async def get_trending_skins(limit: int = 20):
    """获取热门饰品列表（按提及次数 + 最新更新排序）"""
    try:
        from db.skin_processor import SkinEntityProcessor, SkinDetailProcessor
        with SkinEntityProcessor() as proc:
            skins = proc.get_trending_skins(limit=limit)
        # datetime 序列化
        for s in skins:
            for k, v in s.items():
                if isinstance(v, (datetime, date)):
                    s[k] = v.isoformat()
        return {"items": skins, "total": len(skins)}
    except Exception as e:
        logging.exception("获取热门饰品失败")
        raise HTTPException(status_code=500, detail=f"获取热门饰品失败: {e}")


@app.get("/api/skin/search")
async def search_skins(q: str, limit: int = 20):
    """模糊搜索饰品（中文名或英文名）"""
    if not q or len(q.strip()) < 1:
        raise HTTPException(status_code=400, detail="搜索关键词不能为空")
    try:
        from db.skin_processor import SkinEntityProcessor
        with SkinEntityProcessor() as proc:
            skins = proc.search_skins(q.strip(), limit=limit)
        for s in skins:
            for k, v in s.items():
                if isinstance(v, (datetime, date)):
                    s[k] = v.isoformat()
        return {"items": skins, "total": len(skins)}
    except Exception as e:
        logging.exception("搜索饰品失败")
        raise HTTPException(status_code=500, detail=f"搜索饰品失败: {e}")


@app.get("/api/skin/{skin_id}/detail")
async def get_skin_detail(skin_id: int):
    """获取单个饰品的详细信息（实体 + 所有平台价格详情）"""
    try:
        from db.skin_processor import SkinEntityProcessor, SkinDetailProcessor
        with SkinEntityProcessor() as entity_proc:
            entity = entity_proc.get_skin_entity_by_id(skin_id)
            if not entity:
                raise HTTPException(status_code=404, detail="饰品不存在")
            for k, v in entity.items():
                if isinstance(v, (datetime, date)):
                    entity[k] = v.isoformat()

        with SkinDetailProcessor() as detail_proc:
            details = detail_proc.get_skin_detail(skin_id) or []
            if isinstance(details, dict):
                details = [details]
            for d in details:
                for k, v in d.items():
                    if isinstance(v, (datetime, date)):
                        d[k] = v.isoformat()

        return {"entity": entity, "details": details}
    except HTTPException:
        raise
    except Exception as e:
        logging.exception(f"获取饰品 {skin_id} 详情失败")
        raise HTTPException(status_code=500, detail=f"获取饰品详情失败: {e}")


# ── 搬砖收益计算 API ─────────────────────────────────────────────────────

@app.get("/api/profit/platform-fees")
async def get_platform_fees():
    """获取所有平台的费率配置。"""
    try:
        fees = profit_processor.get_all_platform_fees()
        for f in fees:
            for k, v in f.items():
                if hasattr(v, "__float__"):
                    f[k] = float(v)
        return {"success": True, "data": fees}
    except Exception as e:
        logging.exception("获取平台费率失败")
        raise HTTPException(status_code=500, detail=f"获取平台费率失败: {e}")


@app.get("/api/profit/calculate")
async def calculate_profit(
    buy_price: float,
    sell_price: float,
    sell_platform: str = "BUFF",
    hold_days: int = 7,
):
    """计算搬砖利润（指定平台费率）。"""
    try:
        result = profit_processor.calc_profit_for_platform(
            buy_price=buy_price,
            sell_price=sell_price,
            sell_platform=sell_platform,
            hold_days=hold_days,
        )
        if not result:
            raise HTTPException(status_code=404, detail=f"未找到平台 {sell_platform} 的费率配置")
        return {"success": True, "data": result}
    except HTTPException:
        raise
    except Exception as e:
        logging.exception("利润计算失败")
        raise HTTPException(status_code=500, detail=f"利润计算失败: {e}")


@app.get("/api/profit/calculate-all")
async def calculate_profit_all_platforms(
    buy_price: float,
    sell_price: float,
    hold_days: int = 7,
):
    """计算在所有平台卖出的利润对比。"""
    try:
        results = profit_processor.calc_all_platforms_profit(
            buy_price=buy_price,
            sell_price=sell_price,
            hold_days=hold_days,
        )
        return {"success": True, "data": results}
    except Exception as e:
        logging.exception("利润计算失败")
        raise HTTPException(status_code=500, detail=f"利润计算失败: {e}")


def _positive_float(value):
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if result <= 0 or not math.isfinite(result):
        return None
    return result


def _positive_price_from_row(row, keys):
    """Return the first explicitly provided positive price without masking a zero."""
    for key in keys:
        if key not in row:
            continue
        value = row.get(key)
        if value is None or value == "":
            continue
        return _positive_float(value)
    return None


def _extract_price_rows(price_payload):
    if not isinstance(price_payload, dict):
        return []

    data = price_payload.get("data", [])
    if isinstance(data, dict):
        if isinstance(data.get("data"), list):
            data = data["data"]
        elif isinstance(data.get("items"), list):
            data = data["items"]
        else:
            data = list(data.values())

    if not isinstance(data, list):
        return []

    return [row for row in data if isinstance(row, dict)]


def _make_price_node(node_id, label, price, row=None, count_key=None, source="live"):
    row = row or {}
    platform = row.get("platform") or "BUFF"
    count = row.get(count_key) if count_key else None
    return {
        "id": node_id,
        "label": label,
        "price": round(price, 2),
        "platform": platform,
        "platform_key": profit_processor.normalize_platform(platform),
        "count": count,
        "source": source,
    }


def _current_price_nodes(price_rows, fallback_sell=None, fallback_bid=None):
    sell_candidates = []
    bid_candidates = []

    for row in price_rows:
        platform = str(row.get("platform") or "")
        if platform.strip().lower().startswith("steam"):
            continue

        sell_price = _positive_price_from_row(row, ("sellPrice", "sell_price", "price"))
        bidding_price = _positive_price_from_row(
            row,
            ("biddingPrice", "buyPrice", "buy_price"),
        )

        if sell_price:
            sell_candidates.append((sell_price, row))
        if bidding_price:
            bid_candidates.append((bidding_price, row))

    lowest_sell = min(sell_candidates, key=lambda item: item[0], default=None)
    highest_sell = max(sell_candidates, key=lambda item: item[0], default=None)
    lowest_bid = min(bid_candidates, key=lambda item: item[0], default=None)
    highest_bid = max(bid_candidates, key=lambda item: item[0], default=None)

    lowest_sell_node = (
        _make_price_node(
            "current_lowest_sell",
            "最低卖价",
            lowest_sell[0],
            lowest_sell[1],
            "sellCount",
        )
        if lowest_sell
        else None
    )
    lowest_bid_node = (
        _make_price_node(
            "current_lowest_bidding",
            "最低求购",
            lowest_bid[0],
            lowest_bid[1],
            "biddingCount",
        )
        if lowest_bid
        else None
    )
    highest_sell_node = (
        _make_price_node(
            "current_highest_sell",
            "最高卖价",
            highest_sell[0],
            highest_sell[1],
            "sellCount",
        )
        if highest_sell
        else None
    )
    highest_bid_node = (
        _make_price_node(
            "current_highest_bidding",
            "最高求购",
            highest_bid[0],
            highest_bid[1],
            "biddingCount",
        )
        if highest_bid
        else None
    )

    if not lowest_sell_node and fallback_sell:
        lowest_sell_node = _make_price_node(
            "current_lowest_sell",
            "最低卖价",
            fallback_sell,
            source="cache",
        )
    if not highest_sell_node and fallback_sell:
        highest_sell_node = _make_price_node(
            "current_highest_sell",
            "最高卖价",
            fallback_sell,
            source="cache",
        )
    if not lowest_bid_node and fallback_bid:
        lowest_bid_node = _make_price_node(
            "current_lowest_bidding",
            "最低求购",
            fallback_bid,
            source="cache",
        )
    if not highest_bid_node and fallback_bid:
        highest_bid_node = _make_price_node(
            "current_highest_bidding",
            "最高求购",
            fallback_bid,
            source="cache",
        )

    return lowest_bid_node, lowest_sell_node, highest_bid_node, highest_sell_node


def _estimate_future_bidding_node(predicted_sell, current_sell_node, current_highest_bid_node):
    if not current_sell_node or not current_highest_bid_node:
        return None

    current_sell = _positive_float(current_sell_node.get("price"))
    current_bid = _positive_float(current_highest_bid_node.get("price"))
    if not current_sell or not current_bid:
        return None

    bid_to_sell_ratio = min(current_bid / current_sell, 1.0)
    if bid_to_sell_ratio <= 0:
        return None

    predicted_bid = round(predicted_sell * bid_to_sell_ratio, 2)
    node = _make_price_node(
        "future_predicted_bidding",
        "预测求购",
        predicted_bid,
        current_highest_bid_node,
        "count",
        source="estimated_from_spread",
    )
    node["estimation_ratio"] = round(bid_to_sell_ratio, 4)
    return node


def _latest_cached_price_pair(market_hash_name):
    conn = None
    try:
        conn = profit_processor.get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT price, buy_price FROM item_kline_day "
                "WHERE market_hash_name = %s "
                "ORDER BY timestamp DESC LIMIT 1",
                (market_hash_name,),
            )
            row = cursor.fetchone()
            if not row:
                return None, None
            return _positive_float(row[0]), _positive_float(row[1])
    finally:
        if conn:
            conn.close()


@app.get("/api/profit/predict/{market_hash_name}")
async def predict_item_profit(market_hash_name: str, hold_days: int = 7):
    """
    预测指定饰品 7 天后的价格，并计算各平台卖出利润。
    """
    try:
        from models.item_price_predictor import predict_item_7d_range
        prediction = predict_item_7d_range(market_hash_name)
        if not prediction:
            raise HTTPException(
                status_code=404,
                detail=f"无法预测 {market_hash_name}（数据不足，至少需要 {60} 天K线数据）"
            )

        cached_sell_price = None
        cached_bidding_price = None
        try:
            cached_sell_price, cached_bidding_price = _latest_cached_price_pair(
                market_hash_name
            )
        except Exception:
            logging.exception(f"读取 {market_hash_name} 最新缓存价格失败")

        live_price_rows = []
        try:
            live_price_rows = _extract_price_rows(
                await bufftracker_client.get_price(market_hash_name)
            )
        except Exception:
            logging.exception(f"读取 {market_hash_name} 实时多平台价格失败")

        (
            current_lowest_bidding_node,
            current_lowest_sell_node,
            current_highest_bidding_node,
            current_highest_sell_node,
        ) = _current_price_nodes(
            live_price_rows,
            fallback_sell=cached_sell_price,
            fallback_bid=cached_bidding_price,
        )

        predicted_sell_price = _positive_float(prediction["predicted"])
        future_predicted_sell_node = (
            _make_price_node(
                "future_predicted_sell",
                "预测卖价",
                predicted_sell_price,
                {"platform": "BUFF"},
                source="lgbm",
            )
            if predicted_sell_price
            else None
        )
        future_predicted_bidding_node = (
            _estimate_future_bidding_node(
                predicted_sell_price,
                current_lowest_sell_node,
                current_highest_bidding_node,
            )
            if predicted_sell_price
            else None
        )

        buy_nodes = [
            node
            for node in [current_lowest_bidding_node, current_lowest_sell_node]
            if node
        ]
        sell_nodes = [
            node
            for node in [future_predicted_bidding_node, future_predicted_sell_node]
            if node
        ]
        profit_paths = profit_processor.calc_profit_paths(
            buy_nodes=buy_nodes,
            sell_nodes=sell_nodes,
            hold_days=hold_days,
        )
        current_profit_paths = profit_processor.calc_profit_paths(
            buy_nodes=buy_nodes,
            sell_nodes=[
                node
                for node in [current_highest_bidding_node, current_highest_sell_node]
                if node
            ],
            hold_days=hold_days,
        )

        # 兼容旧前端字段：保留“当前最低卖价买入 + 预测卖价卖出”的平台费率对比。
        current_price = (
            current_lowest_sell_node.get("price") if current_lowest_sell_node else None
        )
        profit_by_platform = {}
        if current_price and predicted_sell_price:
            profit_by_platform = profit_processor.calc_all_platforms_profit(
                buy_price=current_price,
                sell_price=predicted_sell_price,
                hold_days=hold_days,
            )

        return {
            "success": True,
            "data": {
                "market_hash_name": market_hash_name,
                "current_price": current_price,
                "current_lowest_bidding_price": (
                    current_lowest_bidding_node.get("price")
                    if current_lowest_bidding_node
                    else None
                ),
                "current_lowest_sell_price": current_price,
                "current_highest_bidding_price": (
                    current_highest_bidding_node.get("price")
                    if current_highest_bidding_node
                    else None
                ),
                "current_highest_sell_price": (
                    current_highest_sell_node.get("price")
                    if current_highest_sell_node
                    else None
                ),
                "predicted_highest_bidding_price": (
                    future_predicted_bidding_node.get("price")
                    if future_predicted_bidding_node
                    else None
                ),
                "predicted_price_7d": predicted_sell_price,
                "predicted_lower": prediction["lower"],
                "predicted_upper": prediction["upper"],
                "confidence": prediction["confidence"],
                "price_nodes": {
                    "current_lowest_bidding": current_lowest_bidding_node,
                    "current_lowest_sell": current_lowest_sell_node,
                    "current_highest_bidding": current_highest_bidding_node,
                    "current_highest_sell": current_highest_sell_node,
                    "future_predicted_bidding": future_predicted_bidding_node,
                    "future_predicted_sell": future_predicted_sell_node,
                },
                "profit_paths": profit_paths,
                "best_path": profit_paths[0] if profit_paths else None,
                "current_profit_paths": current_profit_paths,
                "best_current_path": (
                    current_profit_paths[0] if current_profit_paths else None
                ),
                "profit_by_platform": profit_by_platform,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.exception(f"预测饰品 {market_hash_name} 利润失败")
        raise HTTPException(status_code=500, detail=f"预测失败: {e}")


@app.get("/api/profit/tracked/{email}")
async def get_tracked_items_profit(email: str):
    """
    获取用户所有追踪饰品的预测利润。
    后台触发 LGBM 预测 + 利润计算。
    """
    try:
        # 1. 获取用户追踪的饰品列表
        loop = asyncio.get_event_loop()
        tracked_result = await loop.run_in_executor(
            None, user_actions.get_tracked_items_by_email, email
        )
        if not tracked_result.get("success"):
            raise HTTPException(status_code=400, detail=tracked_result.get("message", "获取追踪列表失败"))

        items = tracked_result["data"]
        if not items:
            return {"success": True, "data": []}

        # 2. 批量预测价格
        from models.item_price_predictor import batch_predict_items
        names = [item["market_hash_name"] for item in items]
        predicted_prices = await loop.run_in_executor(
            None, batch_predict_items, names
        )

        # 3. 获取利润信息
        items_with_profit = await loop.run_in_executor(
            None,
            profit_processor.get_tracked_items_with_profit,
            email,
            predicted_prices,
        )

        # 序列化 Decimal → float
        for item in items_with_profit:
            for k, v in item.items():
                if hasattr(v, "__float__") and not isinstance(v, (int, float, type(None), bool)):
                    item[k] = float(v)
            if item.get("profit_by_platform"):
                for pdata in item["profit_by_platform"].values():
                    for pk, pv in pdata.items():
                        if hasattr(pv, "__float__"):
                            pdata[pk] = float(pv)

        return {"success": True, "data": items_with_profit}
    except HTTPException:
        raise
    except Exception as e:
        logging.exception("获取追踪饰品利润失败")
        raise HTTPException(status_code=500, detail=f"获取追踪利润失败: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
