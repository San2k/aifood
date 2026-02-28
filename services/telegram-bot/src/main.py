"""
Telegram bot main application.
"""

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from .config import settings as app_settings
from .bot.handlers import start, text_input, photo_input, callbacks, reports, settings as settings_handler, fatsecret, profile

# Configure logging
logging.basicConfig(
    level=getattr(logging, app_settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main bot function."""
    logger.info("Starting Telegram bot...")
    logger.info(f"Agent API URL: {app_settings.AGENT_API_URL}")

    # Initialize bot and dispatcher
    bot = Bot(token=app_settings.TELEGRAM_BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Register handlers (order matters!)
    dp.include_router(start.router)
    dp.include_router(reports.router)  # Commands first
    dp.include_router(settings_handler.router)  # Settings command
    dp.include_router(profile.router)  # Profile and weight management
    dp.include_router(fatsecret.router)  # FatSecret commands
    dp.include_router(callbacks.router)  # Then callbacks
    dp.include_router(photo_input.router)  # Photo messages
    dp.include_router(text_input.router)  # Text input last

    logger.info("Handlers registered:")
    logger.info("  - /start")
    logger.info("  - /today, /week, /delete, /help")
    logger.info("  - /settings")
    logger.info("  - /profile, /weight, /weight_history")
    logger.info("  - /connect_fatsecret, /disconnect_fatsecret, /sync_fatsecret")
    logger.info("  - Callback queries")
    logger.info("  - Photo messages")
    logger.info("  - Text messages")
    logger.info("")
    logger.info("Bot started. Polling for updates...")
    
    try:
        # Start polling
        await dp.start_polling(bot, allowed_updates=["message", "callback_query"])
    except Exception as e:
        logger.error(f"Error in bot polling: {e}", exc_info=True)
    finally:
        await bot.session.close()
        logger.info("Bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
