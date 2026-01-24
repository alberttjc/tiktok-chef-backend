from src.schema import STATUS, AgentState
from src.graph import create_agent_graph


def recipe_agent(video_url: str, **kwargs) -> dict:
    # create agent
    graph = create_agent_graph()

    initial_state = AgentState(
        video_url=video_url, max_retries=kwargs.get("max_retries", 2)
    )
    result = graph.invoke(initial_state)

    return {
        "success": result.get("extraction_status") == STATUS.SUCCESS,
        "recipe": result.get("extracted_recipe"),
        "metadata": {
            "steps": result.get("number_of_steps"),
            "is_valid": result.get("is_valid_recipe"),
            "errors": result.get("validation_errors"),
        },
    }


if __name__ == "__main__":
    video_url = "https://www.tiktok.com/@khanhong/video/7557275818255273234"

    # Extract recipe directly
    # recipe = transcribe_recipe(video_url=video_url)
    # print(recipe.model_dump_json(indent=2))

    # Extract recipe using agent
    result = recipe_agent(
        video_url="https://www.tiktok.com/@khanhong/video/7557275818255273234",
        max_retries=3,
    )

    if result["success"]:
        print(f"Recipe extracted in {result['metadata']['steps']} steps")
        print(f"Validation: {'✓' if result['metadata']['is_valid'] else '✗'}")
