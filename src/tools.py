import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai.types import GenerateContentConfig
from pydantic import ValidationError
from langchain_core.tools import tool

# import local modules
from src.schema import Recipe
from src.config import RECIPE_URL_PROMPT, GEMINI_MODEL


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
        return recipe

    except json.JSONDecodeError as e:
        raise RuntimeError("Gemini returned invalid JSON") from e

    except ValidationError as e:
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


@tool
def validate_recipe_structure(recipe_data: Recipe) -> dict:
    """
    Validate recipe data aginst Recipe schema
    """
    try:
        recipe = Recipe.model_validate(recipe_data)
        return {
            "is_valid": True,
            "recipe": recipe,
            "error": None,
        }

    except Exception as e:
        return {
            "is_valid": False,
            "recipe": None,
            "error": str(e),
        }
