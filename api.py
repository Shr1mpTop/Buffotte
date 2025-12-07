from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import logging
import traceback
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from user_manager import UserManager
from db.kline_data_processor import KlineDataProcessor
import pymysql

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
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173", "http://127.0.0.1:5174"],  # 前端地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

user_manager = UserManager()
kline_processor = KlineDataProcessor()

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
                cursor.execute("SELECT username FROM user WHERE email = %s", (request.email,))
                result = cursor.fetchone()
                if result:
                    username = result[0]
                    return {
                        "success": True,
                        "message": "登录成功",
                        "user": {"email": request.email, "username": username}
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

@app.get("/api/kline/data")
async def get_kline_data():
    try:
        conn = kline_processor.get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT timestamp, open_price, high_price, low_price, close_price, volume, turnover FROM kline_data_day ORDER BY timestamp")
            rows = cursor.fetchall()
        conn.close()
        data = []
        for row in rows:
            data.append({
                'timestamp': row[0],
                'open': float(row[1]),
                'high': float(row[2]),
                'low': float(row[3]),
                'close': float(row[4]),
                'volume': row[5],
                'turnover': float(row[6])
            })
        return {"data": data}
    except pymysql.err.OperationalError as e:
        raise HTTPException(status_code=503, detail=f"数据库不可用: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取K线数据失败: {e}")

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)