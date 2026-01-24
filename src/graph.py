from langgraph.graph import StateGraph, START, END
from langchain_core.messages import AIMessage

# import local modules
from src.schema import AgentState, STATUS
from src.tools import extract_recipe_from_url, validate_recipe_structure


# ***************************
# Graph Nodes
# ***************************
def url_extract_node(state: AgentState) -> AgentState:
    """Node for extracting recipe from URL"""
    extraction_result = extract_recipe_from_url.invoke({"video_url": state.video_url})

    if extraction_result["success"]:
        return state.model_copy(
            update={
                "extraction_status": STATUS.RUNNING,
                "extracted_recipe": extraction_result["recipe"],
                "messages": [AIMessage(content="Recipe extracted successfully")],
            }
        )

    else:
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


def validation_node(state: AgentState) -> AgentState:
    """Node for validating recipe"""
    recipe_data = state.extracted_recipe

    if not recipe_data:
        return state.model_copy(
            update={
                "extraction_status": STATUS.FAILED,
                "error_message": "No recipe data to validate",
                "is_valid_recipe": False,
                "messages": [AIMessage(content="No recipe data to validate")],
            }
        )

    # Validate recipe
    validation_result = validate_recipe_structure.invoke({"recipe_data": recipe_data})

    return state.model_copy(
        update={
            "extraction_status": STATUS.SUCCESS,
            "is_valid_recipe": validation_result["is_valid"],
            "validation_errors": validation_result["error"],
            "messages": [AIMessage(content="Recipe validated successfully")],
        }
    )


# ***************************
# Graph Routing Logic
# ***************************
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
    """Build the recipe extraction workflow graph"""

    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("video_analysis", url_extract_node)
    workflow.add_node("recipe_validation", validation_node)

    # Add edges
    workflow.add_edge(START, "video_analysis")
    workflow.add_conditional_edges("video_analysis", route_after_extraction)
    workflow.add_conditional_edges("recipe_validation", route_after_validation)

    return workflow.compile()
