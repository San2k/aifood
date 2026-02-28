"""Photo input handler for food package recognition."""

import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from ...services.agent_client import AgentClient
from ...config import settings

logger = logging.getLogger(__name__)

router = Router()
agent_client = AgentClient(settings.AGENT_API_URL)


@router.message(F.photo)
async def handle_photo_message(message: Message, state: FSMContext):
    """
    Handle photo messages - recognize food from package photo.

    Args:
        message: Telegram message with photo
        state: FSM context for conversation state
    """
    user = message.from_user

    if not user:
        return

    logger.info(f"Received photo from user {user.id}")

    # Get the highest resolution photo (last one in the array)
    photo = message.photo[-1]
    file_id = photo.file_id

    # Get the bot instance to download file
    bot = message.bot
    file = await bot.get_file(file_id)

    # Get file URL that can be accessed by agent-api
    # For Telegram, we'll use the file_path to construct URL
    file_url = f"https://api.telegram.org/file/bot{bot.token}/{file.file_path}"

    logger.info(f"Photo file_id: {file_id}, file_url: {file_url[:50]}...")

    # Get conversation state
    data = await state.get_data()
    conversation_id = data.get("conversation_id")

    try:
        # Send photo to agent API for processing
        response = await agent_client.ingest_message(
            telegram_id=user.id,
            message=message.caption or "",  # Use caption as text if provided
            message_id=message.message_id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            conversation_id=conversation_id,
            input_type="photo",
            photo_file_id=file_url  # Send the accessible URL
        )

        # Update conversation ID
        if response.get("conversation_id"):
            await state.update_data(conversation_id=response["conversation_id"])

        # Handle response
        if response.get("needs_clarification"):
            clarification_requests = response.get("clarification_requests", [])

            if clarification_requests:
                clarif = clarification_requests[0]
                question = clarif.get("question", "")

                # Store clarification in state
                await state.update_data(last_clarification=clarif)

                # Check if there are options (for inline keyboard)
                if clarif.get("options"):
                    from ..keyboards.inline import create_clarification_keyboard
                    keyboard = create_clarification_keyboard(clarif, response["conversation_id"])
                    await message.answer(question, reply_markup=keyboard)
                else:
                    await message.answer(question)

        elif response.get("reply_text"):
            # Success or error message
            await message.answer(response["reply_text"])

        else:
            await message.answer("Фото обработано. Ищу продукт...")

    except Exception as e:
        logger.error(f"Error processing photo: {e}", exc_info=True)
        await message.answer("Извините, произошла ошибка при обработке фото. Попробуйте еще раз или отправьте текстом.")
