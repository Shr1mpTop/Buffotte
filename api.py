from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse
import logging
import traceback
import os
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from db.user_manager import UserManager
from db.kline_data_processor import KlineDataProcessor
from db.item_kline_processor import ItemKlineProcessor
from db.user_actions import UserActions
from crawler.item_price import DailyKlineCrawler
import pymysql
from datetime import date, datetime
import pytz

app = FastAPI()
logging.basicConfig(level=logging.INFO)


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
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173", "http://127.0.0.1:5174", "https://buffotte.hezhili.online"],  # 前端地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

user_manager = UserManager()
kline_processor = KlineDataProcessor()
item_kline_processor = ItemKlineProcessor()
item_crawler = DailyKlineCrawler()
user_actions = UserActions()

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class TrackRequest(BaseModel):
    email: str
    market_hash_name: str


@app.post("/api/register")
async def register(request: RegisterRequest):
    try:
        success = user_manager.register_user(request.username, request.email, request.password)
    except pymysql.err.OperationalError as e:
        raise HTTPException(status_code=503, detail=f"数据库不可用: {e}")
    except Exception as e:
        # 数据库连接或内部错误
        raise HTTPException(status_code=500, detail=f"注册失败: {e}")
    if success:
        return {"success": True, "message": "注册成功"}
    else:
        raise HTTPException(status_code=409, detail="邮箱已存在")

@app.post("/api/login")
async def login(request: LoginRequest, http_request: Request):
    try:
        verified = user_manager.verify_password(request.email, request.password)
    except pymysql.err.OperationalError as e:
        logging.exception("数据库连接错误 during verify_password")
        raise HTTPException(status_code=503, detail=f"数据库不可用: {e}")
    except Exception as e:
        logging.exception("异常 during verify_password")
        # 数据库连接/其它内部错误
        raise HTTPException(status_code=500, detail=f"服务器错误: {e}")
    if verified:
        # 获取用户信息
        try:
            conn = user_manager.get_db_connection()
        except pymysql.err.OperationalError as e:
            logging.exception("数据库连接失败 when attempting to retrieve username")
            raise HTTPException(status_code=503, detail=f"数据库不可用: {e}")
        except Exception as e:
            logging.exception("Unexpected error while obtaining DB connection")
            raise HTTPException(status_code=500, detail=str(e))
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT username, created_at FROM user WHERE email = %s", (request.email,))
                result = cursor.fetchone()
                if result:
                    username = result[0]
                    created_at = result[1]
                    # 将 datetime 对象转换为 ISO 格式字符串
                    created_at_str = created_at.isoformat() if created_at else None
                    return {
                        "success": True,
                        "message": "登录成功",
                        "user": {"email": request.email, "username": username, "created_at": created_at_str}
                    }
                else:
                    raise HTTPException(status_code=404, detail="用户不存在")
        except Exception as e:
            logging.exception("异常 during SELECT username")
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            try:
                conn.close()
            except Exception:
                pass
    else:
        raise HTTPException(status_code=401, detail="邮箱或密码错误")

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

@app.get("/api/user/profile")
async def get_user_profile(email: str):
    try:
        created_at = user_manager.get_user_created_at(email)
        if created_at:
            return {"created_at": created_at.isoformat()}
        else:
            raise HTTPException(status_code=404, detail="用户不存在")
    except pymysql.err.OperationalError as e:
        raise HTTPException(status_code=503, detail=f"数据库不可用: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户信息失败: {e}")

@app.get("/api/user/details/{email}")
async def get_user_details(email: str):
    try:
        details = user_manager.get_user_details(email)
        if details:
            return details
        else:
            raise HTTPException(status_code=404, detail="用户不存在")
    except pymysql.err.OperationalError as e:
        raise HTTPException(status_code=503, detail=f"数据库不可用: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户详情失败: {e}")

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


# 代理到 buff-tracker API
@app.api_route("/api/bufftracker/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_bufftracker(request: Request, path: str):
    """
    代理 buff-tracker API 请求，避免 HTTPS 网站的 Mixed Content 问题
    """
    import httpx

    # 本地开发：BUFFTRACKER_URL=http://localhost:8001
    # Docker部署：BUFFTRACKER_URL=http://host.docker.internal:8001（默认）
    bufftracker_base = os.getenv("BUFFTRACKER_URL", "http://host.docker.internal:8001")

    # 构建目标 URL
    target_url = f"{bufftracker_base}/api/{path}"

    # 添加查询参数
    if request.url.query:
        target_url += f"?{request.url.query}"

    try:
        # 转发请求
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 获取请求体
            body = await request.body()

            # 转发请求
            response = await client.request(
                method=request.method,
                url=target_url,
                headers={k: v for k, v in request.headers.items() if k.lower() not in ['host', 'content-length']},
                content=body
            )

            # 返回响应
            return Response(content=response.content, status_code=response.status_code, headers=dict(response.headers))

    except Exception as e:
        logging.error(f"Buff-tracker proxy error: {repr(e)}")
        raise HTTPException(status_code=503, detail=f"Buff-tracker service unavailable: {str(e)}")

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

@app.post("/api/track/add")
async def add_track(request: TrackRequest):
    result = user_actions.add_track_item(request.email, request.market_hash_name)
    if result["success"]:
        # 追踪成功后，立即调用 handle_item_kline_request 获取并存储数据
        try:
            await item_kline_processor.handle_item_kline_request(request.market_hash_name)
            logging.info(f"成功为新追踪的饰品 {request.market_hash_name} 获取并存储了K线数据。")
        except Exception as e:
            # 即使这里失败，也不应该影响追踪成功的主流程，所以只记录日志
            logging.error(f"为新追踪的饰品 {request.market_hash_name} 获取K线数据失败: {e}")
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
