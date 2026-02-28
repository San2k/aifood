"""
Redis Service for state management and caching.
Stores conversation states, graph checkpoints, and cache data.
"""

import redis.asyncio as redis
import json
import logging
from typing import Dict, Any, Optional
from datetime import timedelta

from ..config import settings

logger = logging.getLogger(__name__)


class RedisService:
    """Service for Redis operations."""
    
    def __init__(self):
        self.redis_url = settings.REDIS_URL
        self.client: Optional[redis.Redis] = None
        self._initialized = False
    
    async def connect(self):
        """Initialize Redis connection."""
        if not self._initialized:
            self.client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=50
            )
            self._initialized = True
            logger.info("Redis connection established")
    
    async def disconnect(self):
        """Close Redis connection."""
        if self.client:
            await self.client.close()
            self._initialized = False
            logger.info("Redis connection closed")
    
    async def save_conversation_state(
        self,
        conversation_id: str,
        state: Dict[str, Any],
        ttl: int = None
    ) -> bool:
        """
        Save conversation state to Redis.
        
        Args:
            conversation_id: Unique conversation identifier
            state: State dictionary to save
            ttl: Time to live in seconds (default: from settings)
            
        Returns:
            True if saved successfully
        """
        if not self.client:
            await self.connect()
        
        try:
            key = f"conversation:{conversation_id}"
            value = json.dumps(state, ensure_ascii=False)
            
            if ttl is None:
                ttl = settings.CONVERSATION_EXPIRE_SECONDS
            
            await self.client.setex(key, ttl, value)
            logger.info(f"Saved conversation state: {conversation_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving conversation state: {e}")
            return False
    
    async def get_conversation_state(
        self,
        conversation_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve conversation state from Redis.
        
        Args:
            conversation_id: Unique conversation identifier
            
        Returns:
            State dictionary or None if not found
        """
        if not self.client:
            await self.connect()
        
        try:
            key = f"conversation:{conversation_id}"
            value = await self.client.get(key)
            
            if value:
                state = json.loads(value)
                logger.info(f"Retrieved conversation state: {conversation_id}")
                return state
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving conversation state: {e}")
            return None
    
    async def delete_conversation_state(self, conversation_id: str) -> bool:
        """
        Delete conversation state from Redis.
        
        Args:
            conversation_id: Unique conversation identifier
            
        Returns:
            True if deleted successfully
        """
        if not self.client:
            await self.connect()
        
        try:
            key = f"conversation:{conversation_id}"
            await self.client.delete(key)
            logger.info(f"Deleted conversation state: {conversation_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting conversation state: {e}")
            return False
    
    async def cache_fatsecret_result(
        self,
        cache_key: str,
        data: Dict[str, Any],
        ttl: int = 86400  # 24 hours
    ) -> bool:
        """
        Cache FatSecret API result.
        
        Args:
            cache_key: Cache key (e.g., "search:eggs")
            data: Data to cache
            ttl: Time to live in seconds (default: 24 hours)
            
        Returns:
            True if cached successfully
        """
        if not self.client:
            await self.connect()
        
        try:
            key = f"fatsecret:{cache_key}"
            value = json.dumps(data, ensure_ascii=False)
            await self.client.setex(key, ttl, value)
            logger.info(f"Cached FatSecret result: {cache_key}")
            return True
            
        except Exception as e:
            logger.error(f"Error caching FatSecret result: {e}")
            return False
    
    async def get_cached_fatsecret_result(
        self,
        cache_key: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached FatSecret result.
        
        Args:
            cache_key: Cache key
            
        Returns:
            Cached data or None if not found
        """
        if not self.client:
            await self.connect()
        
        try:
            key = f"fatsecret:{cache_key}"
            value = await self.client.get(key)
            
            if value:
                data = json.loads(value)
                logger.info(f"Cache hit for FatSecret: {cache_key}")
                return data
            
            logger.info(f"Cache miss for FatSecret: {cache_key}")
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving cached FatSecret result: {e}")
            return None
    
    async def set_user_session(
        self,
        user_id: int,
        session_data: Dict[str, Any],
        ttl: int = None
    ) -> bool:
        """
        Set user session data.
        
        Args:
            user_id: User ID
            session_data: Session data dictionary
            ttl: Time to live in seconds (default: from settings)
            
        Returns:
            True if set successfully
        """
        if not self.client:
            await self.connect()
        
        try:
            key = f"session:user:{user_id}"
            value = json.dumps(session_data, ensure_ascii=False)
            
            if ttl is None:
                ttl = settings.SESSION_EXPIRE_SECONDS
            
            await self.client.setex(key, ttl, value)
            logger.info(f"Set user session: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting user session: {e}")
            return False
    
    async def get_user_session(
        self,
        user_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get user session data.
        
        Args:
            user_id: User ID
            
        Returns:
            Session data or None if not found
        """
        if not self.client:
            await self.connect()
        
        try:
            key = f"session:user:{user_id}"
            value = await self.client.get(key)
            
            if value:
                data = json.loads(value)
                return data
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting user session: {e}")
            return None
    
    async def ping(self) -> bool:
        """
        Ping Redis to check connection.
        
        Returns:
            True if connection is healthy
        """
        if not self.client:
            await self.connect()
        
        try:
            await self.client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis ping failed: {e}")
            return False


# Global service instance
redis_service = RedisService()
