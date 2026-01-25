from src.schema import STATUS, AgentState
from src.graph import create_agent_graph
from src.logger import get_logger

# Initialize logger
logger = get_logger(__name__)


def recipe_agent(video_url: str, **kwargs) -> dict:
    # create agent
    graph = create_agent_graph()

    initial_state = AgentState(
        video_url=video_url, max_retries=kwargs.get("max_retries", 2)
    )
    result: AgentState = graph.invoke(initial_state)

    return {
        "success": result.get("extraction_status") == STATUS.SUCCESS,
        "recipe": result.get("extracted_recipe"),
        "metadata": {
            "steps": result.get("number_of_steps"),
        },
    }


if __name__ == "__main__":
    # Extract recipe using agent
    result = recipe_agent(
        video_url="https://www.tiktok.com/@khanhong/video/7557275818255273234",
        max_retries=3,
    )

    if result["success"]:
        logger.info(f"Recipe extracted in {result['metadata']['steps']} steps")
