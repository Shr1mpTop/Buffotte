from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from user_manager import UserManager

app = FastAPI()

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],  # 前端地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

user_manager = UserManager()

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

@app.post("/api/register")
async def register(request: RegisterRequest):
    success = user_manager.register_user(request.username, request.email, request.password)
    if success:
        return {"success": True, "message": "注册成功"}
    else:
        raise HTTPException(status_code=409, detail="邮箱已存在")

@app.post("/api/login")
async def login(request: LoginRequest):
    if user_manager.verify_password(request.email, request.password):
        # 获取用户信息
        conn = user_manager.get_db_connection()
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
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            conn.close()
    else:
        raise HTTPException(status_code=401, detail="邮箱或密码错误")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)