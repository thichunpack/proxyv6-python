import httpx
from cachetools import TTLCache
from fastapi import HTTPException
from cachetools.keys import hashkey
import asyncio

API_KEY = "https://solumate.vn"

cache = TTLCache(maxsize=100, ttl=10)
cache.clear()


async def fetch_authorization(authorization: str) -> bool:
    headers = {"Accept": "*/*", "Authorization": authorization}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{API_KEY}/api/v1/auth/profile",
                headers=headers,
            )
            await asyncio.sleep(5)  # giả lập độ trễ mạng
            if response.status_code == 200:
                return True
            if response.status_code == 401:
                return False

            # các trường hợp khác coi như lỗi server
            raise HTTPException(
                status_code=response.status_code,
                detail="Lỗi xác thực từ server",
            )

        except httpx.RequestError:
            raise HTTPException(status_code=500, detail="Không thể kết nối API")


async def is_authorized(authorization: str) -> dict:
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header is required")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")

    cache_key = hashkey(authorization)

    if cache_key in cache:
        is_active = cache[cache_key]
    else:
        is_active = await fetch_authorization(authorization)
        cache[cache_key] = is_active

    return {
        "success": is_active,
        "message": (
            "Thành công"
            if is_active
            else "Máy bạn chưa được active, vui lòng liên hệ admin để xóa key và active lại!"
        ),
    }
