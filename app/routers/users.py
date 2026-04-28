import pymysql
from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_user_manager
from db.user_manager import UserManager


router = APIRouter(prefix="/api/user", tags=["users"])


@router.get("/profile")
async def get_user_profile(
    email: str,
    user_manager: UserManager = Depends(get_user_manager),
):
    try:
        created_at = user_manager.get_user_created_at(email)
        if created_at:
            return {"created_at": created_at.isoformat()}
        raise HTTPException(status_code=404, detail="用户不存在")
    except HTTPException:
        raise
    except pymysql.err.OperationalError as e:
        raise HTTPException(status_code=503, detail=f"数据库不可用: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户信息失败: {e}")


@router.get("/details/{email}")
async def get_user_details(
    email: str,
    user_manager: UserManager = Depends(get_user_manager),
):
    try:
        details = user_manager.get_user_details(email)
        if details:
            return details
        raise HTTPException(status_code=404, detail="用户不存在")
    except HTTPException:
        raise
    except pymysql.err.OperationalError as e:
        raise HTTPException(status_code=503, detail=f"数据库不可用: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户详情失败: {e}")
