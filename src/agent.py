import os
import json
from google import genai
from google.genai.types import GenerateContentConfig, Part
from pydantic import ValidationError

# import local modules
from src.config import get_settings
from src.logger import get_logger
from src.tools import download_tiktok_video
from src.schema import Recipe

# Initialize logger
logger = get_logger(__name__)


class RecipeAgent:
    def __init__(self):
        self.extraction_results: dict = None
        self.video_url: str = ""
        self.video_path: str = ""
        self.settings = get_settings()
        self.client = genai.Client(api_key=self.settings.gemini_api_key)

    def _download_video(self, video_url: str) -> None:
        """Download tiktok video and return path to local file.
        Uses yt-dlp to download the video."""
        self.video_path = download_tiktok_video(video_url=video_url)

    def _llm_call(self, video_part: Part) -> Recipe:
        response = self.client.models.generate_content(
            model=self.settings.gemini_model,
            contents=[video_part, self.settings.recipe_video_prompt],
            config=GenerateContentConfig(
                response_json_schema=Recipe.model_json_schema(),
                response_mime_type="application/json",
                temperature=0.2,
            ),
        )

        if not response.text:
            raise RuntimeError("No response")

        try:
            data = json.loads(response.text)
            recipe = Recipe.model_validate(data)
            return recipe

        except json.JSONDecodeError as e:
            logger.error(f"Gemini returned invalid JSON: {str(e)}")
            raise RuntimeError("Gemini returned invalid JSON") from e

        except ValidationError as e:
            logger.error(f"Response did not match recipe schema: {str(e)}")
            raise RuntimeError("Response Error") from e

    def transcribe_recipe(self, video_url: str) -> Recipe:
        try:
            # Download tiktok video
            self._download_video(video_url=video_url)

            # Upload video to Gemini
            with open(self.video_path, "rb") as video_file:
                video_data = video_file.read()

            # Create video part
            video_part = Part.from_bytes(data=video_data, mime_type="video/mp4")
            # Extract response
            recipe = self._llm_call(video_part)

            return recipe

        finally:
            # Clean up video path
            if self.video_path and os.path.exists(self.video_path):
                try:
                    temp_dir = os.path.dirname(self.video_path)
                    os.remove(self.video_path)
                    os.rmdir(temp_dir)
                except Exception as e:
                    logger.warning(f"Failed to clean up video file: {str(e)}")


if __name__ == "__main__":
    recipe = RecipeAgent().transcribe_recipe(
        video_url="https://www.tiktok.com/@khanhong/video/7557275818255273234"
    )
    logger.info(f"Extracted recipe: {recipe.recipe_overview.title}")
