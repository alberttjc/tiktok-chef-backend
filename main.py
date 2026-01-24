import time
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Import local modules
from src.logger import get_logger
from src.agent import recipe_agent
from src.schema import (
    RecipeExtractionRequest,
    RecipeExtractionResponse,
    ErrorResponse,
    HealthResponse,
)


# Initialize logger
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    logger.info("Starting TiktokChef API...")
    yield
    logger.info("Shutting down TiktokChef API...")


# Create FastAPI app
app = FastAPI(
    title="TiktokChef API",
    description="Extract structured recipes from cooking videos using AI",
    version="0.1.0",
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
        # Extract recipe using the agent
        result = recipe_agent(
            video_url=str(request.video_url),
            max_retries=request.max_retries,
        )

        processing_time = time.time() - start_time

        return RecipeExtractionResponse(
            success=result["success"],
            recipe=result["recipe"],
            metadata=result["metadata"],
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


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_config=None)
