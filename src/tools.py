import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai.types import GenerateContentConfig
from pydantic import ValidationError
from langchain_core.tools import tool

# import local modules
from src.logger import get_logger
from src.schema import Recipe
from src.config import RECIPE_URL_PROMPT, GEMINI_MODEL

# Initialize logger
logger = get_logger(__name__)


# load environment variables
load_dotenv()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)


# ***************************
# LLM Function
# ***************************
def transcribe_recipe(video_url: str) -> Recipe:
    """
    Extract structured recipe data using Gemini + Pydantic
    """
    logger.info(f"Calling Gemini API for URL: {video_url}")
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=RECIPE_URL_PROMPT.format(video_url=video_url),
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
