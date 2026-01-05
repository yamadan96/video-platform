from datetime import datetime
from uuid import UUID
from pydantic import BaseModel
from .channel import ChannelResponse


class VideoBase(BaseModel):
    title: str
    description: str | None = None
    tags: list[str] = []


class VideoCreate(VideoBase):
    channel_id: UUID


class VideoUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    tags: list[str] | None = None
    visibility: str | None = None


class VideoResponse(BaseModel):
    id: UUID
    channel_id: UUID
    title: str
    description: str | None = None
    tags: list[str]
    visibility: str
    status: str
    duration: int | None = None
    thumbnail_url: str | None = None
    hls_master_url: str | None = None
    view_count: int
    like_count: int
    comment_count: int
    published_at: datetime | None = None
    created_at: datetime
    channel: ChannelResponse | None = None

    class Config:
        from_attributes = True


class VideoListResponse(BaseModel):
    videos: list[VideoResponse]
    total: int
    page: int
    per_page: int


class UploadInitResponse(BaseModel):
    video_id: UUID
    upload_url: str
    expires_in: int = 3600


class UploadCompleteRequest(BaseModel):
    video_id: UUID
