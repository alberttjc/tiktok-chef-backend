import time
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Import local modules
from src.config import APP_VERSION
from src.logger import get_logger
from src.agent import recipe_agent
from src.database import init_db, get_supabase
from src.crud import (
    create_recipe,
    get_recipes,
    get_recipe_by_id,
    get_recipe_by_source_url,
    delete_recipe,
    update_recipe,
    recipe_to_schema,
)
from src.utils import extract_tiktok_username
from src.schema import (
    RecipeExtractionRequest,
    RecipeExtractionResponse,
    ErrorResponse,
    HealthResponse,
    SaveRecipeRequest,
    SaveRecipeResponse,
    GetRecipesResponse,
    GetRecipeResponse,
    DeleteRecipeResponse,
    UpdateRecipeRequest,
    UpdateRecipeResponse,
)


# Initialize logger
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    logger.info("Starting TiktokChef API...")
    # Initialize database
    init_db()
    yield
    logger.info("Shutting down TiktokChef API...")


# Create FastAPI app
app = FastAPI(
    title="TiktokChef API",
    description="Extract structured recipes from cooking videos using AI",
    version=APP_VERSION,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    """Serve the index.html file"""
    return FileResponse("static/index.html")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse()


@app.post("/extract", response_model=RecipeExtractionResponse)
async def extract_recipe(request: RecipeExtractionRequest) -> RecipeExtractionResponse:
    """
    Extract recipe from a cooking video URL

    - **video_url**: URL of the cooking video to analyze
    - **max_retries**: Maximum number of retry attempts (0-5)
    """
    start_time = time.time()

    try:
        # Check if recipe already exists in database (caching)
        supabase = get_supabase()
        existing_recipe = get_recipe_by_source_url(supabase, str(request.video_url))

        if existing_recipe:
            processing_time = time.time() - start_time
            logger.info(f"Returning cached recipe for URL: {request.video_url}")

            return RecipeExtractionResponse(
                success=True,
                recipe=recipe_to_schema(existing_recipe),
                metadata={
                    "steps": 0,
                    "cached": True,
                    "database_id": existing_recipe["id"],
                },
                processing_time=processing_time,
            )

        # Extract recipe using the agent (new URL)
        logger.info(f"Extracting new recipe for URL: {request.video_url}")
        result = recipe_agent(
            video_url=str(request.video_url),
            max_retries=request.max_retries,
        )

        processing_time = time.time() - start_time
        metadata = result["metadata"]
        metadata.update({"cached": False, "database_id": None})

        # Extract creator username from TikTok URL
        creator_username = extract_tiktok_username(str(request.video_url))
        if creator_username and result["recipe"]:
            result["recipe"].recipe_overview.creator_username = creator_username
            result["recipe"].recipe_overview.source_url = str(request.video_url)

        return RecipeExtractionResponse(
            success=result["success"],
            recipe=result["recipe"],
            metadata=metadata,
            processing_time=processing_time,
        )

    except Exception as e:
        processing_time = time.time() - start_time

        # Log the error
        logger.error(f"Error extracting recipe for URL {request.video_url}: {str(e)}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error="Failed to extract recipe",
                details={
                    "processing_time": processing_time,
                    "video_url": str(request.video_url),
                    "original_error": str(e),
                },
            ).model_dump(),
        )


# ***************************
# Database API Endpoints
# ***************************
@app.post("/recipes", response_model=SaveRecipeResponse)
async def save_recipe(request: SaveRecipeRequest):
    """
    Save a recipe to the database

    - **recipe**: Recipe data to save
    - **source_url**: Original video URL (optional)
    - **creator_username**: TikTok creator username (optional)
    """
    try:
        supabase = get_supabase()
        db_recipe = create_recipe(supabase=supabase,recipe_data=request.recipe)

        return SaveRecipeResponse(
            success=True,
            recipe_id=db_recipe["id"],
            message=f"Recipe '{request.recipe.recipe_overview.title}' saved successfully",
        )

    except Exception as e:
        logger.error(f"Error saving recipe: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error="Failed to save recipe", details={"original_error": str(e)}
            ).model_dump(),
        )


@app.get("/recipes", response_model=GetRecipesResponse)
async def get_all_recipes(skip: int = 0, limit: int = 100):
    """
    Get all recipes from the database

    - **skip**: Number of recipes to skip (pagination)
    - **limit**: Maximum number of recipes to return
    """
    try:
        supabase = get_supabase()
        db_recipes = get_recipes(supabase=supabase, skip=skip, limit=limit)

        # Convert to schemas
        recipes = [recipe_to_schema(db_recipe) for db_recipe in db_recipes]

        return GetRecipesResponse(success=True, recipes=recipes, count=len(recipes))

    except Exception as e:
        logger.error(f"Error getting recipes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error="Failed to get recipes", details={"original_error": str(e)}
            ).model_dump(),
        )


@app.get("/recipes/{recipe_id}", response_model=GetRecipeResponse)
async def get_recipe(recipe_id: int):
    """
    Get a single recipe by ID

    - **recipe_id**: ID of the recipe to retrieve
    """
    try:
        supabase = get_supabase()
        db_recipe = get_recipe_by_id(supabase=supabase, recipe_id=recipe_id)

        if not db_recipe:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse(
                    error="Recipe not found", details={"recipe_id": recipe_id}
                ).model_dump(),
            )

        recipe = recipe_to_schema(db_recipe)

        return GetRecipeResponse(success=True, recipe=recipe)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting recipe {recipe_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error="Failed to get recipe", details={"original_error": str(e)}
            ).model_dump(),
        )


@app.delete("/recipes/{recipe_id}", response_model=DeleteRecipeResponse)
async def delete_recipe_endpoint(recipe_id: int):
    """
    Delete a recipe by ID

    - **recipe_id**: ID of the recipe to delete
    """
    try:
        supabase = get_supabase()
        success = delete_recipe(supabase=supabase, recipe_id=recipe_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse(
                    error="Recipe not found", details={"recipe_id": recipe_id}
                ).model_dump(),
            )

        return DeleteRecipeResponse(
            success=True, message=f"Recipe {recipe_id} deleted successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting recipe {recipe_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error="Failed to delete recipe", details={"original_error": str(e)}
            ).model_dump(),
        )


@app.put("/recipes/{recipe_id}", response_model=UpdateRecipeResponse)
async def update_recipe_endpoint(recipe_id: int, request: UpdateRecipeRequest):
    """
    Update a recipe by ID

    - **recipe_id**: ID of the recipe to update
    - **recipe**: Updated recipe data
    - **source_url**: Updated original video URL (optional)
    """
    try:
        supabase = get_supabase()
        db_recipe = update_recipe(
            supabase=supabase, recipe_id=recipe_id, recipe_data=request.recipe
        )

        if not db_recipe:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse(
                    error="Recipe not found", details={"recipe_id": recipe_id}
                ).model_dump(),
            )

        # Update source URL and creator username if provided
        if request.source_url or request.creator_username:
            update_data = {}
            if request.source_url:
                update_data["source_url"] = str(request.source_url)
            if request.creator_username:
                update_data["creator_username"] = request.creator_username

            supabase.table("recipes").update(update_data).eq("id", recipe_id).execute()

        return UpdateRecipeResponse(
            success=True,
            recipe_id=int(db_recipe["id"]),
            message=f"Recipe '{request.recipe.recipe_overview.title}' updated successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating recipe {recipe_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error="Failed to update recipe", details={"original_error": str(e)}
            ).model_dump(),
        )


if __name__ == "__main__":
    # demo_url = "https://www.tiktok.com/@khanhong/video/7557275818255273234"
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_config=None)
