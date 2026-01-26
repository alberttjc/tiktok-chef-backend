from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from src.models import Recipe, Ingredient, Instruction
from src.schema import Recipe as RecipeSchema, Ingredient as IngredientSchema
from src.logger import get_logger

logger = get_logger(__name__)


def create_recipe(
    db: Session, recipe_data: RecipeSchema, source_url: Optional[str] = None
) -> Recipe:
    """Create a new recipe with ingredients and instructions"""
    logger.info(f"Creating recipe: {recipe_data.recipe_overview.title}")

    # Create recipe record
    db_recipe = Recipe(
        title=recipe_data.recipe_overview.title,
        source_url=source_url,
        base_servings=recipe_data.recipe_overview.servings,
        prep_time=recipe_data.recipe_overview.prep_time,
        cook_time=recipe_data.recipe_overview.cook_time,
        difficulty=recipe_data.recipe_overview.difficulty,
        cuisine_type=recipe_data.recipe_overview.cuisine_type,
    )

    db.add(db_recipe)
    db.flush()  # Get the ID without committing

    # Add ingredients
    for ingredient in recipe_data.ingredients:
        try:
            amount = float(ingredient.amount)
        except (ValueError, TypeError):
            amount = 0.0

        db_ingredient = Ingredient(
            recipe_id=db_recipe.id,
            name=ingredient.item,
            amount=amount,
            unit=ingredient.unit,
            original_text=f"{ingredient.amount} {ingredient.unit or ''} {ingredient.item}".strip(),
        )
        db.add(db_ingredient)

    # Add instructions
    for i, instruction in enumerate(recipe_data.instructions, 1):
        db_instruction = Instruction(
            recipe_id=db_recipe.id, step_number=i, instruction_text=instruction
        )
        db.add(db_instruction)

    db.commit()
    db.refresh(db_recipe)

    logger.info(f"Recipe created with ID: {db_recipe.id}")
    return db_recipe


def get_recipes(db: Session, skip: int = 0, limit: int = 100) -> List[Recipe]:
    """Get all recipes with pagination"""
    return (
        db.query(Recipe)
        .order_by(desc(Recipe.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_recipe_by_id(db: Session, recipe_id: int) -> Optional[Recipe]:
    """Get a single recipe by ID"""
    return db.query(Recipe).filter(Recipe.id == recipe_id).first()


def get_recipe_by_source_url(db: Session, source_url: str) -> Optional[Recipe]:
    """Get a recipe by its source URL"""
    return db.query(Recipe).filter(Recipe.source_url == source_url).first()


def delete_recipe(db: Session, recipe_id: int) -> bool:
    """Delete a recipe by ID"""
    db_recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if db_recipe:
        db.delete(db_recipe)
        db.commit()
        logger.info(f"Recipe deleted: {recipe_id}")
        return True
    return False


def update_recipe(
    db: Session, recipe_id: int, recipe_data: RecipeSchema
) -> Optional[Recipe]:
    """Update an existing recipe with ingredients and instructions"""
    logger.info(f"Updating recipe ID: {recipe_id}")

    # Get existing recipe
    db_recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not db_recipe:
        return None

    # Update recipe fields
    db_recipe.title = recipe_data.recipe_overview.title
    db_recipe.base_servings = recipe_data.recipe_overview.servings
    db_recipe.prep_time = recipe_data.recipe_overview.prep_time
    db_recipe.cook_time = recipe_data.recipe_overview.cook_time
    db_recipe.difficulty = recipe_data.recipe_overview.difficulty
    db_recipe.cuisine_type = recipe_data.recipe_overview.cuisine_type

    # Delete existing ingredients and instructions (cascade delete)
    db.query(Ingredient).filter(Ingredient.recipe_id == recipe_id).delete()
    db.query(Instruction).filter(Instruction.recipe_id == recipe_id).delete()

    # Add updated ingredients
    for ingredient in recipe_data.ingredients:
        try:
            amount = float(ingredient.amount)
        except (ValueError, TypeError):
            amount = 0.0

        db_ingredient = Ingredient(
            recipe_id=int(db_recipe.id),
            name=ingredient.item,
            amount=amount,
            unit=ingredient.unit,
            original_text=f"{ingredient.amount} {ingredient.unit or ''} {ingredient.item}".strip(),
        )
        db.add(db_ingredient)

    # Add updated instructions
    for i, instruction in enumerate(recipe_data.instructions, 1):
        db_instruction = Instruction(
            recipe_id=int(db_recipe.id), step_number=i, instruction_text=instruction
        )
        db.add(db_instruction)

    db.commit()
    db.refresh(db_recipe)

    logger.info(f"Recipe updated: {db_recipe.id}")
    return db_recipe


def recipe_to_schema(db_recipe: Recipe) -> RecipeSchema:
    """Convert database model to Pydantic schema"""
    ingredients = []
    for ingredient in db_recipe.ingredients:
        ingredients.append(
            IngredientSchema(
                item=ingredient.name,
                amount=str(ingredient.amount),
                unit=ingredient.unit,
                notes=ingredient.original_text,
            )
        )

    from src.schema import RecipeOverview

    recipe_id = int(db_recipe.id)
    recipe_schema = RecipeSchema(
        recipe_overview=RecipeOverview(
            id=recipe_id,  # Include database ID
            title=getattr(db_recipe, "title", ""),
            prep_time=getattr(db_recipe, "prep_time", None),
            cook_time=getattr(db_recipe, "cook_time", None),
            servings=getattr(db_recipe, "base_servings", 1),
            difficulty=getattr(db_recipe, "difficulty", None),
            cuisine_type=getattr(db_recipe, "cuisine_type", None),
        ),
        ingredients=ingredients,
        instructions=[
            instr.instruction_text
            for instr in sorted(db_recipe.instructions, key=lambda x: x.step_number)
        ],
        equipment=None,  # Not stored in database for MVP
    )

    # Add ID to top-level for easier frontend access
    recipe_schema.id = recipe_id
    return recipe_schema
