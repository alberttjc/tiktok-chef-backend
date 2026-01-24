import time
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from src.agent import recipe_agent
from src.schema import (
    RecipeExtractionRequest,
    RecipeExtractionResponse,
    ErrorResponse,
    HealthResponse,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    print("Starting Recipe Extraction API...")
    yield
    print("Shutting down Recipe Extraction API...")


# Create FastAPI app
app = FastAPI(
    title="Recipe Extraction API",
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


@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint with API health status"""
    return HealthResponse()


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
        
        # Log the error (in production, you'd use proper logging)
        print(f"Error extracting recipe: {str(e)}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error="Failed to extract recipe",
                details={
                    "processing_time": processing_time,
                    "video_url": str(request.video_url),
                    "original_error": str(e),
                }
            ).model_dump()
        )


@app.get("/extract/demo")
async def demo_extraction() -> RecipeExtractionResponse:
    """
    Demo endpoint with a sample video URL
    """
    demo_url = "https://www.tiktok.com/@khanhong/video/7557275818255273234"
    
    try:
        result = recipe_agent(video_url=demo_url, max_retries=2)
        
        return RecipeExtractionResponse(
            success=result["success"],
            recipe=result["recipe"],
            metadata=result["metadata"],
            processing_time=None,
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error="Demo extraction failed",
                details={"original_error": str(e)}
            ).model_dump()
        )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
