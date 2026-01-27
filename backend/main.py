from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sys
import os
from pathlib import Path
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# 添加backend目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.routes import router as api_router
from core.bilivox_manager import BiliVoxManager

# 创建FastAPI应用
app = FastAPI(
    title="BiliVox API",
    description="BiliVox视频资料库构建工具API",
    version="1.0.0"
)

cors_origins_env = os.getenv("BILIVOX_CORS_ORIGINS", "").strip()
cors_origins = [o.strip() for o in cors_origins_env.split(",") if o.strip()] or ["http://localhost:3000"]

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建BiliVox管理器实例
bilivox_manager = BiliVoxManager()

# 注册API路由
app.include_router(api_router, prefix="/api")

project_root = Path(__file__).resolve().parents[1]
frontend_dist = project_root / "frontend" / "dist"
frontend_assets = frontend_dist / "assets"

if frontend_assets.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_assets)), name="assets")


def _serve_frontend(path: str = ""):
    if not frontend_dist.exists():
        return None
    safe_path = path.lstrip("/")
    candidate = (frontend_dist / safe_path).resolve()
    try:
        candidate.relative_to(frontend_dist.resolve())
    except Exception:
        candidate = frontend_dist / "index.html"
    if candidate.exists() and candidate.is_file():
        if candidate.suffix.lower() == ".html":
            return FileResponse(str(candidate), headers={"Cache-Control": "no-cache"})
        return FileResponse(str(candidate))
    requested = Path(safe_path)
    if requested.suffix:
        raise HTTPException(status_code=404)
    index = frontend_dist / "index.html"
    if index.exists():
        return FileResponse(str(index), headers={"Cache-Control": "no-cache"})
    return None


@app.get("/", include_in_schema=False)
def frontend_root():
    served = _serve_frontend("index.html")
    if served is not None:
        return served
    return {
        "message": "BiliVox API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health", include_in_schema=False)
def health_check():
    return {"status": "healthy"}


@app.get("/{path:path}", include_in_schema=False)
def frontend_fallback(path: str):
    served = _serve_frontend(path)
    if served is not None:
        return served
    return {
        "message": "BiliVox API",
        "version": "1.0.0",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    reload_enabled = os.getenv("BILIVOX_RELOAD", "").strip() == "1"
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=reload_enabled
    )
