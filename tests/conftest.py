#!/usr/bin/env python3
"""
Pytest configuration and shared fixtures for TiktokChef API testing
"""

import os
import sys
from typing import Generator, Dict, Any
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from src.database import get_supabase
from src.schema import Recipe, RecipeOverview, Ingredient as SchemaIngredient


# Mock Supabase client for testing
class MockSupabaseTable:
    def __init__(self, table_name: str, data_store: Dict[str, list]):
        self.table_name = table_name
        self.data_store = data_store
        self.query_filters = {}
        self.query_select = "*"
        self.query_order = None
        self.query_range = None

    def select(self, columns: str, count: str = None):
        self.query_select = columns
        return self

    def insert(self, data):
        # Handle both single dict and list of dicts
        if isinstance(data, dict):
            data = [data]

        for item in data:
            # Generate ID if not present
            if "id" not in item:
                existing_ids = [row.get("id", 0) for row in self.data_store[self.table_name]]
                item["id"] = max(existing_ids) + 1 if existing_ids else 1

            self.data_store[self.table_name].append(item)

        return self

    def update(self, data):
        self._update_data = data
        return self

    def delete(self):
        self._delete_mode = True
        return self

    def eq(self, column: str, value):
        self.query_filters[column] = value
        return self

    def order(self, column: str, desc: bool = False):
        self.query_order = (column, desc)
        return self

    def range(self, start: int, end: int):
        self.query_range = (start, end)
        return self

    def limit(self, count: int):
        self.query_limit = count
        return self

    def execute(self):
        # Handle delete
        if hasattr(self, "_delete_mode"):
            filtered_data = []
            deleted_data = []
            for row in self.data_store[self.table_name]:
                if all(row.get(k) == v for k, v in self.query_filters.items()):
                    deleted_data.append(row)
                else:
                    filtered_data.append(row)
            self.data_store[self.table_name] = filtered_data
            return type("Response", (), {"data": deleted_data})()

        # Handle update
        if hasattr(self, "_update_data"):
            for row in self.data_store[self.table_name]:
                if all(row.get(k) == v for k, v in self.query_filters.items()):
                    row.update(self._update_data)
            return type("Response", (), {"data": []})()

        # Handle select
        result = list(self.data_store[self.table_name])

        # Apply filters
        if self.query_filters:
            result = [
                row
                for row in result
                if all(row.get(k) == v for k, v in self.query_filters.items())
            ]

        # Join related data if select includes nested tables
        if "*" in self.query_select and "(" in self.query_select:
            for row in result:
                # Add ingredients
                if "ingredients" in self.query_select:
                    row["ingredients"] = [
                        ing
                        for ing in self.data_store.get("ingredients", [])
                        if ing.get("recipe_id") == row.get("id")
                    ]
                # Add instructions
                if "instructions" in self.query_select:
                    row["instructions"] = [
                        inst
                        for inst in self.data_store.get("instructions", [])
                        if inst.get("recipe_id") == row.get("id")
                    ]

        # Apply ordering
        if self.query_order:
            column, desc = self.query_order
            result = sorted(result, key=lambda x: x.get(column, ""), reverse=desc)

        # Apply range
        if self.query_range:
            start, end = self.query_range
            result = result[start : end + 1]

        return type("Response", (), {"data": result})()


class MockSupabaseClient:
    def __init__(self):
        self.data_store = {"recipes": [], "ingredients": [], "instructions": []}

    def table(self, table_name: str):
        return MockSupabaseTable(table_name, self.data_store)


@pytest.fixture
def mock_supabase():
    """Create a mock Supabase client for testing"""
    return MockSupabaseClient()


@pytest.fixture
def supabase_client(mock_supabase):
    """
    Override get_supabase dependency with mock client
    """

    def override_get_supabase():
        return mock_supabase

    app.dependency_overrides[get_supabase] = override_get_supabase

    yield mock_supabase

    # Cleanup data after each test
    mock_supabase.data_store["instructions"] = []
    mock_supabase.data_store["ingredients"] = []
    mock_supabase.data_store["recipes"] = []

    # Clear overrides
    app.dependency_overrides.clear()


@pytest.fixture
def client(supabase_client) -> Generator:
    """
    Create a test client with the mock Supabase database
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
    def test_database_initialization(self, supabase_client):
        """Test that mock database works properly"""
        # Insert a recipe
        response = (
            supabase_client.table("recipes")
            .insert(
                {
                    "title": "Test Recipe",
                    "base_servings": 2,
                    "prep_time": "10 mins",
                    "cook_time": "20 mins",
                }
            )
            .execute()
        )

        # Verify it was saved
        retrieved = (
            supabase_client.table("recipes").select("*").eq("title", "Test Recipe").execute()
        )
        assert len(retrieved.data) > 0
        assert retrieved.data[0]["title"] == "Test Recipe"


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
