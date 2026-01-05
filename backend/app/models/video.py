import uuid
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, Text, Integer, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ..database import Base


class VideoVisibility(str, PyEnum):
    PUBLIC = "public"
    UNLISTED = "unlisted"
    PRIVATE = "private"


class VideoStatus(str, PyEnum):
    UPLOADING = "uploading"
    PROCESSING = "processing"
    READY = "ready"
    PUBLISHED = "published"
    FAILED = "failed"


class Video(Base):
    __tablename__ = "videos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    channel_id = Column(UUID(as_uuid=True), ForeignKey("channels.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    tags = Column(ARRAY(String), default=[])
    visibility = Column(Enum(VideoVisibility), default=VideoVisibility.PRIVATE, nullable=False)
    status = Column(Enum(VideoStatus), default=VideoStatus.UPLOADING, nullable=False)
    duration = Column(Integer, nullable=True)  # 秒
    source_url = Column(String(500), nullable=True)  # オリジナル動画URL
    hls_master_url = Column(String(500), nullable=True)  # HLSマスターURL
    thumbnail_url = Column(String(500), nullable=True)
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    published_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    channel = relationship("Channel", back_populates="videos")
    comments = relationship("Comment", back_populates="video", lazy="selectin")
    likes = relationship("Like", back_populates="video", lazy="selectin")
