"""
User Repository.
Handles user CRUD operations.
"""

import logging
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.user_profile import UserProfile

logger = logging.getLogger(__name__)


class UserRepository:
    """Repository for user operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_telegram_id(self, telegram_id: int) -> Optional[UserProfile]:
        """
        Get user by Telegram ID.
        
        Args:
            telegram_id: Telegram user ID
            
        Returns:
            UserProfile or None
        """
        stmt = select(UserProfile).where(UserProfile.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if user:
            logger.info(f"Found user: {user.id} (telegram_id={telegram_id})")
        else:
            logger.info(f"User not found: telegram_id={telegram_id}")
        
        return user
    
    async def get_by_id(self, user_id: int) -> Optional[UserProfile]:
        """
        Get user by ID.
        
        Args:
            user_id: Database user ID
            
        Returns:
            UserProfile or None
        """
        stmt = select(UserProfile).where(UserProfile.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def create_user(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        language_code: str = "en"
    ) -> UserProfile:
        """
        Create new user.
        
        Args:
            telegram_id: Telegram user ID
            username: Telegram username
            first_name: User's first name
            last_name: User's last name
            language_code: Language code
            
        Returns:
            Created UserProfile
        """
        user = UserProfile(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            language_code=language_code,
            is_active=True
        )
        
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        
        logger.info(f"Created user: {user.id} (telegram_id={telegram_id}, username={username})")
        return user
    
    async def get_or_create_user(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        language_code: str = "en"
    ) -> tuple[UserProfile, bool]:
        """
        Get existing user or create new one.
        
        Args:
            telegram_id: Telegram user ID
            username: Telegram username
            first_name: User's first name
            last_name: User's last name
            language_code: Language code
            
        Returns:
            Tuple of (UserProfile, created: bool)
        """
        user = await self.get_by_telegram_id(telegram_id)
        
        if user:
            return user, False
        
        user = await self.create_user(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            language_code=language_code
        )
        
        return user, True
    
    async def update_last_active(self, user_id: int):
        """
        Update user's last active timestamp.
        
        Args:
            user_id: Database user ID
        """
        from datetime import datetime
        
        user = await self.get_by_id(user_id)
        if user:
            user.last_active_at = datetime.utcnow()
            await self.session.flush()
            logger.debug(f"Updated last_active for user {user_id}")
