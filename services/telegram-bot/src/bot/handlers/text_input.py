"""
Text message handler for food input.
"""

import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from ...services.agent_client import AgentClient
from ...config import settings
from ..keyboards.inline import create_clarification_keyboard, create_food_selection_keyboard

logger = logging.getLogger(__name__)

router = Router()

# Initialize agent client
agent_client = AgentClient(settings.AGENT_API_URL)


@router.message(F.text & ~F.text.startswith("/"))
async def handle_text_message(message: Message, state: FSMContext):
    """
    Handle text messages from users.

    Sends message to Agent API and returns response.
    """
    user = message.from_user
    text = message.text

    logger.info(f"Received text from user {user.id}: {text[:50]}...")

    # Get conversation state
    data = await state.get_data()
    conversation_id = data.get("conversation_id")
    last_clarification = data.get("last_clarification")

    # Check if this is a response to a clarification
    clarification_responses = None
    if last_clarification:
        logger.info(f"User is responding to clarification: {last_clarification.get('type')}")
        # Format clarification response based on context
        context = last_clarification.get("context", {})
        food_index = context.get("food_index", 0)
        clarification_responses = {
            f"clarif_{food_index}": text
        }
        # Clear the clarification from state
        await state.update_data(last_clarification=None)

    try:
        # Send to Agent API
        response = await agent_client.ingest_message(
            telegram_id=user.id,
            message=text,
            message_id=message.message_id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            conversation_id=conversation_id,
            clarification_responses=clarification_responses
        )
        
        # Store conversation ID
        if response.get("conversation_id"):
            await state.update_data(conversation_id=response["conversation_id"])
        
        # Check if clarification needed
        needs_clarification = response.get("needs_clarification", False)
        clarification_requests = response.get("clarification_requests", [])
        
        if needs_clarification and clarification_requests:
            # Show clarification with inline keyboard
            clarif = clarification_requests[0]
            question = clarif.get("question", "Уточните, пожалуйста")
            options = clarif.get("options")
            
            # Store clarification in state
            await state.update_data(last_clarification=clarif)
            
            if options:
                # Create inline keyboard
                keyboard = create_clarification_keyboard(
                    clarif,
                    response.get("conversation_id", "")
                )
                await message.answer(question, reply_markup=keyboard)
            else:
                # No options - just ask text
                await message.answer(question)
        else:
            # Normal response - check both reply_text and ai_advice (for conversational responses)
            reply_text = response.get("reply_text") or response.get("ai_advice") or "Обработано!"
            await message.answer(reply_text)
        
    except Exception as e:
        logger.error(f"Error handling message: {e}", exc_info=True)
        await message.answer("Произошла ошибка. Попробуйте позже.")
