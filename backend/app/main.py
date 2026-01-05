from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .api import auth_router, channels_router, videos_router, interactions_router

app = FastAPI(
    title=settings.app_name,
    description="YouTube ライクな動画プラットフォーム API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # フロントエンド
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーター登録
app.include_router(auth_router)
app.include_router(channels_router)
app.include_router(videos_router)
app.include_router(interactions_router)


@app.get("/health")
async def health_check():
    """ヘルスチェック"""
    return {"status": "healthy", "app": settings.app_name}


@app.get("/")
async def root():
    """ルート"""
    return {
        "message": "Video Platform API",
        "docs": "/docs",
    }
