"""
Inline keyboards for bot.
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict, Any


def create_clarification_keyboard(
    clarification_request: Dict[str, Any],
    conversation_id: str
) -> InlineKeyboardMarkup:
    """
    Create inline keyboard for clarification request.
    
    Args:
        clarification_request: Clarification data from API
        conversation_id: Conversation ID
        
    Returns:
        InlineKeyboardMarkup
    """
    options = clarification_request.get("options", [])
    clarif_type = clarification_request.get("type", "unknown")
    
    buttons = []
    
    # Create button for each option
    for idx, option in enumerate(options):
        # Create callback data: clarif_{conversation_id}_{idx}
        callback_data = f"clarif:{conversation_id}:{idx}"
        buttons.append([InlineKeyboardButton(
            text=option,
            callback_data=callback_data
        )])
    
    # Add "Other" button
    buttons.append([InlineKeyboardButton(
        text="Другое / Ввести вручную",
        callback_data=f"clarif:{conversation_id}:other"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_food_selection_keyboard(
    food_candidates: List[Dict[str, Any]],
    conversation_id: str
) -> InlineKeyboardMarkup:
    """
    Create keyboard for food selection.
    
    Args:
        food_candidates: List of food options
        conversation_id: Conversation ID
        
    Returns:
        InlineKeyboardMarkup
    """
    buttons = []
    
    for idx, food in enumerate(food_candidates[:5]):  # Max 5 options
        food_name = food.get("food_name", "Unknown")
        brand = food.get("brand_name", "")
        
        # Format button text
        text = food_name
        if brand:
            text += f" ({brand})"
        
        callback_data = f"food:{conversation_id}:{idx}"
        buttons.append([InlineKeyboardButton(
            text=text,
            callback_data=callback_data
        )])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_settings_keyboard() -> InlineKeyboardMarkup:
    """
    Create main settings menu keyboard.

    Returns:
        InlineKeyboardMarkup with settings options
    """
    buttons = [
        [InlineKeyboardButton(
            text="👤 Физические параметры",
            callback_data="settings_physical"
        )],
        [InlineKeyboardButton(
            text="🎯 Настроить цели по КБЖУ",
            callback_data="settings_goals"
        )]
        # FatSecret connection button removed - feature not supported
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_goal_selection_keyboard() -> InlineKeyboardMarkup:
    """
    Create goal selection keyboard.

    Returns:
        InlineKeyboardMarkup with goal options
    """
    buttons = [
        [InlineKeyboardButton(
            text="🔥 Похудение",
            callback_data="goal_weight_loss"
        )],
        [InlineKeyboardButton(
            text="💪 Набор мышечной массы",
            callback_data="goal_muscle_gain"
        )],
        [InlineKeyboardButton(
            text="⚖️ Поддержание веса",
            callback_data="goal_maintenance"
        )],
        [InlineKeyboardButton(
            text="🏥 Здоровье",
            callback_data="goal_health"
        )],
        [InlineKeyboardButton(
            text="◀️ Назад",
            callback_data="settings_back"
        )]
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_profile_menu() -> InlineKeyboardMarkup:
    """
    Create profile menu keyboard.

    Returns:
        InlineKeyboardMarkup with profile options
    """
    buttons = [
        [InlineKeyboardButton(
            text="⚙️ Изменить настройки",
            callback_data="open_settings"
        )],
        [InlineKeyboardButton(
            text="⚖️ Обновить вес",
            callback_data="update_weight"
        )],
        [InlineKeyboardButton(
            text="📊 История веса",
            callback_data="weight_history"
        )]
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_weight_menu() -> InlineKeyboardMarkup:
    """
    Create weight management menu keyboard.

    Returns:
        InlineKeyboardMarkup with weight options
    """
    buttons = [
        [InlineKeyboardButton(
            text="📊 Показать историю",
            callback_data="weight_history"
        )],
        [InlineKeyboardButton(
            text="◀️ Назад к профилю",
            callback_data="back_to_profile"
        )]
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)
