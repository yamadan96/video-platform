from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class ChannelBase(BaseModel):
    name: str
    description: str | None = None


class ChannelCreate(ChannelBase):
    pass


class ChannelUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    icon_url: str | None = None
    banner_url: str | None = None


class ChannelResponse(BaseModel):
    id: UUID
    owner_user_id: UUID
    name: str
    description: str | None = None
    icon_url: str | None = None
    banner_url: str | None = None
    subscriber_count: int
    created_at: datetime

    class Config:
        from_attributes = True
