'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { ThumbsUp, Share2, Flag, User } from 'lucide-react';
import { Video, Comment, videosAPI, interactionsAPI } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import VideoPlayer from '@/components/VideoPlayer';
import styles from './page.module.css';

function formatViews(count: number): string {
  if (count >= 1000000) return `${(count / 1000000).toFixed(1)}M`;
  if (count >= 1000) return `${(count / 1000).toFixed(1)}K`;
  return count.toString();
}

function formatDate(dateString?: string): string {
  if (!dateString) return '';
  return new Date(dateString).toLocaleDateString('ja-JP', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
}

export default function WatchPage() {
  const params = useParams();
  const videoId = params.id as string;
  const { user, token } = useAuth();
  
  const [video, setVideo] = useState<Video | null>(null);
  const [comments, setComments] = useState<Comment[]>([]);
  const [newComment, setNewComment] = useState('');
  const [liked, setLiked] = useState(false);
  const [loading, setLoading] = useState(true);
  const [showFullDesc, setShowFullDesc] = useState(false);

  useEffect(() => {
    if (!videoId) return;
    
    setLoading(true);
    Promise.all([
      videosAPI.get(videoId),
      interactionsAPI.getComments(videoId),
    ])
      .then(([videoData, commentsData]) => {
        setVideo(videoData);
        setComments(commentsData.comments);
        // 視聴回数カウント
        videosAPI.recordView(videoId);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [videoId]);

  const handleLike = async () => {
    if (!token) return alert('ログインしてください');
    
    try {
      if (liked) {
        const res = await interactionsAPI.unlike(videoId, token);
        setVideo(v => v ? { ...v, like_count: res.like_count } : v);
        setLiked(false);
      } else {
        const res = await interactionsAPI.like(videoId, token);
        setVideo(v => v ? { ...v, like_count: res.like_count } : v);
        setLiked(true);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleComment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !newComment.trim()) return;
    
    try {
      const comment = await interactionsAPI.createComment(videoId, newComment, token);
      setComments([comment, ...comments]);
      setNewComment('');
      setVideo(v => v ? { ...v, comment_count: v.comment_count + 1 } : v);
    } catch (e) {
      console.error(e);
    }
  };

  const handleShare = () => {
    navigator.clipboard.writeText(window.location.href);
    alert('URLをコピーしました');
  };

  if (loading) {
    return (
      <div className={styles.container}>
        <div className={styles.playerSkeleton} />
      </div>
    );
  }

  if (!video) {
    return (
      <div className={styles.container}>
        <div className={styles.error}>動画が見つかりません</div>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <div className={styles.main}>
        {/* Player */}
        <div className={styles.playerWrapper}>
          <VideoPlayer
            src={video.hls_master_url || ''}
            poster={video.thumbnail_url}
          />
        </div>

        {/* Video Info */}
        <div className={styles.videoInfo}>
          <h1 className={styles.title}>{video.title}</h1>
          
          <div className={styles.meta}>
            <div className={styles.channel}>
              <div className={styles.channelAvatar}>
                {video.channel?.icon_url ? (
                  <img src={video.channel.icon_url} alt="" />
                ) : (
                  <User size={20} />
                )}
              </div>
              <div className={styles.channelInfo}>
                <span className={styles.channelName}>{video.channel?.name}</span>
                <span className={styles.subscribers}>
                  {formatViews(video.channel?.subscriber_count || 0)} チャンネル登録者
                </span>
              </div>
              <button className={styles.subscribeBtn}>登録</button>
            </div>
            
            <div className={styles.actions}>
              <button 
                className={`${styles.actionBtn} ${liked ? styles.liked : ''}`}
                onClick={handleLike}
              >
                <ThumbsUp size={20} />
                <span>{formatViews(video.like_count)}</span>
              </button>
              <button className={styles.actionBtn} onClick={handleShare}>
                <Share2 size={20} />
                <span>共有</span>
              </button>
              <button className={styles.actionBtn}>
                <Flag size={20} />
                <span>通報</span>
              </button>
            </div>
          </div>

          {/* Description */}
          <div className={styles.description}>
            <div className={styles.descStats}>
              {formatViews(video.view_count)} 回視聴 • {formatDate(video.published_at)}
            </div>
            <p className={showFullDesc ? '' : styles.descCollapsed}>
              {video.description || '説明はありません'}
            </p>
            {video.description && video.description.length > 200 && (
              <button 
                className={styles.showMore}
                onClick={() => setShowFullDesc(!showFullDesc)}
              >
                {showFullDesc ? '折りたたむ' : 'もっと見る'}
              </button>
            )}
            {video.tags.length > 0 && (
              <div className={styles.tags}>
                {video.tags.map(tag => (
                  <span key={tag} className={styles.tag}>#{tag}</span>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Comments */}
        <div className={styles.comments}>
          <h3>{video.comment_count} 件のコメント</h3>
          
          {user && (
            <form className={styles.commentForm} onSubmit={handleComment}>
              <div className={styles.commentAvatar}>
                {user.icon_url ? (
                  <img src={user.icon_url} alt="" />
                ) : (
                  <User size={16} />
                )}
              </div>
              <input
                type="text"
                placeholder="コメントを追加..."
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
                className={styles.commentInput}
              />
              <button 
                type="submit" 
                className="btn btn-primary"
                disabled={!newComment.trim()}
              >
                投稿
              </button>
            </form>
          )}
          
          <div className={styles.commentList}>
            {comments.map(comment => (
              <div key={comment.id} className={styles.comment}>
                <div className={styles.commentAvatar}>
                  {comment.user?.icon_url ? (
                    <img src={comment.user.icon_url} alt="" />
                  ) : (
                    <User size={16} />
                  )}
                </div>
                <div className={styles.commentContent}>
                  <div className={styles.commentHeader}>
                    <span className={styles.commentAuthor}>
                      {comment.user?.display_name || '匿名'}
                    </span>
                    <span className={styles.commentDate}>
                      {formatDate(comment.created_at)}
                    </span>
                  </div>
                  <p>{comment.body}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Sidebar - Related Videos */}
      <aside className={styles.sidebar}>
        <h3>関連動画</h3>
        <p className={styles.sidebarEmpty}>関連動画がまだありません</p>
      </aside>
    </div>
  );
}
