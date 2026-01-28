#!/usr/bin/env python3
"""
Pytest configuration and shared fixtures for TiktokChef API testing
"""

import os
import sys
import tempfile
from typing import Generator, Dict, Any
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from src.database import Base, get_db
from src.models import Recipe, Ingredient, Instruction
from src.schema import Recipe, RecipeOverview, Ingredient as SchemaIngredient


@pytest.fixture(scope="session")
def test_db() -> Generator:
    """
    Create a temporary database for testing
    """
    # Create temporary file for test database
    db_fd, db_path = tempfile.mkstemp()

    # Create test database engine
    test_engine = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}
    )

    # Create all tables
    Base.metadata.create_all(bind=test_engine)

    # Create session factory
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=test_engine
    )

    # Override the database dependency
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    yield TestingSessionLocal

    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def db_session(test_db):
    """
    Get a database session for testing
    """
    db = test_db()
    try:
        yield db
    finally:
        # Clean up database after each test
        db.query(Instruction).delete()
        db.query(Ingredient).delete()
        # Equipment is not stored in database (schema-only for MVP)
        db.query(Recipe).delete()
        db.commit()
        db.close()


@pytest.fixture
def client(test_db) -> Generator:
    """
    Create a test client with the test database
    """
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def sample_recipe_data() -> Dict[str, Any]:
    """
    Sample recipe data for testing
    """
    return {
        "recipe": {
            "recipe_overview": {
                "title": "Test Recipe",
                "prep_time": "15 mins",
                "cook_time": "30 mins",
                "servings": 4,
                "difficulty": "Easy",
                "cuisine_type": "Italian",
            },
            "ingredients": [
                {
                    "item": "Pasta",
                    "amount": "200",
                    "unit": "grams",
                    "notes": "Any type",
                },
                {"item": "Tomato Sauce", "amount": "1", "unit": "cup"},
                {"item": "Cheese", "amount": "100", "unit": "grams", "notes": "Grated"},
            ],
            "instructions": [
                "Boil water for pasta",
                "Cook pasta according to package directions",
                "Heat tomato sauce in a pan",
                "Combine pasta with sauce",
                "Top with cheese and serve",
            ],
            "equipment": ["Pot", "Pan", "Strainer"],
        },
        "source_url": "https://example.com/video/123",
    }


@pytest.fixture
def sample_recipe_update_data() -> Dict[str, Any]:
    """
    Sample recipe update data for testing
    """
    return {
        "recipe": {
            "recipe_overview": {
                "title": "Updated Test Recipe",
                "prep_time": "20 mins",
                "cook_time": "35 mins",
                "servings": 6,
                "difficulty": "Intermediate",
                "cuisine_type": "Mexican",
            },
            "ingredients": [
                {"item": "Tortillas", "amount": "4", "unit": "pieces"},
                {"item": "Chicken", "amount": "500", "unit": "grams"},
                {"item": "Cheese", "amount": "200", "unit": "grams"},
            ],
            "instructions": [
                "Cook chicken thoroughly",
                "Warm tortillas",
                "Add chicken to tortillas",
                "Top with cheese",
                "Roll into burritos",
            ],
            "equipment": ["Skillet", "Cutting board"],
        },
        "source_url": "https://example-updated.com/video/456",
    }


@pytest.fixture
def created_recipe(client, sample_recipe_data):
    """
    Create a recipe in the database for testing and return its ID
    """
    response = client.post("/recipes", json=sample_recipe_data)
    assert response.status_code == 200
    return response.json()["recipe_id"]


@pytest.fixture
def mock_video_extraction():
    """
    Mock the video extraction process to avoid calling external APIs
    """
    mock_result = {
        "success": True,
        "recipe": {
            "recipe_overview": {
                "title": "Extracted Recipe",
                "prep_time": "10 mins",
                "cook_time": "20 mins",
                "servings": 2,
                "difficulty": "Easy",
                "cuisine_type": "Asian",
            },
            "ingredients": [
                {"item": "Rice", "amount": "1", "unit": "cup"},
                {"item": "Soy Sauce", "amount": "2", "unit": "tablespoons"},
            ],
            "instructions": ["Cook rice", "Add soy sauce", "Serve hot"],
            "equipment": ["Pot", "Stove"],
        },
        "metadata": {"steps": 3, "processing_time": 5.0},
    }

    with patch("main.recipe_agent") as mock_agent:
        mock_agent.return_value = mock_result
        yield mock_agent


@pytest.fixture
def invalid_video_extraction():
    """
    Mock failed video extraction
    """
    with patch("main.recipe_agent") as mock_agent:
        mock_agent.side_effect = Exception("Video processing failed")
        yield mock_agent


# Test URLs for different scenarios
VALID_VIDEO_URL = "https://www.tiktok.com/@user/video/1234567890"
INVALID_VIDEO_URL = "not-a-valid-url"
NONEXISTENT_VIDEO_URL = "https://www.tiktok.com/@nonexistent/video/9999999999"


class TestDatabaseSetup:
    """Test database setup and fixtures"""

    @pytest.mark.database
    def test_database_initialization(self, db_session):
        """Test that database tables are created properly"""
        # Check that we can create a recipe
        recipe = Recipe(
            title="Test Recipe",
            base_servings=2,
            prep_time="10 mins",
            cook_time="20 mins",
        )
        db_session.add(recipe)
        db_session.commit()

        # Verify it was saved
        retrieved = (
            db_session.query(Recipe).filter(Recipe.title == "Test Recipe").first()
        )
        assert retrieved is not None
        assert retrieved.title == "Test Recipe"


# Utility functions for testing
def assert_valid_health_response(response_data: Dict[str, Any]):
    """Assert that health response has expected format"""
    assert "status" in response_data
    assert "version" in response_data
    assert response_data["status"] == "healthy"


def assert_valid_error_response(response_data: Dict[str, Any]):
    """Assert that error response has expected format"""
    assert "error" in response_data
    assert isinstance(response_data["error"], str)


def assert_valid_recipe_structure(recipe_data: Dict[str, Any]):
    """Assert that recipe data has expected structure"""
    assert "recipe_overview" in recipe_data
    assert "ingredients" in recipe_data
    assert "instructions" in recipe_data

    overview = recipe_data["recipe_overview"]
    assert "title" in overview
    assert "servings" in overview
    assert isinstance(overview["servings"], int)

    assert isinstance(recipe_data["ingredients"], list)
    assert isinstance(recipe_data["instructions"], list)
