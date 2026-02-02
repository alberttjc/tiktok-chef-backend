import os
import json
import tempfile
import subprocess
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai.types import GenerateContentConfig, Part
from pydantic import ValidationError
from langchain_core.tools import tool

# import local modules
from src.logger import get_logger
from src.schema import Recipe
from src.config import RECIPE_VIDEO_PROMPT, GEMINI_MODEL

# Initialize logger
logger = get_logger(__name__)


# load environment variables
load_dotenv()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)


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
# LLM Function
# ***************************
def transcribe_recipe(video_url: str) -> Recipe:
    """
    Extract structured recipe data using Gemini + Pydantic.
    Downloads the video first, then sends it to Gemini for analysis.
    """
    video_path = None

    try:
        # Download the video
        video_path = download_tiktok_video(video_url)

        # Upload video to Gemini
        logger.info(f"Uploading video to Gemini: {video_path}")
        with open(video_path, 'rb') as video_file:
            video_data = video_file.read()

        # Create video part
        video_part = Part.from_bytes(
            data=video_data,
            mime_type="video/mp4"
        )

        # Call Gemini with video
        logger.info("Analyzing video with Gemini API")
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[video_part, RECIPE_VIDEO_PROMPT],
            config=GenerateContentConfig(
                response_json_schema=Recipe.model_json_schema(),
                response_mime_type="application/json",
                temperature=0.2,
            ),
        )

        if not response.text:
            raise RuntimeError("Empty response from Gemini")

        try:
            data = json.loads(response.text)
            recipe = Recipe.model_validate(data)
            logger.info("Successfully parsed and validated recipe from Gemini response")
            return recipe

        except json.JSONDecodeError as e:
            logger.error(f"Gemini returned invalid JSON: {str(e)}")
            raise RuntimeError("Gemini returned invalid JSON") from e

        except ValidationError as e:
            logger.error(f"Response did not match recipe schema: {str(e)}")
            raise RuntimeError("Response did not match recipe schema") from e

    finally:
        # Clean up downloaded video
        if video_path and os.path.exists(video_path):
            try:
                temp_dir = os.path.dirname(video_path)
                os.remove(video_path)
                os.rmdir(temp_dir)
                logger.info("Cleaned up temporary video file")
            except Exception as e:
                logger.warning(f"Failed to clean up video file: {str(e)}")


# ***************************
# Graph Tools
# ***************************
@tool
def extract_recipe_from_url(video_url: str) -> dict:
    """
    Extract recipe using direct gemini client
    """
    try:
        recipe = transcribe_recipe(video_url=video_url)
        return {
            "success": True,
            "recipe": recipe,
            "error": None,
        }

    except Exception as e:
        return {
            "success": False,
            "recipe": None,
            "error": str(e),
        }
