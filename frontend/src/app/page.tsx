'use client';

import { useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { Video, videosAPI } from '@/lib/api';
import VideoCard from '@/components/VideoCard';
import styles from './page.module.css';

export default function HomePage() {
  const searchParams = useSearchParams();
  const query = searchParams.get('q') || '';
  const [videos, setVideos] = useState<Video[]>([]);
  const [loading, setLoading] = useState(true);
  const [sort, setSort] = useState<'new' | 'popular'>('new');

  useEffect(() => {
    setLoading(true);
    videosAPI.list({ q: query || undefined, sort })
      .then(res => setVideos(res.videos))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [query, sort]);

  return (
    <div className={styles.container}>
      {/* Hero Section */}
      {!query && (
        <section className={styles.hero}>
          <div className={styles.heroContent}>
            <h1 className={styles.heroTitle}>
              <span className="gradient-text">VideoHub</span>へようこそ
            </h1>
            <p className={styles.heroSubtitle}>
              動画をアップロード、共有、発見しよう
            </p>
          </div>
        </section>
      )}

      {/* Search Results Header */}
      {query && (
        <div className={styles.searchHeader}>
          <h2>「{query}」の検索結果</h2>
          <span>{videos.length} 件の動画</span>
        </div>
      )}

      {/* Sort Buttons */}
      <div className={styles.sortBar}>
        <button
          className={`${styles.sortBtn} ${sort === 'new' ? styles.active : ''}`}
          onClick={() => setSort('new')}
        >
          新着
        </button>
        <button
          className={`${styles.sortBtn} ${sort === 'popular' ? styles.active : ''}`}
          onClick={() => setSort('popular')}
        >
          人気
        </button>
      </div>

      {/* Video Grid */}
      {loading ? (
        <div className={styles.videoGrid}>
          {[...Array(8)].map((_, i) => (
            <div key={i} className={styles.skeleton}>
              <div className={styles.skeletonThumb} />
              <div className={styles.skeletonInfo}>
                <div className={styles.skeletonAvatar} />
                <div className={styles.skeletonMeta}>
                  <div className={styles.skeletonTitle} />
                  <div className={styles.skeletonChannel} />
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : videos.length > 0 ? (
        <div className={styles.videoGrid}>
          {videos.map(video => (
            <VideoCard key={video.id} video={video} />
          ))}
        </div>
      ) : (
        <div className={styles.empty}>
          <div className={styles.emptyIcon}>📹</div>
          <h3>動画が見つかりません</h3>
          <p>最初の動画をアップロードしてみましょう！</p>
        </div>
      )}
    </div>
  );
}
