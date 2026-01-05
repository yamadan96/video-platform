'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { User, Video as VideoIcon } from 'lucide-react';
import { Channel, Video, channelsAPI } from '@/lib/api';
import VideoCard from '@/components/VideoCard';
import styles from './page.module.css';

function formatCount(count: number): string {
  if (count >= 1000000) return `${(count / 1000000).toFixed(1)}M`;
  if (count >= 1000) return `${(count / 1000).toFixed(1)}K`;
  return count.toString();
}

export default function ChannelPage() {
  const params = useParams();
  const channelId = params.id as string;
  
  const [channel, setChannel] = useState<Channel | null>(null);
  const [videos, setVideos] = useState<Video[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!channelId) return;
    
    setLoading(true);
    Promise.all([
      channelsAPI.get(channelId),
      channelsAPI.getVideos(channelId),
    ])
      .then(([channelData, videosData]) => {
        setChannel(channelData);
        setVideos(videosData);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [channelId]);

  if (loading) {
    return (
      <div className={styles.container}>
        <div className={styles.bannerSkeleton} />
      </div>
    );
  }

  if (!channel) {
    return (
      <div className={styles.container}>
        <div className={styles.error}>チャンネルが見つかりません</div>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      {/* Banner */}
      <div className={styles.banner}>
        {channel.banner_url ? (
          <img src={channel.banner_url} alt="" />
        ) : (
          <div className={styles.bannerPlaceholder} />
        )}
      </div>

      {/* Channel Info */}
      <div className={styles.channelHeader}>
        <div className={styles.avatar}>
          {channel.icon_url ? (
            <img src={channel.icon_url} alt={channel.name} />
          ) : (
            <User size={48} />
          )}
        </div>
        
        <div className={styles.channelInfo}>
          <h1>{channel.name}</h1>
          <p className={styles.stats}>
            {formatCount(channel.subscriber_count)} 登録者 • {videos.length} 本の動画
          </p>
          {channel.description && (
            <p className={styles.description}>{channel.description}</p>
          )}
        </div>

        <button className={styles.subscribeBtn}>登録</button>
      </div>

      {/* Tabs */}
      <div className={styles.tabs}>
        <button className={`${styles.tab} ${styles.active}`}>動画</button>
        <button className={styles.tab}>再生リスト</button>
        <button className={styles.tab}>概要</button>
      </div>

      {/* Videos Grid */}
      <div className={styles.content}>
        {videos.length > 0 ? (
          <div className={styles.videoGrid}>
            {videos.map(video => (
              <VideoCard key={video.id} video={video} />
            ))}
          </div>
        ) : (
          <div className={styles.empty}>
            <VideoIcon size={48} />
            <h3>動画がありません</h3>
            <p>このチャンネルにはまだ動画がアップロードされていません</p>
          </div>
        )}
      </div>
    </div>
  );
}
