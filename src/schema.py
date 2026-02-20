from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Literal, List, Any, Dict
from src.config import get_settings


# ***************************
# Recipe Data Schema
# ***************************
class RecipeOverview(BaseModel):
    id: Optional[int] = None
    title: str
    source_url: Optional[str] = None
    creator_username: Optional[str] = None
    prep_time: Optional[str] = None
    cook_time: Optional[str] = None
    servings: int
    difficulty: Optional[Literal["Easy", "Intermediate", "Advanced"]] = None
    cuisine_type: Optional[str] = None


class Ingredient(BaseModel):
    item: str
    amount: str
    unit: Optional[str] = None
    notes: Optional[str] = None


class Recipe(BaseModel):
    id: Optional[int] = None
    recipe_overview: RecipeOverview
    ingredients: List[Ingredient]
    instructions: List[str]


# ***************************
# API Request/Response Models
# ***************************
class RecipeExtractionRequest(BaseModel):
    video_url: HttpUrl = Field(..., description="URL of the cooking video")
    max_retries: int = Field(
        default=2, ge=0, le=5, description="Maximum number of retry attempts"
    )


class RecipeExtractionResponse(BaseModel):
    success: bool = Field(
        ..., description="Whether the recipe was extracted successfully"
    )
    recipe: Optional[Recipe] = Field(None, description="The extracted recipe data")
    metadata: Dict[str, Any] = Field(
        ...,
        description="Processing metadata including steps, validation status, and errors",
    )
    processing_time: Optional[float] = Field(
        None, description="Total processing time in seconds"
    )


class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(
        None, description="Additional error details"
    )


class HealthResponse(BaseModel):
    status: str = Field(default="healthy", description="API health status")
    version: str = Field(default_factory=lambda: get_settings().app_version, description="API version")


# ***************************
# Database API Models
# ***************************
class SaveRecipeRequest(BaseModel):
    recipe: Recipe = Field(..., description="Recipe data to save")
    source_url: Optional[HttpUrl] = Field(None, description="Original video URL")
    creator_username: Optional[str] = Field(None, description="TikTok creator username")


class SaveRecipeResponse(BaseModel):
    success: bool = Field(..., description="Whether the recipe was saved successfully")
    recipe_id: int = Field(..., description="ID of the saved recipe")
    message: str = Field(..., description="Success message")


class GetRecipesResponse(BaseModel):
    success: bool = Field(
        ..., description="Whether recipes were retrieved successfully"
    )
    recipes: List[Recipe] = Field(..., description="List of recipes")
    count: int = Field(..., description="Number of recipes returned")


class GetRecipeResponse(BaseModel):
    success: bool = Field(..., description="Whether recipe was retrieved successfully")
    recipe: Recipe = Field(..., description="Recipe data")


class DeleteRecipeResponse(BaseModel):
    success: bool = Field(..., description="Whether recipe was deleted successfully")
    message: str = Field(..., description="Deletion status message")


class UpdateRecipeRequest(BaseModel):
    recipe: Recipe = Field(..., description="Updated recipe data")
    source_url: Optional[HttpUrl] = Field(
        None, description="Updated original video URL"
    )
    creator_username: Optional[str] = Field(None, description="TikTok creator username")


class UpdateRecipeResponse(BaseModel):
    success: bool = Field(..., description="Whether recipe was updated successfully")
    recipe_id: int = Field(..., description="ID of the updated recipe")
    message: str = Field(..., description="Update status message")
