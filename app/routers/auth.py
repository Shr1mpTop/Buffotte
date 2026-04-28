import logging

import pymysql
from fastapi import APIRouter, Depends, HTTPException, Request

from app.dependencies import get_user_manager
from app.schemas.auth import LoginRequest, RegisterRequest
from db.user_manager import UserManager


router = APIRouter(prefix="/api", tags=["auth"])


@router.post("/register")
async def register(
    request: RegisterRequest,
    user_manager: UserManager = Depends(get_user_manager),
):
    try:
        success = user_manager.register_user(request.username, request.email, request.password)
    except pymysql.err.OperationalError as e:
        raise HTTPException(status_code=503, detail=f"数据库不可用: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"注册失败: {e}")
    if success:
        return {"success": True, "message": "注册成功"}
    raise HTTPException(status_code=409, detail="邮箱已存在")


@router.post("/login")
async def login(
    request: LoginRequest,
    http_request: Request,
    user_manager: UserManager = Depends(get_user_manager),
):
    try:
        verified = user_manager.verify_password(request.email, request.password)
    except pymysql.err.OperationalError as e:
        logging.exception("数据库连接错误 during verify_password")
        raise HTTPException(status_code=503, detail=f"数据库不可用: {e}")
    except Exception as e:
        logging.exception("异常 during verify_password")
        raise HTTPException(status_code=500, detail=f"服务器错误: {e}")

    if not verified:
        raise HTTPException(status_code=401, detail="邮箱或密码错误")

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
            cursor.execute("SELECT id, username, created_at FROM user WHERE email = %s", (request.email,))
            result = cursor.fetchone()
            if result:
                user_id = result[0]
                username = result[1]
                created_at = result[2]
                created_at_str = created_at.isoformat() if created_at else None
                return {
                    "success": True,
                    "message": "登录成功",
                    "user": {
                        "id": user_id,
                        "email": request.email,
                        "username": username,
                        "created_at": created_at_str,
                    },
                }
            raise HTTPException(status_code=404, detail="用户不存在")
    except HTTPException:
        raise
    except Exception as e:
        logging.exception("异常 during SELECT username")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            conn.close()
        except Exception:
            pass
