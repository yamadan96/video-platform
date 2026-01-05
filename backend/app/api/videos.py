from datetime import datetime
from uuid import UUID
import boto3
from botocore.config import Config
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func

from ..database import get_db
from ..models import Video, VideoStatus, VideoVisibility, Channel, User
from ..schemas import (
    VideoCreate, VideoUpdate, VideoResponse, VideoListResponse,
    UploadInitResponse, UploadCompleteRequest
)
from ..core.config import settings
from .auth import get_current_user

router = APIRouter(prefix="/videos", tags=["動画"])


def get_s3_client():
    """S3/MinIOクライアントを取得"""
    return boto3.client(
        "s3",
        endpoint_url=f"http://{settings.minio_endpoint}",
        aws_access_key_id=settings.minio_access_key,
        aws_secret_access_key=settings.minio_secret_key,
        config=Config(signature_version="s3v4"),
    )


@router.post("/init-upload", response_model=UploadInitResponse)
async def init_upload(
    video_data: VideoCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """アップロード開始：プリサインURLを返す"""
    # チャンネル権限チェック
    result = await db.execute(select(Channel).where(Channel.id == video_data.channel_id))
    channel = result.scalar_one_or_none()
    
    if not channel or channel.owner_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="このチャンネルに動画をアップロードする権限がありません")
    
    # 動画レコード作成
    video = Video(
        channel_id=video_data.channel_id,
        title=video_data.title,
        description=video_data.description,
        tags=video_data.tags,
        status=VideoStatus.UPLOADING,
    )
    db.add(video)
    await db.commit()
    await db.refresh(video)
    
    # プリサインURL生成
    s3 = get_s3_client()
    object_key = f"uploads/{video.id}/original.mp4"
    
    presigned_url = s3.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": settings.minio_bucket,
            "Key": object_key,
            "ContentType": "video/mp4"
        },
        ExpiresIn=3600,
    )
    
    # ソースURL保存
    video.source_url = object_key
    await db.commit()
    
    return UploadInitResponse(
        video_id=video.id,
        upload_url=presigned_url,
    )


@router.post("/complete-upload")
async def complete_upload(
    data: UploadCompleteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """アップロード完了：変換ジョブをキューに投入"""
    result = await db.execute(select(Video).where(Video.id == data.video_id))
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(status_code=404, detail="動画が見つかりません")
    
    # 権限チェック
    channel_result = await db.execute(select(Channel).where(Channel.id == video.channel_id))
    channel = channel_result.scalar_one_or_none()
    
    if not channel or channel.owner_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="この動画を操作する権限がありません")
    
    # ステータス更新
    video.status = VideoStatus.PROCESSING
    await db.commit()
    
    # Celeryタスクをキューに投入（非同期）
    from ..workers.tasks import transcode_video
    transcode_video.delay(str(video.id))
    
    return {"message": "変換処理を開始しました", "video_id": str(video.id)}


@router.get("", response_model=VideoListResponse)
async def list_videos(
    q: str | None = Query(None, description="検索クエリ"),
    sort: str = Query("new", description="ソート順: new, popular"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """動画一覧・検索"""
    query = select(Video).where(
        Video.visibility == VideoVisibility.PUBLIC,
        Video.status == VideoStatus.PUBLISHED
    )
    
    # 検索
    if q:
        search_filter = or_(
            Video.title.ilike(f"%{q}%"),
            Video.description.ilike(f"%{q}%"),
        )
        query = query.where(search_filter)
    
    # ソート
    if sort == "popular":
        query = query.order_by(Video.view_count.desc())
    else:
        query = query.order_by(Video.published_at.desc())
    
    # 総数取得
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0
    
    # ページネーション
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    videos = result.scalars().all()
    
    return VideoListResponse(
        videos=[VideoResponse.model_validate(v) for v in videos],
        total=total,
        page=page,
        per_page=per_page
    )


@router.get("/{video_id}", response_model=VideoResponse)
async def get_video(
    video_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """動画詳細を取得"""
    result = await db.execute(
        select(Video).where(Video.id == video_id)
    )
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(status_code=404, detail="動画が見つかりません")
    
    # 非公開動画のアクセス制限（簡易版）
    if video.visibility == VideoVisibility.PRIVATE:
        raise HTTPException(status_code=403, detail="この動画は非公開です")
    
    return VideoResponse.model_validate(video)


@router.patch("/{video_id}", response_model=VideoResponse)
async def update_video(
    video_id: UUID,
    video_data: VideoUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """動画を更新"""
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(status_code=404, detail="動画が見つかりません")
    
    # 権限チェック
    channel_result = await db.execute(select(Channel).where(Channel.id == video.channel_id))
    channel = channel_result.scalar_one_or_none()
    
    if not channel or channel.owner_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="この動画を編集する権限がありません")
    
    # 更新データを適用
    update_data = video_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key == "visibility":
            value = VideoVisibility(value)
        setattr(video, key, value)
    
    # 公開に変更した場合
    if video_data.visibility == "public" and video.status == VideoStatus.READY:
        video.status = VideoStatus.PUBLISHED
        video.published_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(video)
    
    return VideoResponse.model_validate(video)


@router.post("/{video_id}/view")
async def record_view(
    video_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """視聴回数をカウント"""
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(status_code=404, detail="動画が見つかりません")
    
    video.view_count += 1
    await db.commit()
    
    return {"view_count": video.view_count}
