from typing import List, Optional, Dict, Any
from supabase import Client
from postgrest.exceptions import APIError
from src.schema import Recipe as RecipeSchema, Ingredient as IngredientSchema
from src.logger import get_logger

logger = get_logger(__name__)


def create_recipe(
    supabase: Client, recipe_data: RecipeSchema, source_url: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new recipe with ingredients and instructions"""
    logger.info(f"Creating recipe: {recipe_data.recipe_overview.title}")

    try:
        # Create recipe record
        recipe_dict = {
            "title": recipe_data.recipe_overview.title,
            "source_url": source_url,
            "base_servings": recipe_data.recipe_overview.servings,
            "prep_time": recipe_data.recipe_overview.prep_time,
            "cook_time": recipe_data.recipe_overview.cook_time,
            "difficulty": recipe_data.recipe_overview.difficulty,
            "cuisine_type": recipe_data.recipe_overview.cuisine_type,
        }

        # Insert recipe and get the new ID
        response = supabase.table("recipes").insert(recipe_dict).execute()
        recipe_id = response.data[0]["id"]

        logger.info(f"Recipe created with ID: {recipe_id}")

        # Prepare ingredients batch
        ingredients_batch = []
        for ingredient in recipe_data.ingredients:
            try:
                amount = float(ingredient.amount)
            except (ValueError, TypeError):
                amount = 0.0

            ingredients_batch.append({
                "recipe_id": recipe_id,
                "name": ingredient.item,
                "amount": amount,
                "unit": ingredient.unit,
                "original_text": f"{ingredient.amount} {ingredient.unit or ''} {ingredient.item}".strip(),
            })

        # Batch insert ingredients
        if ingredients_batch:
            supabase.table("ingredients").insert(ingredients_batch).execute()

        # Prepare instructions batch
        instructions_batch = []
        for i, instruction in enumerate(recipe_data.instructions, 1):
            instructions_batch.append({
                "recipe_id": recipe_id,
                "step_number": i,
                "instruction_text": instruction,
            })

        # Batch insert instructions
        if instructions_batch:
            supabase.table("instructions").insert(instructions_batch).execute()

        # Return complete recipe
        return get_recipe_by_id(supabase, recipe_id)

    except APIError as e:
        logger.error(f"Supabase API error creating recipe: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error creating recipe: {str(e)}")
        raise


def get_recipes(supabase: Client, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
    """Get all recipes with pagination"""
    try:
        response = (
            supabase.table("recipes")
            .select("*, ingredients(*), instructions(*)")
            .order("created_at", desc=True)
            .range(skip, skip + limit - 1)
            .execute()
        )
        return response.data
    except APIError as e:
        logger.error(f"Supabase API error getting recipes: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error getting recipes: {str(e)}")
        raise


def get_recipe_by_id(supabase: Client, recipe_id: int) -> Optional[Dict[str, Any]]:
    """Get a single recipe by ID"""
    try:
        response = (
            supabase.table("recipes")
            .select("*, ingredients(*), instructions(*)")
            .eq("id", recipe_id)
            .execute()
        )

        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except APIError as e:
        logger.error(f"Supabase API error getting recipe by ID: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error getting recipe by ID: {str(e)}")
        raise


def get_recipe_by_source_url(supabase: Client, source_url: str) -> Optional[Dict[str, Any]]:
    """Get a recipe by its source URL"""
    try:
        response = (
            supabase.table("recipes")
            .select("*, ingredients(*), instructions(*)")
            .eq("source_url", source_url)
            .execute()
        )

        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except APIError as e:
        logger.error(f"Supabase API error getting recipe by URL: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error getting recipe by URL: {str(e)}")
        raise


def delete_recipe(supabase: Client, recipe_id: int) -> bool:
    """Delete a recipe by ID"""
    try:
        response = supabase.table("recipes").delete().eq("id", recipe_id).execute()

        # Check if any rows were affected
        if response.data and len(response.data) > 0:
            logger.info(f"Recipe deleted: {recipe_id}")
            return True
        return False
    except APIError as e:
        logger.error(f"Supabase API error deleting recipe: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error deleting recipe: {str(e)}")
        raise


def update_recipe(
    supabase: Client, recipe_id: int, recipe_data: RecipeSchema
) -> Optional[Dict[str, Any]]:
    """Update an existing recipe with ingredients and instructions"""
    logger.info(f"Updating recipe ID: {recipe_id}")

    try:
        # Check if recipe exists
        existing_recipe = get_recipe_by_id(supabase, recipe_id)
        if not existing_recipe:
            return None

        # Update recipe fields
        recipe_dict = {
            "title": recipe_data.recipe_overview.title,
            "base_servings": recipe_data.recipe_overview.servings,
            "prep_time": recipe_data.recipe_overview.prep_time,
            "cook_time": recipe_data.recipe_overview.cook_time,
            "difficulty": recipe_data.recipe_overview.difficulty,
            "cuisine_type": recipe_data.recipe_overview.cuisine_type,
        }

        supabase.table("recipes").update(recipe_dict).eq("id", recipe_id).execute()

        # Delete existing ingredients and instructions
        supabase.table("ingredients").delete().eq("recipe_id", recipe_id).execute()
        supabase.table("instructions").delete().eq("recipe_id", recipe_id).execute()

        # Prepare ingredients batch
        ingredients_batch = []
        for ingredient in recipe_data.ingredients:
            try:
                amount = float(ingredient.amount)
            except (ValueError, TypeError):
                amount = 0.0

            ingredients_batch.append({
                "recipe_id": recipe_id,
                "name": ingredient.item,
                "amount": amount,
                "unit": ingredient.unit,
                "original_text": f"{ingredient.amount} {ingredient.unit or ''} {ingredient.item}".strip(),
            })

        # Batch insert ingredients
        if ingredients_batch:
            supabase.table("ingredients").insert(ingredients_batch).execute()

        # Prepare instructions batch
        instructions_batch = []
        for i, instruction in enumerate(recipe_data.instructions, 1):
            instructions_batch.append({
                "recipe_id": recipe_id,
                "step_number": i,
                "instruction_text": instruction,
            })

        # Batch insert instructions
        if instructions_batch:
            supabase.table("instructions").insert(instructions_batch).execute()

        logger.info(f"Recipe updated: {recipe_id}")

        # Return updated recipe
        return get_recipe_by_id(supabase, recipe_id)

    except APIError as e:
        logger.error(f"Supabase API error updating recipe: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error updating recipe: {str(e)}")
        raise


def recipe_to_schema(db_recipe: Dict[str, Any]) -> RecipeSchema:
    """Convert database dict to Pydantic schema"""
    ingredients = []
    for ingredient in db_recipe.get("ingredients", []):
        ingredients.append(
            IngredientSchema(
                item=ingredient["name"],
                amount=str(ingredient["amount"]),
                unit=ingredient.get("unit"),
                notes=ingredient.get("original_text"),
            )
        )

    # Sort instructions by step_number
    instructions_data = db_recipe.get("instructions", [])
    sorted_instructions = sorted(instructions_data, key=lambda x: x["step_number"])

    from src.schema import RecipeOverview

    recipe_id = int(db_recipe["id"])
    recipe_schema = RecipeSchema(
        recipe_overview=RecipeOverview(
            id=recipe_id,
            title=db_recipe.get("title", ""),
            prep_time=db_recipe.get("prep_time"),
            cook_time=db_recipe.get("cook_time"),
            servings=db_recipe.get("base_servings", 1),
            difficulty=db_recipe.get("difficulty"),
            cuisine_type=db_recipe.get("cuisine_type"),
        ),
        ingredients=ingredients,
        instructions=[instr["instruction_text"] for instr in sorted_instructions],
        equipment=None,  # Not stored in database for MVP
    )

    # Add ID to top-level for easier frontend access
    recipe_schema.id = recipe_id
    return recipe_schema
