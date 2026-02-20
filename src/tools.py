import os
import tempfile
import subprocess

# import local modules
from src.logger import get_logger

# Initialize logger
logger = get_logger(__name__)


# ***************************
# Video Download Function
# ***************************
def download_tiktok_video(video_url: str) -> str:
    """
    Download TikTok video and return path to local file.
    Uses yt-dlp to download the video.
    """
    logger.info(f"Downloading video from: {video_url}")

    # Create temp directory for videos
    temp_dir = tempfile.mkdtemp(prefix="tiktok_")
    output_path = os.path.join(temp_dir, "video.mp4")

    try:
        # Use yt-dlp to download TikTok video
        result = subprocess.run(
            [
                "yt-dlp",
                "-f", "best",
                "-o", output_path,
                video_url
            ],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            logger.error(f"Failed to download video: {result.stderr}")
            raise RuntimeError(f"Video download failed: {result.stderr}")

        if not os.path.exists(output_path):
            raise RuntimeError("Video file not found after download")

        logger.info(f"Video downloaded successfully to: {output_path}")
        return output_path

    except subprocess.TimeoutExpired:
        logger.error("Video download timed out")
        raise RuntimeError("Video download timed out")
    except Exception as e:
        logger.error(f"Error downloading video: {str(e)}")
        raise RuntimeError(f"Error downloading video: {str(e)}")
