import os
import subprocess
import tempfile
from uuid import UUID
import boto3
from botocore.config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .celery_app import celery_app
from ..core.config import settings
from ..models import Video, VideoStatus


def get_sync_db():
    """同期DBセッションを取得（Celeryタスク用）"""
    engine = create_engine(settings.database_url)
    Session = sessionmaker(bind=engine)
    return Session()


def get_s3_client():
    """S3クライアント取得"""
    return boto3.client(
        "s3",
        endpoint_url=f"http://{settings.minio_endpoint}",
        aws_access_key_id=settings.minio_access_key,
        aws_secret_access_key=settings.minio_secret_key,
        config=Config(signature_version="s3v4"),
    )


@celery_app.task(bind=True, max_retries=3)
def transcode_video(self, video_id: str):
    """動画をHLS形式に変換"""
    db = get_sync_db()
    s3 = get_s3_client()
    
    try:
        # 動画取得
        video = db.query(Video).filter(Video.id == UUID(video_id)).first()
        if not video:
            raise ValueError(f"Video not found: {video_id}")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "input.mp4")
            output_dir = os.path.join(tmpdir, "hls")
            os.makedirs(output_dir)
            
            # S3から動画をダウンロード
            s3.download_file(
                settings.minio_bucket,
                video.source_url,
                input_path
            )
            
            # FFmpegでHLS変換
            # 複数解像度: 1080p, 720p, 480p
            output_master = os.path.join(output_dir, "master.m3u8")
            
            cmd = [
                "ffmpeg", "-i", input_path,
                "-filter_complex",
                "[0:v]split=3[v1][v2][v3];"
                "[v1]scale=w=1920:h=1080[v1out];"
                "[v2]scale=w=1280:h=720[v2out];"
                "[v3]scale=w=854:h=480[v3out]",
                "-map", "[v1out]", "-c:v:0", "libx264", "-b:v:0", "5M",
                "-map", "[v2out]", "-c:v:1", "libx264", "-b:v:1", "3M",
                "-map", "[v3out]", "-c:v:2", "libx264", "-b:v:2", "1M",
                "-map", "0:a?", "-c:a", "aac", "-b:a", "128k",
                "-f", "hls",
                "-hls_time", "6",
                "-hls_list_size", "0",
                "-hls_segment_filename", os.path.join(output_dir, "segment_%v_%03d.ts"),
                "-master_pl_name", "master.m3u8",
                "-var_stream_map", "v:0,a:0 v:1,a:1 v:2,a:2",
                os.path.join(output_dir, "stream_%v.m3u8"),
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(f"FFmpeg failed: {result.stderr}")
            
            # サムネイル生成
            thumbnail_path = os.path.join(tmpdir, "thumbnail.jpg")
            subprocess.run([
                "ffmpeg", "-i", input_path,
                "-ss", "00:00:01",
                "-vframes", "1",
                "-q:v", "2",
                thumbnail_path
            ], capture_output=True)
            
            # 動画の長さ取得
            duration_result = subprocess.run([
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                input_path
            ], capture_output=True, text=True)
            duration = int(float(duration_result.stdout.strip())) if duration_result.stdout.strip() else 0
            
            # S3にアップロード
            hls_base_key = f"videos/{video_id}/hls"
            
            for filename in os.listdir(output_dir):
                filepath = os.path.join(output_dir, filename)
                s3_key = f"{hls_base_key}/{filename}"
                content_type = "application/x-mpegURL" if filename.endswith(".m3u8") else "video/MP2T"
                s3.upload_file(filepath, settings.minio_bucket, s3_key, ExtraArgs={"ContentType": content_type})
            
            # サムネイルアップロード
            thumbnail_key = f"videos/{video_id}/thumbnail.jpg"
            if os.path.exists(thumbnail_path):
                s3.upload_file(thumbnail_path, settings.minio_bucket, thumbnail_key, ExtraArgs={"ContentType": "image/jpeg"})
            
            # DB更新
            video.hls_master_url = f"http://{settings.minio_endpoint}/{settings.minio_bucket}/{hls_base_key}/master.m3u8"
            video.thumbnail_url = f"http://{settings.minio_endpoint}/{settings.minio_bucket}/{thumbnail_key}"
            video.duration = duration
            video.status = VideoStatus.READY
            db.commit()
            
            return {"status": "success", "video_id": video_id}
            
    except Exception as e:
        # エラー時
        video = db.query(Video).filter(Video.id == UUID(video_id)).first()
        if video:
            video.status = VideoStatus.FAILED
            db.commit()
        raise self.retry(exc=e, countdown=60)
    finally:
        db.close()
