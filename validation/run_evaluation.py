#!/usr/bin/env python3
"""
Evaluation script for reviewing recipe agent outputs with live extraction.

This script runs the agent with real API calls and displays the results
for manual review and accuracy verification.
"""

import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent import recipe_agent
from src.schema import Recipe
from src.logger import get_logger
from test_cases import TEST_CASES

logger = get_logger(__name__)


# ***************************
# Output Display Functions
# ***************************
def print_header(text: str, char: str = "="):
    """Print a formatted header"""
    print(f"\n{char * 80}")
    print(f"{text.center(80)}")
    print(f"{char * 80}\n")


def print_section(title: str):
    """Print a section title"""
    print(f"\n{'─' * 80}")
    print(f"  {title}")
    print(f"{'─' * 80}")


def print_recipe_overview(overview):
    """Print recipe overview in a formatted way"""
    print(f"  Title:        {overview.title}")
    print(f"  Servings:     {overview.servings}")
    print(f"  Prep Time:    {overview.prep_time or 'N/A'}")
    print(f"  Cook Time:    {overview.cook_time or 'N/A'}")
    print(f"  Difficulty:   {overview.difficulty or 'N/A'}")
    print(f"  Cuisine:      {overview.cuisine_type or 'N/A'}")


def print_ingredients(ingredients):
    """Print ingredients in a formatted way"""
    for i, ing in enumerate(ingredients, 1):
        amount = ing.amount
        unit = ing.unit or ''
        item = ing.item
        notes = ing.notes or ''

        ingredient_str = f"  {i:2d}. {amount} {unit} {item}".strip()
        if notes:
            ingredient_str += f" ({notes})"
        print(ingredient_str)


def print_instructions(instructions: List[str]):
    """Print instructions in a formatted way"""
    for i, instruction in enumerate(instructions, 1):
        print(f"  {i:2d}. {instruction}")


def compare_with_expected(actual_recipe, expected_recipe) -> List[str]:
    """Compare actual recipe with expected recipe and return differences"""
    differences = []

    # Compare overview
    actual_overview = actual_recipe.recipe_overview
    expected_overview = expected_recipe["recipe_overview"]

    if actual_overview.title != expected_overview["title"]:
        differences.append(f"Title: '{actual_overview.title}' vs expected '{expected_overview['title']}'")
    if actual_overview.prep_time != expected_overview.get("prep_time"):
        differences.append(f"Prep time: '{actual_overview.prep_time}' vs expected '{expected_overview.get('prep_time')}'")
    if actual_overview.cook_time != expected_overview.get("cook_time"):
        differences.append(f"Cook time: '{actual_overview.cook_time}' vs expected '{expected_overview.get('cook_time')}'")
    if actual_overview.servings != expected_overview["servings"]:
        differences.append(f"Servings: {actual_overview.servings} vs expected {expected_overview['servings']}")
    if actual_overview.difficulty != expected_overview.get("difficulty"):
        differences.append(f"Difficulty: '{actual_overview.difficulty}' vs expected '{expected_overview.get('difficulty')}'")
    if actual_overview.cuisine_type != expected_overview.get("cuisine_type"):
        differences.append(f"Cuisine: '{actual_overview.cuisine_type}' vs expected '{expected_overview.get('cuisine_type')}'")

    # Compare counts
    actual_ing_count = len(actual_recipe.ingredients)
    expected_ing_count = len(expected_recipe["ingredients"])
    if actual_ing_count != expected_ing_count:
        differences.append(f"Ingredient count: {actual_ing_count} vs expected {expected_ing_count}")

    actual_inst_count = len(actual_recipe.instructions)
    expected_inst_count = len(expected_recipe["instructions"])
    if actual_inst_count != expected_inst_count:
        differences.append(f"Instruction count: {actual_inst_count} vs expected {expected_inst_count}")

    return differences


def check_completeness(result: Dict[str, Any]) -> Dict[str, Any]:
    """Check completeness of extraction"""
    if not result.get("success"):
        return {
            "complete": False,
            "notes": ["Extraction failed"]
        }

    recipe = result["recipe"]
    overview = recipe.recipe_overview
    notes = []

    # Check optional fields
    if not overview.prep_time:
        notes.append("Missing prep_time")
    if not overview.cook_time:
        notes.append("Missing cook_time")
    if not overview.difficulty:
        notes.append("Missing difficulty")
    if not overview.cuisine_type:
        notes.append("Missing cuisine_type")

    return {
        "complete": len(notes) == 0,
        "notes": notes if notes else ["All fields populated"]
    }


def display_test_result(test_case: Dict[str, Any], result: Dict[str, Any], execution_time: float):
    """Display a single test result for review"""
    print_header(f"TEST CASE #{test_case['id']}: {test_case['name']}", "═")

    # Test information
    print(f"Description:  {test_case['description']}")
    print(f"Video URL:    {test_case['video_url']}")
    print(f"Execution:    {execution_time:.3f}s")

    # Result status
    print_section("EXTRACTION RESULT")
    success_symbol = "✓" if result.get("success") else "✗"
    print(f"  Status: {success_symbol} {'SUCCESS' if result.get('success') else 'FAILED'}")

    if not result.get("success"):
        print(f"  Error: {result.get('metadata', {}).get('error', 'Unknown error')}")
        return

    # Recipe details
    recipe = result["recipe"]

    print_section("RECIPE OVERVIEW")
    print_recipe_overview(recipe.recipe_overview)

    print_section("INGREDIENTS")
    print_ingredients(recipe.ingredients)

    print_section("INSTRUCTIONS")
    print_instructions(recipe.instructions)

    # Metadata
    print_section("METADATA")
    metadata = result.get("metadata", {})
    print(f"  Steps taken:  {metadata.get('steps', 'N/A')}")

    # Completeness check
    print_section("COMPLETENESS CHECK")
    completeness = check_completeness(result)

    if completeness["complete"]:
        print("  ✓ All optional fields populated")
    else:
        for note in completeness["notes"]:
            print(f"  • {note}")

    # Compare with expected if available
    if test_case.get("expected_response"):
        print_section("COMPARISON WITH EXPECTED")
        differences = compare_with_expected(recipe, test_case["expected_response"]["recipe"])

        if not differences:
            print("  ✓ Matches expected response")
        else:
            print("  ⚠ Differences found:")
            for diff in differences:
                print(f"    • {diff}")


# ***************************
# Main Evaluation Runner
# ***************************
def run_evaluation(output_file: Optional[str] = None):
    """
    Run evaluation with test cases using live extraction

    Args:
        output_file: Optional path to save results as JSON
    """
    print_header("RECIPE AGENT EVALUATION - LIVE EXTRACTION", "═")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total test cases: {len(TEST_CASES)}")

    results = []
    summary = {
        "total": len(TEST_CASES),
        "successful": 0,
        "failed": 0,
        "total_time": 0
    }

    for test_case in TEST_CASES:
        start_time = time.time()

        # Run agent with live extraction
        result = recipe_agent(test_case["video_url"])

        execution_time = time.time() - start_time
        summary["total_time"] += execution_time

        # Display result
        display_test_result(test_case, result, execution_time)

        # Track success/failure
        if result.get("success"):
            summary["successful"] += 1
        else:
            summary["failed"] += 1

        # Store result
        results.append({
            "test_case": test_case["name"],
            "result": result,
            "execution_time": execution_time
        })

        # Pause between tests for readability
        if len(TEST_CASES) > 1:
            print("\n" + "─" * 80)
            input("Press Enter to continue to next test case...")

    # Summary
    print_header("EVALUATION SUMMARY", "═")
    print(f"  Total Tests:      {summary['total']}")
    print(f"  Successful:       {summary['successful']} ✓")
    print(f"  Failed:           {summary['failed']} ✗")
    print(f"  Success Rate:     {(summary['successful'] / summary['total'] * 100):.1f}%")
    print(f"  Total Time:       {summary['total_time']:.3f}s")
    print(f"  Avg Time/Test:    {(summary['total_time'] / summary['total']):.3f}s")

    # Save results if requested
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump({
                "summary": summary,
                "results": results,
                "timestamp": datetime.now().isoformat()
            }, f, indent=2, default=str)

        print(f"\n  Results saved to: {output_file}")

    print("\n" + "═" * 80 + "\n")

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Evaluate recipe agent with live extraction"
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Save results to JSON file"
    )

    args = parser.parse_args()

    try:
        results = run_evaluation(output_file=args.output)
    except KeyboardInterrupt:
        print("\n\nEvaluation interrupted by user.")
        sys.exit(0)
