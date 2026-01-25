from langgraph.graph import StateGraph, START, END
from langchain_core.messages import AIMessage

# import local modules
from src.logger import get_logger
from src.schema import AgentState, STATUS
from src.tools import extract_recipe_from_url

# Initialize logger
logger = get_logger(__name__)


# ***************************
# Graph Nodes
# ***************************
def url_extract_node(state: AgentState) -> AgentState:
    """Node for extracting recipe from URL"""
    logger.info(f"Extracting recipe from: {state.video_url}")
    extraction_result = extract_recipe_from_url.invoke({"video_url": state.video_url})

    if extraction_result["success"]:
        logger.info("Extraction successful")
        return state.model_copy(
            update={
                "extraction_status": STATUS.SUCCESS,
                "extracted_recipe": extraction_result["recipe"],
                "messages": [AIMessage(content="Recipe extracted successfully")],
            }
        )

    else:
        logger.error(f"Extraction failed: {extraction_result['error']}")
        return state.model_copy(
            update={
                "extraction_status": STATUS.FAILED,
                "error_message": extraction_result["error"],
                "messages": [
                    AIMessage(
                        content=f"Extraction failed: {extraction_result['error']}"
                    )
                ],
            }
        )


# ***************************
# Graph Routing Logic
# ***************************
# DO NOT DELETE FOR NOW
def route_after_extraction(state: AgentState):
    if state.extraction_status == STATUS.RUNNING:
        return "recipe_validation"
    else:
        return END


def route_after_validation(state: AgentState):
    return END


# ***************************
# Graph Creation
# ***************************
def create_agent_graph() -> StateGraph:
    """Build the TiktokChef workflow graph"""

    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("video_analysis", url_extract_node)

    # Add edges
    workflow.add_edge(START, "video_analysis")
    workflow.add_edge("video_analysis", END)

    return workflow.compile()
