from datetime import datetime
from uuid import UUID
from pydantic import BaseModel
from .auth import UserResponse


class CommentCreate(BaseModel):
    body: str


class CommentResponse(BaseModel):
    id: UUID
    video_id: UUID
    user_id: UUID
    body: str
    created_at: datetime
    user: UserResponse | None = None

    class Config:
        from_attributes = True


class CommentListResponse(BaseModel):
    comments: list[CommentResponse]
    total: int


class ReportCreate(BaseModel):
    target_type: str  # video, comment, user
    target_id: UUID
    reason: str
    detail: str | None = None


class ReportResponse(BaseModel):
    id: UUID
    reporter_user_id: UUID
    target_type: str
    target_id: UUID
    reason: str
    detail: str | None = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
