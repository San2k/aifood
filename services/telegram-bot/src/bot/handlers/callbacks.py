"""
Callback query handlers for inline keyboards.
"""

import logging
import httpx
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from ...services.agent_client import AgentClient
from ...config import settings

logger = logging.getLogger(__name__)

router = Router()

# Initialize agent client
agent_client = AgentClient(settings.AGENT_API_URL)


@router.callback_query(F.data.startswith("clarif:"))
async def handle_clarification_callback(callback: CallbackQuery, state: FSMContext):
    """
    Handle clarification response from inline keyboard.
    
    Callback data format: clarif:{conversation_id}:{option_index}
    """
    user = callback.from_user
    
    try:
        # Parse callback data
        parts = callback.data.split(":")
        if len(parts) < 3:
            await callback.answer("Ошибка данных")
            return
        
        conversation_id = parts[1]
        option_index = parts[2]
        
        logger.info(f"Clarification callback from user {user.id}: {option_index}")
        
        # Get state data
        data = await state.get_data()
        last_clarification = data.get("last_clarification", {})
        options = last_clarification.get("options", [])
        
        # Determine response text
        if option_index == "other":
            await callback.message.answer("Введите ваш ответ:")
            await callback.answer()
            return
        
        # Get selected option
        option_idx = int(option_index)
        if option_idx < len(options):
            selected_option = options[option_idx]
        else:
            await callback.answer("Опция не найдена")
            return
        
        # Answer callback first
        await callback.answer(f"Выбрано: {selected_option}")

        # Send response back to Agent API
        response = await agent_client.ingest_message(
            telegram_id=user.id,
            message=selected_option,
            message_id=callback.message.message_id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            conversation_id=conversation_id,
            input_type="callback",
            clarification_responses={"clarif_0": selected_option}
        )
        
        # Store new conversation ID
        if response.get("conversation_id"):
            await state.update_data(conversation_id=response["conversation_id"])
        
        # Send reply
        reply_text = response.get("reply_text", "Обработано!")
        await callback.message.answer(reply_text)
        
        # Remove inline keyboard
        await callback.message.edit_reply_markup(reply_markup=None)
        
    except Exception as e:
        logger.error(f"Error handling clarification callback: {e}", exc_info=True)
        await callback.answer("Произошла ошибка")


@router.callback_query(F.data.startswith("food:"))
async def handle_food_selection_callback(callback: CallbackQuery, state: FSMContext):
    """
    Handle food selection from inline keyboard.
    
    Callback data format: food:{conversation_id}:{food_index}
    """
    user = callback.from_user
    
    try:
        # Parse callback data
        parts = callback.data.split(":")
        if len(parts) < 3:
            await callback.answer("Ошибка данных")
            return
        
        conversation_id = parts[1]
        food_index = int(parts[2])
        
        logger.info(f"Food selection callback from user {user.id}: index {food_index}")
        
        await callback.answer(f"Выбран продукт #{food_index + 1}")
        
        # Get state data
        data = await state.get_data()
        food_candidates = data.get("food_candidates", [])
        
        if food_index < len(food_candidates):
            selected_food = food_candidates[food_index]
            food_name = selected_food.get("food_name", "Unknown")
            
            # Continue processing with selected food
            # TODO: Send food_id back to Agent API
            
            await callback.message.answer(f"Выбрано: {food_name}")
            await callback.message.edit_reply_markup(reply_markup=None)
        else:
            await callback.answer("Продукт не найден")
        
    except Exception as e:
        logger.error(f"Error handling food selection: {e}", exc_info=True)
        await callback.answer("Произошла ошибка")


@router.callback_query(F.data.startswith("delete_entry:"))
async def handle_delete_entry_callback(callback: CallbackQuery):
    """
    Handle food entry deletion from inline keyboard.

    Callback data format: delete_entry:{entry_id}
    """
    user = callback.from_user

    try:
        # Parse callback data
        parts = callback.data.split(":")
        if len(parts) < 2:
            await callback.answer("Ошибка данных")
            return

        entry_id = int(parts[1])

        logger.info(f"Delete entry callback from user {user.id}: entry_id {entry_id}")

        # Call Agent API to delete the entry
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = f"{settings.AGENT_API_URL}/v1/food-log/{entry_id}"
            response = await client.delete(url, params={"telegram_id": user.id})
            response.raise_for_status()

        await callback.answer("✅ Запись удалена")

        # Edit message to show deletion success
        await callback.message.edit_text(
            "✅ **Запись успешно удалена!**\n\n"
            "Используйте /today чтобы посмотреть обновлённый отчёт.",
            parse_mode="Markdown"
        )

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            await callback.answer("❌ Запись не найдена")
            await callback.message.edit_text("❌ Запись не найдена или уже удалена.")
        else:
            logger.error(f"HTTP error deleting entry: {e}")
            await callback.answer("❌ Ошибка удаления")
    except Exception as e:
        logger.error(f"Error handling delete entry: {e}", exc_info=True)
        await callback.answer("❌ Произошла ошибка")
