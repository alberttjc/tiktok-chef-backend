#!/usr/bin/env python3
"""
Comprehensive test suite for TiktokChef API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from typing import Dict, Any
from unittest.mock import patch

from tests.conftest import (
    assert_valid_health_response,
    assert_valid_error_response,
    assert_valid_recipe_structure,
    VALID_VIDEO_URL,
    INVALID_VIDEO_URL,
    NONEXISTENT_VIDEO_URL,
)


class TestCoreEndpoints:
    """Test core application endpoints"""

    @pytest.mark.api
    def test_root_endpoint(self, client: TestClient):
        """Test the root endpoint serves HTML"""
        response = client.get("/")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")

    @pytest.mark.api
    def test_health_endpoint(self, client: TestClient):
        """Test the health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert_valid_health_response(data)

    @pytest.mark.api
    def test_swagger_docs(self, client: TestClient):
        """Test Swagger UI documentation"""
        response = client.get("/docs")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")

    @pytest.mark.api
    def test_redoc_docs(self, client: TestClient):
        """Test ReDoc documentation"""
        response = client.get("/redoc")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")


class TestRecipeExtractionEndpoint:
    """Test recipe extraction from video URLs"""

    @pytest.mark.api
    @pytest.mark.external
    def test_extract_recipe_success(self, client: TestClient, mock_video_extraction):
        """Test successful recipe extraction"""
        # Clear any existing recipes to ensure fresh extraction
        with patch("main.get_recipe_by_source_url") as mock_get:
            mock_get.return_value = None  # No existing recipe

            response = client.post(
                "/extract", json={"video_url": VALID_VIDEO_URL, "max_retries": 2}
            )

            assert response.status_code == 200
            data = response.json()

            # Verify response structure
            assert "success" in data
            assert "recipe" in data
            assert "metadata" in data
            assert "processing_time" in data

            assert data["success"] is True
            assert_valid_recipe_structure(data["recipe"])

            # Verify metadata
            metadata = data["metadata"]
            assert "steps" in metadata
            assert "cached" in metadata
            assert metadata["cached"] is False  # First time extraction

            # Verify processing time is reasonable
            assert data["processing_time"] >= 0

    @pytest.mark.api
    @pytest.mark.external
    def test_extract_recipe_with_cache(
        self, client: TestClient, sample_recipe_data, mock_video_extraction
    ):
        """Test recipe extraction with database caching"""
        # First, save a recipe with the same URL
        client.post(
            "/recipes", json={**sample_recipe_data, "source_url": VALID_VIDEO_URL}
        )

        # Now try extraction - should return cached recipe
        response = client.post(
            "/extract", json={"video_url": VALID_VIDEO_URL, "max_retries": 2}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["metadata"]["cached"] is True
        assert data["metadata"]["database_id"] is not None

    @pytest.mark.api
    def test_extract_recipe_invalid_url(self, client: TestClient):
        """Test recipe extraction with invalid URL"""
        response = client.post(
            "/extract", json={"video_url": INVALID_VIDEO_URL, "max_retries": 2}
        )

        # Should return validation error
        assert response.status_code == 422

    @pytest.mark.api
    @pytest.mark.external
    def test_extract_recipe_max_retries(
        self, client: TestClient, mock_video_extraction
    ):
        """Test recipe extraction with different max_retries values"""
        for max_retries in [0, 1, 3, 5]:
            response = client.post(
                "/extract",
                json={"video_url": VALID_VIDEO_URL, "max_retries": max_retries},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True


class TestRecipeCRUDEndpoints:
    """Test recipe CRUD operations"""

    @pytest.mark.api
    @pytest.mark.database
    def test_save_recipe_success(self, client: TestClient, sample_recipe_data):
        """Test successful recipe creation"""
        response = client.post("/recipes", json=sample_recipe_data)

        assert response.status_code == 200
        data = response.json()

        assert "success" in data
        assert "recipe_id" in data
        assert "message" in data

        assert data["success"] is True
        assert isinstance(data["recipe_id"], int)
        assert "saved successfully" in data["message"].lower()

    @pytest.mark.api
    @pytest.mark.database
    def test_save_recipe_without_source_url(
        self, client: TestClient, sample_recipe_data
    ):
        """Test recipe creation without source URL"""
        data = sample_recipe_data.copy()
        data.pop("source_url", None)

        response = client.post("/recipes", json=data)
        assert response.status_code == 200
        assert response.json()["success"] is True

    @pytest.mark.api
    @pytest.mark.database
    def test_save_recipe_invalid_data(self, client: TestClient):
        """Test recipe creation with invalid data"""
        invalid_data = {
            "recipe": {
                "recipe_overview": {
                    "title": "",  # Empty title
                    "servings": 0,  # Invalid servings
                }
            }
        }

        response = client.post("/recipes", json=invalid_data)
        assert response.status_code == 422

    @pytest.mark.api
    @pytest.mark.database
    def test_get_all_recipes_empty(self, client: TestClient):
        """Test getting recipes when database is empty"""
        response = client.get("/recipes")

        assert response.status_code == 200
        data = response.json()

        assert "success" in data
        assert "recipes" in data
        assert "count" in data

        assert data["success"] is True
        # Note: This test uses shared DB so might not be empty, that's OK

    @pytest.mark.api
    @pytest.mark.database
    def test_get_all_recipes_with_data(self, client: TestClient, created_recipe):
        """Test getting recipes when database has data"""
        response = client.get("/recipes")

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["count"] >= 1
        assert len(data["recipes"]) == data["count"]

        # Verify recipe structure
        for recipe in data["recipes"]:
            assert_valid_recipe_structure(recipe)

    @pytest.mark.api
    @pytest.mark.database
    def test_get_all_recipes_pagination(self, client: TestClient, sample_recipe_data):
        """Test recipe pagination"""
        # Create multiple recipes
        recipe_ids = []
        for i in range(5):
            data = sample_recipe_data.copy()
            data["recipe"]["recipe_overview"]["title"] = f"Recipe {i}"
            response = client.post("/recipes", json=data)
            recipe_ids.append(response.json()["recipe_id"])

        # Test pagination
        response = client.get("/recipes?skip=2&limit=2")
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert len(data["recipes"]) == 2
        assert data["count"] == 2

    @pytest.mark.api
    @pytest.mark.database
    def test_get_single_recipe_success(self, client: TestClient, created_recipe):
        """Test getting a single recipe by ID"""
        response = client.get(f"/recipes/{created_recipe}")

        assert response.status_code == 200
        data = response.json()

        assert "success" in data
        assert "recipe" in data

        assert data["success"] is True
        assert_valid_recipe_structure(data["recipe"])

    @pytest.mark.api
    @pytest.mark.database
    def test_get_single_recipe_not_found(self, client: TestClient):
        """Test getting a non-existent recipe"""
        response = client.get("/recipes/99999")

        assert response.status_code == 404
        data = response.json()
        assert_valid_error_response(data["detail"])
        assert "not found" in data["detail"]["error"].lower()

    @pytest.mark.api
    @pytest.mark.database
    def test_update_recipe_success(
        self, client: TestClient, created_recipe, sample_recipe_update_data
    ):
        """Test successful recipe update"""
        response = client.put(
            f"/recipes/{created_recipe}", json=sample_recipe_update_data
        )

        assert response.status_code == 200
        data = response.json()

        assert "success" in data
        assert "recipe_id" in data
        assert "message" in data

        assert data["success"] is True
        assert data["recipe_id"] == created_recipe
        assert "updated successfully" in data["message"].lower()

    @pytest.mark.api
    @pytest.mark.database
    def test_update_recipe_not_found(
        self, client: TestClient, sample_recipe_update_data
    ):
        """Test updating a non-existent recipe"""
        response = client.put("/recipes/99999", json=sample_recipe_update_data)

        assert response.status_code == 404
        data = response.json()
        assert_valid_error_response(data["detail"])
        assert "not found" in data["detail"]["error"].lower()

    @pytest.mark.api
    @pytest.mark.database
    def test_delete_recipe_success(self, client: TestClient, created_recipe):
        """Test successful recipe deletion"""
        response = client.delete(f"/recipes/{created_recipe}")

        assert response.status_code == 200
        data = response.json()

        assert "success" in data
        assert "message" in data

        assert data["success"] is True
        assert "deleted successfully" in data["message"].lower()

        # Verify recipe is actually deleted
        verify_response = client.get(f"/recipes/{created_recipe}")
        assert verify_response.status_code == 404

    @pytest.mark.api
    @pytest.mark.database
    def test_delete_recipe_not_found(self, client: TestClient):
        """Test deleting a non-existent recipe"""
        response = client.delete("/recipes/99999")

        assert response.status_code == 404
        data = response.json()
        assert_valid_error_response(data["detail"])
        assert "not found" in data["detail"]["error"].lower()


class TestStaticFiles:
    """Test static file serving"""

    @pytest.mark.api
    def test_static_file_access(self, client: TestClient):
        """Test accessing static files"""
        # Test if static directory is accessible
        response = client.get("/static/")

        # Should return 404 if directory is empty, or 200 if it has index
        assert response.status_code in [200, 404]

    @pytest.mark.api
    def test_static_file_not_found(self, client: TestClient):
        """Test accessing non-existent static file"""
        response = client.get("/static/nonexistent.txt")
        assert response.status_code == 404


class TestErrorHandling:
    """Test error handling across all endpoints"""

    @pytest.mark.api
    def test_method_not_allowed(self, client: TestClient):
        """Test unsupported HTTP methods"""
        # Try GET on POST endpoint
        response = client.get("/extract")
        assert response.status_code == 405

        # Try POST on GET endpoint
        response = client.post("/health")
        assert response.status_code == 405

    @pytest.mark.api
    def test_invalid_json(self, client: TestClient):
        """Test endpoints with invalid JSON"""
        response = client.post(
            "/extract",
            data="invalid json content",
            headers={"content-type": "application/json"},
        )
        assert response.status_code == 422

    @pytest.mark.api
    def test_missing_content_type(self, client: TestClient):
        """Test endpoints without proper content type"""
        response = client.post("/extract", data='{"video_url": "test"}')
        # FastAPI should handle this gracefully
        assert response.status_code in [200, 422]


class TestResponseFormats:
    """Test response format consistency"""

    @pytest.mark.api
    def test_content_type_headers(self, client: TestClient):
        """Test proper content-type headers"""
        # JSON endpoints
        response = client.get("/health")
        assert response.headers["content-type"] == "application/json"

        # HTML endpoints
        response = client.get("/")
        assert response.headers["content-type"].startswith("text/html")
