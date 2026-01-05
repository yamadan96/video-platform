import Link from 'next/link';
import { Video } from '@/lib/api';
import styles from './VideoCard.module.css';

interface VideoCardProps {
  video: Video;
}

function formatDuration(seconds?: number): string {
  if (!seconds) return '0:00';
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function formatViews(count: number): string {
  if (count >= 1000000) return `${(count / 1000000).toFixed(1)}M`;
  if (count >= 1000) return `${(count / 1000).toFixed(1)}K`;
  return count.toString();
}

function formatDate(dateString?: string): string {
  if (!dateString) return '';
  const date = new Date(dateString);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const days = Math.floor(diff / (1000 * 60 * 60 * 24));
  
  if (days === 0) return '今日';
  if (days === 1) return '昨日';
  if (days < 7) return `${days}日前`;
  if (days < 30) return `${Math.floor(days / 7)}週間前`;
  if (days < 365) return `${Math.floor(days / 30)}ヶ月前`;
  return `${Math.floor(days / 365)}年前`;
}

export default function VideoCard({ video }: VideoCardProps) {
  return (
    <Link href={`/watch/${video.id}`} className={styles.card}>
      <div className={styles.thumbnail}>
        {video.thumbnail_url ? (
          <img src={video.thumbnail_url} alt={video.title} />
        ) : (
          <div className={styles.thumbnailPlaceholder}>
            <span>▶</span>
          </div>
        )}
        <span className={styles.duration}>{formatDuration(video.duration)}</span>
      </div>
      
      <div className={styles.info}>
        <div className={styles.channelAvatar}>
          {video.channel?.icon_url ? (
            <img src={video.channel.icon_url} alt={video.channel.name} />
          ) : (
            <span>{video.channel?.name?.[0] || 'C'}</span>
          )}
        </div>
        
        <div className={styles.meta}>
          <h3 className={styles.title}>{video.title}</h3>
          <p className={styles.channel}>{video.channel?.name || '不明なチャンネル'}</p>
          <p className={styles.stats}>
            {formatViews(video.view_count)} 回視聴 • {formatDate(video.published_at)}
          </p>
        </div>
      </div>
    </Link>
  );
}
