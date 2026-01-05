import uuid
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, Text, UniqueConstraint, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ..database import Base


class CommentStatus(str, PyEnum):
    ACTIVE = "active"
    DELETED = "deleted"
    HIDDEN = "hidden"


class Comment(Base):
    __tablename__ = "comments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    body = Column(Text, nullable=False)
    status = Column(Enum(CommentStatus), default=CommentStatus.ACTIVE, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    video = relationship("Video", back_populates="comments")
    user = relationship("User", back_populates="comments")


class Like(Base):
    __tablename__ = "likes"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id"), primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="likes")
    video = relationship("Video", back_populates="likes")


class ReportReason(str, PyEnum):
    SPAM = "spam"
    VIOLENCE = "violence"
    ADULT = "adult"
    COPYRIGHT = "copyright"
    HATE = "hate"
    OTHER = "other"


class ReportStatus(str, PyEnum):
    OPEN = "open"
    IN_REVIEW = "in_review"
    CLOSED = "closed"


class ReportTargetType(str, PyEnum):
    VIDEO = "video"
    COMMENT = "comment"
    USER = "user"


class Report(Base):
    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reporter_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    target_type = Column(Enum(ReportTargetType), nullable=False)
    target_id = Column(UUID(as_uuid=True), nullable=False)
    reason = Column(Enum(ReportReason), nullable=False)
    detail = Column(Text, nullable=True)
    status = Column(Enum(ReportStatus), default=ReportStatus.OPEN, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class WatchHistory(Base):
    __tablename__ = "watch_history"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id"), primary_key=True)
    last_position_sec = Column(Integer, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
