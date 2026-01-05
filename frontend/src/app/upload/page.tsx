'use client';

import { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Upload, X, Image, Check } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { videosAPI, channelsAPI, Channel } from '@/lib/api';
import styles from './page.module.css';

export default function UploadPage() {
  const router = useRouter();
  const { user, token } = useAuth();
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const [channels, setChannels] = useState<Channel[]>([]);
  const [selectedChannel, setSelectedChannel] = useState<string>('');
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [tags, setTags] = useState('');
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState<'idle' | 'uploading' | 'processing' | 'done' | 'error'>('idle');
  const [error, setError] = useState('');

  useEffect(() => {
    if (!user || !token) return;
    
    // ユーザーのチャンネルを取得（MVPでは仮で作成）
    // 実際にはチャンネル一覧APIが必要
    channelsAPI.create({ name: `${user.display_name}のチャンネル` }, token)
      .then(channel => {
        setChannels([channel]);
        setSelectedChannel(channel.id);
      })
      .catch(() => {
        // チャンネル既存の場合は無視
      });
  }, [user, token]);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      if (!selectedFile.type.startsWith('video/')) {
        setError('動画ファイルを選択してください');
        return;
      }
      setFile(selectedFile);
      setTitle(selectedFile.name.replace(/\.[^/.]+$/, ''));
      setError('');
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile?.type.startsWith('video/')) {
      setFile(droppedFile);
      setTitle(droppedFile.name.replace(/\.[^/.]+$/, ''));
      setError('');
    } else {
      setError('動画ファイルを選択してください');
    }
  };

  const handleUpload = async () => {
    if (!file || !token || !selectedChannel || !title.trim()) {
      setError('必須項目を入力してください');
      return;
    }

    setUploading(true);
    setStatus('uploading');
    setError('');

    try {
      // 1. アップロード初期化
      const initRes = await videosAPI.initUpload({
        channel_id: selectedChannel,
        title,
        description,
        tags: tags.split(',').map(t => t.trim()).filter(Boolean),
      }, token);

      // 2. プリサインURLへアップロード
      const xhr = new XMLHttpRequest();
      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) {
          setProgress(Math.round((e.loaded / e.total) * 100));
        }
      };

      await new Promise<void>((resolve, reject) => {
        xhr.open('PUT', initRes.upload_url);
        xhr.setRequestHeader('Content-Type', 'video/mp4');
        xhr.onload = () => xhr.status === 200 ? resolve() : reject(new Error('アップロード失敗'));
        xhr.onerror = () => reject(new Error('アップロード失敗'));
        xhr.send(file);
      });

      // 3. アップロード完了通知 → 変換開始
      setStatus('processing');
      await videosAPI.completeUpload(initRes.video_id, token);

      setStatus('done');
      setTimeout(() => {
        router.push('/');
      }, 2000);

    } catch (e) {
      console.error(e);
      setError(e instanceof Error ? e.message : 'アップロードに失敗しました');
      setStatus('error');
    } finally {
      setUploading(false);
    }
  };

  if (!user) {
    return (
      <div className={styles.container}>
        <div className={styles.authPrompt}>
          <h2>ログインが必要です</h2>
          <p>動画をアップロードするにはログインしてください</p>
          <a href="/auth/login" className="btn btn-primary">ログイン</a>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <h1 className={styles.title}>動画をアップロード</h1>

      {!file ? (
        <div 
          className={styles.dropzone}
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept="video/*"
            onChange={handleFileSelect}
            hidden
          />
          <Upload size={48} className={styles.dropzoneIcon} />
          <h3>動画ファイルをドラッグ＆ドロップ</h3>
          <p>または、クリックしてファイルを選択</p>
          <span className={styles.dropzoneHint}>MP4, MOV, AVI（最大5GB）</span>
        </div>
      ) : (
        <div className={styles.uploadForm}>
          {/* Preview */}
          <div className={styles.preview}>
            <div className={styles.previewThumb}>
              <Image size={32} />
            </div>
            <div className={styles.previewInfo}>
              <span className={styles.fileName}>{file.name}</span>
              <span className={styles.fileSize}>
                {(file.size / 1024 / 1024).toFixed(2)} MB
              </span>
            </div>
            {status === 'idle' && (
              <button 
                className={styles.removeBtn}
                onClick={() => setFile(null)}
              >
                <X size={20} />
              </button>
            )}
          </div>

          {/* Progress */}
          {status !== 'idle' && (
            <div className={styles.progressSection}>
              <div className={styles.progressBar}>
                <div 
                  className={styles.progressFill}
                  style={{ width: status === 'done' ? '100%' : `${progress}%` }}
                />
              </div>
              <div className={styles.progressStatus}>
                {status === 'uploading' && `アップロード中... ${progress}%`}
                {status === 'processing' && '変換処理中...'}
                {status === 'done' && (
                  <span className={styles.success}>
                    <Check size={16} /> 完了！リダイレクト中...
                  </span>
                )}
                {status === 'error' && (
                  <span className={styles.errorText}>{error}</span>
                )}
              </div>
            </div>
          )}

          {/* Form */}
          {status === 'idle' && (
            <>
              <div className={styles.formGroup}>
                <label>タイトル *</label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="input"
                  placeholder="動画のタイトル"
                  maxLength={100}
                />
              </div>

              <div className={styles.formGroup}>
                <label>説明</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className={styles.textarea}
                  placeholder="動画の説明を入力"
                  rows={4}
                />
              </div>

              <div className={styles.formGroup}>
                <label>タグ（カンマ区切り）</label>
                <input
                  type="text"
                  value={tags}
                  onChange={(e) => setTags(e.target.value)}
                  className="input"
                  placeholder="ゲーム, 実況, エンタメ"
                />
              </div>

              {error && <p className={styles.error}>{error}</p>}

              <button 
                className={styles.uploadBtn}
                onClick={handleUpload}
                disabled={!title.trim()}
              >
                <Upload size={20} />
                アップロード開始
              </button>
            </>
          )}
        </div>
      )}
    </div>
  );
}
