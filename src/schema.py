from enum import Enum
from pydantic import BaseModel, Field, HttpUrl
from typing import Annotated, Sequence, Optional, Literal, List, Any, Dict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from src.config import APP_VERSION


# ***************************
# Enum Status
# ***************************
class STATUS(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    FAILED = "failed"
    SUCCESS = "success"


# ***************************
# Recipe Data Schema
# ***************************
class RecipeOverview(BaseModel):
    id: Optional[int] = None
    title: str
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
    equipment: Optional[List[str]] = None


# ***************************
# Agent Data Schema
# ***************************
class AgentState(BaseModel):
    # Core messaging
    messages: Annotated[Sequence[BaseMessage], add_messages] = Field(
        default_factory=list
    )

    # Recipe extraction state
    video_url: Optional[str] = None
    extracted_recipe: Optional[Recipe] = None
    extraction_status: STATUS = Field(default=STATUS.PENDING)

    # Error handling
    error_message: Optional[str] = None
    retry_count: int = Field(default=0, ge=0)
    max_retries: int = Field(default=2, ge=0, le=5)

    # Processing metadata
    number_of_steps: int = Field(default=0, ge=0)
    processing_time: Optional[float] = 0


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
    version: str = Field(default=APP_VERSION, description="API version")


# ***************************
# Database API Models
# ***************************
class SaveRecipeRequest(BaseModel):
    recipe: Recipe = Field(..., description="Recipe data to save")
    source_url: Optional[HttpUrl] = Field(None, description="Original video URL")


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


class UpdateRecipeResponse(BaseModel):
    success: bool = Field(..., description="Whether recipe was updated successfully")
    recipe_id: int = Field(..., description="ID of the updated recipe")
    message: str = Field(..., description="Update status message")
