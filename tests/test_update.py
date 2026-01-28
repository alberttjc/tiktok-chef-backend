#!/usr/bin/env python3
"""
Test script for the new recipe update functionality
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from main import app


def test_update_functionality():
    """Test the recipe update functionality"""
    client = TestClient(app)

    print("Testing Recipe Update Functionality...")
    print("=" * 50)

    # 1. Get existing recipes
    print("1. Getting existing recipes...")
    response = client.get("/recipes")
    if response.status_code != 200:
        print(f"   ❌ Failed to get recipes: {response.status_code}")
        return

    recipes = response.json()["recipes"]
    if not recipes:
        print("   ❌ No recipes found to test with")
        return

    recipe_id = recipes[0]["id"]
    original_title = recipes[0]["recipe_overview"]["title"]
    print(f"   ✅ Found recipe {recipe_id}: {original_title}")

    # 2. Test update
    print(f"\n2. Updating recipe {recipe_id}...")
    update_data = {
        "recipe": {
            "recipe_overview": {
                "title": f"Updated {original_title}",
                "servings": 6,
                "prep_time": "20 mins",
                "cook_time": "25 mins",
                "difficulty": "Intermediate",
                "cuisine_type": "Test Cuisine",
            },
            "ingredients": [
                {"item": "Test Ingredient 1", "amount": "2", "unit": "cups"},
                {"item": "Test Ingredient 2", "amount": "1", "unit": "tablespoon"},
            ],
            "instructions": ["Test instruction 1", "Test instruction 2"],
        },
        "source_url": "https://test-update-example.com/video",
    }

    update_response = client.put(f"/recipes/{recipe_id}", json=update_data)
    print(f"   Update status: {update_response.status_code}")

    if update_response.status_code == 200:
        update_result = update_response.json()
        print(f"   ✅ Update successful: {update_result['message']}")

        # 3. Verify the update
        print(f"\n3. Verifying the update...")
        verify_response = client.get(f"/recipes/{recipe_id}")
        if verify_response.status_code == 200:
            updated_recipe = verify_response.json()["recipe"]
            updated_title = updated_recipe["recipe_overview"]["title"]

            if updated_title == f"Updated {original_title}":
                print(f"   ✅ Title updated correctly: {updated_title}")
            else:
                print(f"   ❌ Title not updated: {updated_title}")

            if len(updated_recipe["ingredients"]) == 2:
                print(
                    f"   ✅ Ingredients updated correctly: {len(updated_recipe['ingredients'])} items"
                )
            else:
                print(
                    f"   ❌ Ingredients not updated: {len(updated_recipe['ingredients'])} items"
                )

            if len(updated_recipe["instructions"]) == 2:
                print(
                    f"   ✅ Instructions updated correctly: {len(updated_recipe['instructions'])} items"
                )
            else:
                print(
                    f"   ❌ Instructions not updated: {len(updated_recipe['instructions'])} items"
                )
        else:
            print(f"   ❌ Failed to verify update: {verify_response.status_code}")
    else:
        print(f"   ❌ Update failed: {update_response.json()}")

    # 4. Test update with non-existent recipe
    print(f"\n4. Testing update with non-existent recipe...")
    fake_update_response = client.put("/recipes/99999", json=update_data)
    if fake_update_response.status_code == 404:
        print(f"   ✅ Correctly returns 404 for non-existent recipe")
    else:
        print(f"   ❌ Expected 404, got {fake_update_response.status_code}")

    print("\n✅ Update functionality tests completed!")


if __name__ == "__main__":
    test_update_functionality()
