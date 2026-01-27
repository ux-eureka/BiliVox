import os
from fastapi import Header, HTTPException


def require_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")):
    expected = os.getenv("BILIVOX_API_KEY", "").strip()
    if not expected:
        return
    if not x_api_key or x_api_key.strip() != expected:
        raise HTTPException(status_code=401, detail="未授权：缺少或错误的 API Key")

