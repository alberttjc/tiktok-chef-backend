from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Prompts
RECIPE_VIDEO_PROMPT = """
You are a professional chef that extracts recipe information from cooking videos.
Analyze the video content carefully and provide detailed ingredient lists and cooking instructions.

Watch the entire video and identify:
- The exact recipe being prepared
- All ingredients used (with measurements if shown)
- Step-by-step cooking instructions
- Preparation and cooking times if mentioned
- Difficulty level and cuisine type

Focus on precise measurements and important cooking instruction notes.
Be accurate - only extract information that is clearly shown or mentioned in the video.
"""


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_version: str = "0.1.0"

    # Gemini
    gemini_api_key: str
    gemini_model: str = "gemini-2.5-flash"

    # Supabase
    supabase_url: str
    supabase_key: str

    # CORS — comma-separated list of allowed origins
    allowed_origins_str: str = (
        "http://localhost:3000,http://localhost:5173,http://localhost:8000"
    )

    # Auth — optional; empty string means dev mode (no auth enforced)
    api_key: str = ""

    @field_validator("gemini_api_key", "supabase_url", "supabase_key", mode="before")
    @classmethod
    def must_not_be_empty(cls, v: str, info) -> str:
        if not v or not v.strip():
            raise ValueError(f"{info.field_name} must not be empty")
        return v

    @property
    def allowed_origins(self) -> List[str]:
        return [o.strip() for o in self.allowed_origins_str.split(",") if o.strip()]

    @property
    def recipe_video_prompt(self) -> str:
        return RECIPE_VIDEO_PROMPT


@lru_cache
def get_settings() -> Settings:
    return Settings()
