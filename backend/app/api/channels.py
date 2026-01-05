from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..models import Channel, Video, User
from ..schemas import ChannelCreate, ChannelUpdate, ChannelResponse, VideoResponse
from .auth import get_current_user

router = APIRouter(prefix="/channels", tags=["チャンネル"])


@router.post("", response_model=ChannelResponse)
async def create_channel(
    channel_data: ChannelCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """チャンネル作成"""
    channel = Channel(
        owner_user_id=current_user.id,
        name=channel_data.name,
        description=channel_data.description,
    )
    db.add(channel)
    await db.commit()
    await db.refresh(channel)
    
    return ChannelResponse.model_validate(channel)


@router.get("/{channel_id}", response_model=ChannelResponse)
async def get_channel(
    channel_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """チャンネル詳細を取得"""
    result = await db.execute(select(Channel).where(Channel.id == channel_id))
    channel = result.scalar_one_or_none()
    
    if not channel:
        raise HTTPException(status_code=404, detail="チャンネルが見つかりません")
    
    return ChannelResponse.model_validate(channel)


@router.patch("/{channel_id}", response_model=ChannelResponse)
async def update_channel(
    channel_id: UUID,
    channel_data: ChannelUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """チャンネル更新"""
    result = await db.execute(select(Channel).where(Channel.id == channel_id))
    channel = result.scalar_one_or_none()
    
    if not channel:
        raise HTTPException(status_code=404, detail="チャンネルが見つかりません")
    
    if channel.owner_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="このチャンネルを編集する権限がありません")
    
    # 更新データを適用
    update_data = channel_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(channel, key, value)
    
    await db.commit()
    await db.refresh(channel)
    
    return ChannelResponse.model_validate(channel)


@router.get("/{channel_id}/videos", response_model=list[VideoResponse])
async def get_channel_videos(
    channel_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """チャンネルの動画一覧を取得"""
    result = await db.execute(
        select(Video)
        .where(Video.channel_id == channel_id)
        .where(Video.visibility == "public")
        .where(Video.status == "published")
        .order_by(Video.published_at.desc())
    )
    videos = result.scalars().all()
    
    return [VideoResponse.model_validate(v) for v in videos]
