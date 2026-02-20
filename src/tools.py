import os
import re
import tempfile
import subprocess
from typing import Optional

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


# ***************************
# TikTok URL Utilities
# ***************************
def extract_tiktok_username(url: str) -> Optional[str]:
    """
    Extract TikTok username from various TikTok URL formats.

    Supported formats:
    - https://www.tiktok.com/@username/video/123456789
    - https://tiktok.com/@username/video/123456789
    - https://vm.tiktok.com/ZMxxx/ (short URL - cannot extract username)
    - https://www.tiktok.com/@username

    Returns:
        Username without @ prefix, or None if not found
    """
    if not url:
        return None

    try:
        match = re.search(r"/@([a-zA-Z0-9._]+)", url)
        return match.group(1) if match else None
    except Exception:
        return None


def format_tiktok_username(username: Optional[str]) -> Optional[str]:
    """
    Format username to ensure it has @ prefix for display.

    Returns:
        Username with @ prefix, or None if input is None
    """
    if not username:
        return None
    return username if username.startswith("@") else f"@{username}"
