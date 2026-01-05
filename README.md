# 動画プラットフォーム

YouTube ライクな動画プラットフォーム MVP

## 技術スタック

- **Frontend**: Next.js 14 + TypeScript
- **Backend**: FastAPI + SQLAlchemy + Celery
- **Database**: PostgreSQL 15
- **Cache/Queue**: Redis
- **Storage**: MinIO (S3互換)
- **Transcode**: FFmpeg

## 開発環境の起動

```bash
# 全サービス起動
docker-compose up -d

# ログ確認
docker-compose logs -f backend

# 停止
docker-compose down
```

## アクセス

- フロントエンド: http://localhost:3000
- バックエンド API: http://localhost:8000
- API ドキュメント: http://localhost:8000/docs
- MinIO コンソール: http://localhost:9001 (minioadmin/minioadmin)

## 開発

```bash
# バックエンドのマイグレーション
docker-compose exec backend alembic upgrade head

# テスト実行
docker-compose exec backend pytest tests/ -v
```
