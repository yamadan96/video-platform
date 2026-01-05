from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..models import Comment, CommentStatus, Like, Report, Video, User
from ..schemas import CommentCreate, CommentResponse, CommentListResponse, ReportCreate, ReportResponse
from .auth import get_current_user

router = APIRouter(tags=["インタラクション"])


# ========== いいね ==========

@router.post("/videos/{video_id}/like")
async def like_video(
    video_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """動画にいいね"""
    # 動画存在チェック
    video_result = await db.execute(select(Video).where(Video.id == video_id))
    video = video_result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="動画が見つかりません")
    
    # 既存のいいねチェック
    like_result = await db.execute(
        select(Like).where(Like.user_id == current_user.id, Like.video_id == video_id)
    )
    existing_like = like_result.scalar_one_or_none()
    
    if existing_like:
        raise HTTPException(status_code=400, detail="既にいいねしています")
    
    # いいね追加
    like = Like(user_id=current_user.id, video_id=video_id)
    db.add(like)
    video.like_count += 1
    await db.commit()
    
    return {"liked": True, "like_count": video.like_count}


@router.delete("/videos/{video_id}/like")
async def unlike_video(
    video_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """いいねを解除"""
    video_result = await db.execute(select(Video).where(Video.id == video_id))
    video = video_result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="動画が見つかりません")
    
    like_result = await db.execute(
        select(Like).where(Like.user_id == current_user.id, Like.video_id == video_id)
    )
    existing_like = like_result.scalar_one_or_none()
    
    if not existing_like:
        raise HTTPException(status_code=400, detail="いいねしていません")
    
    await db.delete(existing_like)
    video.like_count = max(0, video.like_count - 1)
    await db.commit()
    
    return {"liked": False, "like_count": video.like_count}


# ========== コメント ==========

@router.get("/videos/{video_id}/comments", response_model=CommentListResponse)
async def get_comments(
    video_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """動画のコメント一覧を取得"""
    result = await db.execute(
        select(Comment)
        .where(Comment.video_id == video_id)
        .where(Comment.status == CommentStatus.ACTIVE)
        .order_by(Comment.created_at.desc())
    )
    comments = result.scalars().all()
    
    return CommentListResponse(
        comments=[CommentResponse.model_validate(c) for c in comments],
        total=len(comments)
    )


@router.post("/videos/{video_id}/comments", response_model=CommentResponse)
async def create_comment(
    video_id: UUID,
    comment_data: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """コメント投稿"""
    # 動画存在チェック
    video_result = await db.execute(select(Video).where(Video.id == video_id))
    video = video_result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="動画が見つかりません")
    
    # コメント作成
    comment = Comment(
        video_id=video_id,
        user_id=current_user.id,
        body=comment_data.body,
    )
    db.add(comment)
    video.comment_count += 1
    await db.commit()
    await db.refresh(comment)
    
    return CommentResponse.model_validate(comment)


@router.delete("/videos/{video_id}/comments/{comment_id}")
async def delete_comment(
    video_id: UUID,
    comment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """コメント削除"""
    result = await db.execute(
        select(Comment).where(Comment.id == comment_id, Comment.video_id == video_id)
    )
    comment = result.scalar_one_or_none()
    
    if not comment:
        raise HTTPException(status_code=404, detail="コメントが見つかりません")
    
    if comment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="このコメントを削除する権限がありません")
    
    comment.status = CommentStatus.DELETED
    comment.deleted_at = datetime.utcnow()
    
    # 動画のコメント数を減らす
    video_result = await db.execute(select(Video).where(Video.id == video_id))
    video = video_result.scalar_one_or_none()
    if video:
        video.comment_count = max(0, video.comment_count - 1)
    
    await db.commit()
    
    return {"deleted": True}


# ========== 通報 ==========

@router.post("/reports", response_model=ReportResponse)
async def create_report(
    report_data: ReportCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """通報を送信"""
    report = Report(
        reporter_user_id=current_user.id,
        target_type=report_data.target_type,
        target_id=report_data.target_id,
        reason=report_data.reason,
        detail=report_data.detail,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    
    return ReportResponse.model_validate(report)
