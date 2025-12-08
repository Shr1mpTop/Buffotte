from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import logging
import traceback
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from db.user_manager import UserManager
from db.kline_data_processor import KlineDataProcessor
from db.item_kline_processor import ItemKlineProcessor
from crawler.item_price import DailyKlineCrawler
import pymysql
from datetime import date, datetime
import pytz

app = FastAPI()
logging.basicConfig(level=logging.INFO)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Log method/path and headers
    logging.info(f"Request {request.method} {request.url} from {request.client}")
    logging.info(f"Headers: {dict(request.headers)}")
    response = await call_next(request)
    logging.info(f"Response status: {response.status_code} for {request.method} {request.url}")
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

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

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
    # Debugging: log incoming request headers to diagnose issues from browser requests
    logging.info(f"Login request headers: {dict(http_request.headers)}")
    logging.info(f"Login request payload: {request.dict()}")
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
                'timestamp': row[0] * 1000, # 转换为毫秒时间戳
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
            cursor.execute("SELECT * FROM kline_data_prediction WHERE date >= %s ORDER BY date", (date.today(),))
            predictions = cursor.fetchall()

        for pred in predictions:
            # 将 date 对象转换为毫秒时间戳
            ts = int(datetime.combine(pred['date'], datetime.min.time()).timestamp() * 1000)
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

@app.get("/api/summary/latest")
async def get_latest_summary():
    conn = None
    try:
        conn = user_manager.get_db_connection()
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            # 获取东八区今天的日期
            today_utc8 = datetime.now(pytz.timezone('Asia/Shanghai')).date()
            cursor.execute("""
                SELECT id, summary FROM summary 
                WHERE DATE(CONVERT_TZ(created_at, '+00:00', '+08:00')) = %s
                ORDER BY created_at DESC 
                LIMIT 1
            """, (today_utc8,))
            result = cursor.fetchone()
            if result:
                return {"summary": result['summary'], "summary_id": result['id']}
            else:
                # 如果今天没有，就返回最新的一个
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
async def get_news(page: int = 1, size: int = 10, summary_id: int = None):
    conn = None
    try:
        logging.info(f"Attempting to get DB connection for news. Page: {page}, Size: {size}, Summary ID: {summary_id}")
        conn = user_manager.get_db_connection()
        logging.info("DB connection for news successful.")
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            offset = (page - 1) * size
            logging.info(f"Executing news query with offset: {offset}, limit: {size}")
            cursor.execute(
                "SELECT id, title, url, source, publish_time, summary as preview FROM news ORDER BY publish_time DESC LIMIT %s OFFSET %s", 
                (size, offset)
            )
            news_list = cursor.fetchall()
            logging.info(f"Fetched {len(news_list)} news items.")
            
            # 如果提供了summary_id，查询关联的新闻ID
            highlighted_news_ids = set()
            if summary_id:
                cursor.execute(
                    "SELECT news_id FROM summary_news_association WHERE summary_id = %s",
                    (summary_id,)
                )
                highlighted_news_ids = {row['news_id'] for row in cursor.fetchall()}
                logging.info(f"Highlighted news IDs for summary {summary_id}: {highlighted_news_ids}")
            
            # 标记新闻是否被洞察提及
            for news in news_list:
                news['highlighted'] = news['id'] in highlighted_news_ids
            
            # 获取总数用于分页
            cursor.execute("SELECT COUNT(*) as total FROM news")
            total = cursor.fetchone()['total']
            logging.info(f"Total news items: {total}")
            
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
            logging.info("DB connection for news closed.")

# 代理到 buff-tracker API
@app.api_route("/api/bufftracker/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_bufftracker(request: Request, path: str):
    """
    代理 buff-tracker API 请求，避免 HTTPS 网站的 Mixed Content 问题
    """
    import httpx

    # 构建目标 URL
    target_url = f"http://bufftracker.hezhili.online:8010/api/{path}"

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
            return JSONResponse(
                status_code=response.status_code,
                content=response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            )

    except Exception as e:
        logging.error(f"Buff-tracker proxy error: {e}")
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
async def get_item_kline_data(market_hash_name: str):
    try:
        # 调用 item_kline_processor 中的方法来获取 K 线数据
        # 注意: 这里调用的是一个只获取数据而不保存到数据库的方法
        historical_data = await item_kline_processor.get_item_kline_data_for_chart(market_hash_name)
        return {"success": True, "data": historical_data}
    except HTTPException as e:
        raise e
    except Exception as e:
        logging.exception(f"获取饰品 {market_hash_name} 的 K线数据失败")
        raise HTTPException(status_code=500, detail=f"获取饰品 K线数据失败: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
