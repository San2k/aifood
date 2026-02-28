"""
Main LangGraph definition for nutrition bot.
Assembles all nodes and defines routing logic.
"""

import logging
from typing import Literal
from langgraph.graph import StateGraph, END

from .state import NutritionBotState
from .nodes import (
    detect_input_type,
    detect_intent,
    normalize_input,
    process_photo,
    process_nutrition_label,
    process_custom_nutrition,
    need_clarification,
    fatsecret_search,
    show_more_foods,
    select_serving,
    save_entry,
    calculate_totals,
    generate_advice,
    conversational_response
)

logger = logging.getLogger(__name__)


def route_after_detect(state: NutritionBotState) -> Literal["detect_intent", "process_photo", "need_clarification"]:
    """Route after detecting input type."""
    next_node = state.get("next_node")
    if next_node:
        return next_node

    # For text input, go to intent detection first
    input_type = state.get("input_type", "text")
    if input_type == "text":
        return "detect_intent"
    elif input_type == "photo":
        return "process_photo"
    else:
        # For callbacks/confirmations, may already have clarification
        return "need_clarification"


def route_after_intent(state: NutritionBotState) -> Literal["normalize_input", "conversational_response"]:
    """Route after detecting user intent."""
    next_node = state.get("next_node")
    if next_node:
        return next_node

    # Default to normalize_input if intent detection failed
    return "normalize_input"


def route_after_normalize(state: NutritionBotState) -> Literal["need_clarification", "process_custom_nutrition", "fatsecret_search"]:
    """Route after normalizing input."""
    if state.get("next_node"):
        return state.get("next_node")
    return "fatsecret_search"


def route_after_custom_nutrition(state: NutritionBotState) -> Literal["need_clarification", "save_entry", END]:
    """Route after processing custom nutrition."""
    if state.get("should_end"):
        return END
    if state.get("next_node"):
        return state.get("next_node")
    return "save_entry"


def route_after_photo(state: NutritionBotState) -> Literal["need_clarification", "fatsecret_search", "process_nutrition_label", END]:
    """Route after processing photo."""
    if state.get("should_end"):
        return END
    if state.get("next_node"):
        return state.get("next_node")
    return "fatsecret_search"


def route_after_nutrition_label(state: NutritionBotState) -> Literal["fatsecret_search", "process_custom_nutrition", END]:
    """Route after processing nutrition label."""
    if state.get("should_end"):
        return END
    if state.get("next_node"):
        return state.get("next_node")
    return "fatsecret_search"


def route_after_clarification(state: NutritionBotState) -> Literal["fatsecret_search", "select_serving", "show_more_foods", "process_custom_nutrition", END]:
    """Route after clarification check."""
    if state.get("should_end"):
        return END
    if state.get("next_node"):
        return state.get("next_node")
    return "fatsecret_search"


def route_after_show_more(state: NutritionBotState) -> Literal["need_clarification", END]:
    """Route after showing more foods."""
    if state.get("should_end"):
        return END
    return "need_clarification"


def route_after_search(state: NutritionBotState) -> Literal["select_serving", "need_clarification", END]:
    """Route after FatSecret search."""
    if state.get("should_end"):
        return END
    if state.get("next_node"):
        return state.get("next_node")
    return "select_serving"


def route_after_serving(state: NutritionBotState) -> Literal["save_entry", "need_clarification", END]:
    """Route after serving selection."""
    if state.get("should_end"):
        return END
    if state.get("next_node"):
        return state.get("next_node")
    return "save_entry"


def route_after_save(state: NutritionBotState) -> Literal["calculate_totals", END]:
    """Route after saving entry."""
    if state.get("should_end"):
        return END
    return "calculate_totals"


def route_after_totals(state: NutritionBotState) -> Literal["generate_advice", END]:
    """Route after calculating totals."""
    if state.get("should_end"):
        return END
    return "generate_advice"


def create_nutrition_graph() -> StateGraph:
    """
    Create and compile the nutrition bot graph.
    
    Returns:
        Compiled StateGraph
    """
    # Create graph
    workflow = StateGraph(NutritionBotState)
    
    # Add nodes
    workflow.add_node("detect_input_type", detect_input_type)
    workflow.add_node("detect_intent", detect_intent)
    workflow.add_node("conversational_response", conversational_response)
    workflow.add_node("normalize_input", normalize_input)
    workflow.add_node("process_photo", process_photo)
    workflow.add_node("process_nutrition_label", process_nutrition_label)
    workflow.add_node("process_custom_nutrition", process_custom_nutrition)
    workflow.add_node("need_clarification", need_clarification)
    workflow.add_node("fatsecret_search", fatsecret_search)
    workflow.add_node("show_more_foods", show_more_foods)
    workflow.add_node("select_serving", select_serving)
    workflow.add_node("save_entry", save_entry)
    workflow.add_node("calculate_totals", calculate_totals)
    workflow.add_node("generate_advice", generate_advice)
    
    # Set entry point
    workflow.set_entry_point("detect_input_type")
    
    # Add edges with routing
    workflow.add_conditional_edges(
        "detect_input_type",
        route_after_detect,
        {
            "detect_intent": "detect_intent",
            "process_photo": "process_photo",
            "need_clarification": "need_clarification"
        }
    )

    workflow.add_conditional_edges(
        "detect_intent",
        route_after_intent,
        {
            "normalize_input": "normalize_input",
            "conversational_response": "conversational_response"
        }
    )
    
    workflow.add_conditional_edges(
        "normalize_input",
        route_after_normalize,
        {
            "need_clarification": "need_clarification",
            "process_custom_nutrition": "process_custom_nutrition",
            "fatsecret_search": "fatsecret_search"
        }
    )

    workflow.add_conditional_edges(
        "process_custom_nutrition",
        route_after_custom_nutrition,
        {
            "need_clarification": "need_clarification",
            "save_entry": "save_entry",
            END: END
        }
    )

    workflow.add_conditional_edges(
        "process_photo",
        route_after_photo,
        {
            "need_clarification": "need_clarification",
            "fatsecret_search": "fatsecret_search",
            "process_nutrition_label": "process_nutrition_label",
            END: END
        }
    )

    workflow.add_conditional_edges(
        "process_nutrition_label",
        route_after_nutrition_label,
        {
            "fatsecret_search": "fatsecret_search",
            "process_custom_nutrition": "process_custom_nutrition",
            END: END
        }
    )

    workflow.add_conditional_edges(
        "need_clarification",
        route_after_clarification,
        {
            "fatsecret_search": "fatsecret_search",
            "select_serving": "select_serving",
            "show_more_foods": "show_more_foods",
            "process_custom_nutrition": "process_custom_nutrition",
            END: END
        }
    )

    workflow.add_conditional_edges(
        "show_more_foods",
        route_after_show_more,
        {
            "need_clarification": "need_clarification",
            END: END
        }
    )
    
    workflow.add_conditional_edges(
        "fatsecret_search",
        route_after_search,
        {
            "select_serving": "select_serving",
            "need_clarification": "need_clarification",
            END: END
        }
    )
    
    workflow.add_conditional_edges(
        "select_serving",
        route_after_serving,
        {
            "save_entry": "save_entry",
            "need_clarification": "need_clarification",
            END: END
        }
    )
    
    workflow.add_conditional_edges(
        "save_entry",
        route_after_save,
        {
            "calculate_totals": "calculate_totals",
            END: END
        }
    )
    
    workflow.add_conditional_edges(
        "calculate_totals",
        route_after_totals,
        {
            "generate_advice": "generate_advice",
            END: END
        }
    )
    
    # Final nodes always end
    workflow.add_edge("generate_advice", END)
    workflow.add_edge("conversational_response", END)
    
    # Compile
    compiled_graph = workflow.compile()
    
    logger.info("Nutrition bot graph compiled successfully")
    return compiled_graph


# Global compiled graph instance
nutrition_graph = create_nutrition_graph()
