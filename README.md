# TiktokChef API

A FastAPI application that extracts structured recipes from cooking videos using AI and LangGraph.

## Features

- 🎥 Extract recipes from cooking video URLs
- 🤖 AI-powered recipe analysis using Google Gemini
- 📊 Structured recipe data with ingredients and instructions
- ✅ Recipe validation and error handling
- 🚀 RESTful API with OpenAPI documentation

## System Architecture

```mermaid
graph LR
    START --> video_analysis
    video_analysis --> END
```

## Getting Started

### Prerequisites

- Python 3.12+
- Google Gemini API key

### 1. Install `uv` (Package Manager)

**macOS/Linux:**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows:**

```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Installation

```bash
# Install dependencies
uv sync

# Install dependencies with testing
uv sync --extra test
```

### Setup Environment

Create a `.env` file with your API keys:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### Run the API

```bash
# Start the development server
uv run python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or with python directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Health Check

- `GET /` - Basic health status
- `GET /health` - Detailed health information

### TiktokChef API

- `POST /extract` - Extract recipe from video URL

### Database API

- `POST /recipes` - Save a recipe to the database
- `GET /recipes` - Get all recipes (with pagination)
- `GET /recipes/{recipe_id}` - Get a single recipe by ID
- `PUT /recipes/{recipe_id}` - Update a recipe by ID
- `DELETE /recipes/{recipe_id}` - Delete a recipe by ID

### Example Usage

```bash
# Extract recipe from a video
curl -X POST "http://localhost:8000/extract" \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "https://www.tiktok.com/@khanhong/video/7557275818255273234",
    "max_retries": 2
  }'

# Try the demo endpoint
curl "http://localhost:8000/extract/demo"
```

### Database Usage Examples

```bash
# Save a recipe
curl -X POST "http://localhost:8000/recipes" \
  -H "Content-Type: application/json" \
  -d '{
    "recipe": {
      "recipe_overview": {
        "title": "Simple Pasta",
        "servings": 4,
        "prep_time": "10 mins",
        "cook_time": "15 mins",
        "difficulty": "Easy",
        "cuisine_type": "Italian"
      },
      "ingredients": [
        {"item": "Pasta", "amount": "200", "unit": "g"},
        {"item": "Tomato Sauce", "amount": "1", "unit": "cup"}
      ],
      "instructions": [
        "Boil water and cook pasta",
        "Heat tomato sauce and combine with pasta"
      ]
    },
    "source_url": "https://example.com/video"
  }'

# Get all recipes
curl "http://localhost:8000/recipes"

# Get a specific recipe
curl "http://localhost:8000/recipes/1"

# Delete a recipe
curl -X DELETE "http://localhost:8000/recipes/1"

# Update a recipe
curl -X PUT "http://localhost:8000/recipes/1" \
  -H "Content-Type: application/json" \
  -d '{
    "recipe": {
      "recipe_overview": {
        "title": "Updated Recipe Title",
        "servings": 6,
        "prep_time": "20 mins",
        "cook_time": "25 mins",
        "difficulty": "Intermediate",
        "cuisine_type": "Updated Cuisine"
      },
      "ingredients": [
        {"item": "Updated Ingredient", "amount": "2", "unit": "cups"}
      ],
      "instructions": [
        "Updated instruction 1",
        "Updated instruction 2"
      ]
    },
    "source_url": "https://updated-example.com/video"
  }'
```

### Response Format

```json
{
  "success": true,
  "recipe": {
    "recipe_overview": {
      "title": "Recipe Title",
      "prep_time": "15 mins",
      "cook_time": "30 mins",
      "servings": 4,
      "difficulty": "Easy",
      "cuisine_type": "Italian"
    },
    "ingredients": [
      {
        "item": "Pasta",
        "amount": "200",
        "unit": "g",
        "notes": null
      }
    ],
    "instructions": [
      "Boil water in a large pot",
      "Add pasta and cook according to package directions"
    ]
  },
  "metadata": {
    "steps": 2,
    "is_valid": true,
    "errors": null
  },
  "processing_time": 3.45
}
```

## Documentation

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

## Development

### Running Tests

```bash
# Test the API endpoints
uv run python tests/test_api.py
```

### Project Structure

```
recipe-app/
├── main.py              # FastAPI application
├── src/
│   ├── agent.py        # TiktokChef agent
│   ├── config.py       # Configuration and prompts
│   ├── graph.py        # LangGraph workflow
│   ├── schema.py       # Pydantic models
│   └── tools.py        # AI tools and functions
├── tests/
│   └── test_api.py     # API test script
└── README.md           # This file
```

## 🐳 Docker Workflow

For production or containerized environments:

| Action    | Command                                     |
| --------- | ------------------------------------------- |
| **Build** | `docker build -t tiktokchef .`              |
| **Run**   | `docker run -p 8000:8000 tiktokchef`        |
| **Test**  | `curl http://localhost:8000`                |
| **Clean** | `docker stop <id> && docker rmi tiktokchef` |
