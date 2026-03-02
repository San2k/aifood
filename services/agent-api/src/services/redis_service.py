"""
Redis service for state management.
"""
import redis.asyncio as redis
import json
import logging
from typing import Optional, Dict, Any
from ..config import settings

logger = logging.getLogger(__name__)


class RedisService:
    """Service for managing scan state in Redis."""

    def __init__(self):
        self.redis_url = settings.REDIS_URL
        self.ttl = settings.REDIS_SCAN_TTL
        self.client: Optional[redis.Redis] = None

    async def connect(self):
        """Establish Redis connection."""
        if not self.client:
            self.client = redis.from_url(
                self.redis_url,
                decode_responses=True
            )
            logger.info("Connected to Redis")

    async def disconnect(self):
        """Close Redis connection."""
        if self.client:
            await self.client.close()
            logger.info("Disconnected from Redis")

    async def set_scan_state(
        self,
        scan_id: str,
        data: Dict[str, Any],
        ttl: Optional[int] = None
    ):
        """
        Store scan state in Redis.

        Args:
            scan_id: Scan identifier
            data: State data (will be JSON-serialized)
            ttl: Time to live in seconds (default: settings.REDIS_SCAN_TTL)
        """
        if not self.client:
            await self.connect()

        key = f"scan:{scan_id}"
        ttl = ttl or self.ttl

        await self.client.setex(
            key,
            ttl,
            json.dumps(data)
        )

        logger.debug(f"Stored scan state: {scan_id} (TTL: {ttl}s)")

    async def get_scan_state(self, scan_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve scan state from Redis.

        Args:
            scan_id: Scan identifier

        Returns:
            State data dict or None if not found
        """
        if not self.client:
            await self.connect()

        key = f"scan:{scan_id}"
        data = await self.client.get(key)

        if data:
            return json.loads(data)
        return None

    async def delete_scan_state(self, scan_id: str):
        """
        Delete scan state from Redis.

        Args:
            scan_id: Scan identifier
        """
        if not self.client:
            await self.connect()

        key = f"scan:{scan_id}"
        await self.client.delete(key)
        logger.debug(f"Deleted scan state: {scan_id}")

    async def set_progress(self, scan_id: str, progress: int, step: str):
        """
        Update scan progress.

        Args:
            scan_id: Scan identifier
            progress: Progress percentage (0-100)
            step: Current processing step
        """
        if not self.client:
            await self.connect()

        key = f"scan:{scan_id}:progress"
        await self.client.hset(
            key,
            mapping={
                "progress": progress,
                "step": step
            }
        )
        await self.client.expire(key, self.ttl)
        logger.debug(f"Updated progress for {scan_id}: {progress}% ({step})")

    async def get_progress(self, scan_id: str) -> Optional[Dict[str, Any]]:
        """
        Get scan progress.

        Args:
            scan_id: Scan identifier

        Returns:
            Dict with progress and step, or None
        """
        if not self.client:
            await self.connect()

        key = f"scan:{scan_id}:progress"
        data = await self.client.hgetall(key)

        if data:
            return {
                "progress": int(data.get("progress", 0)),
                "step": data.get("step", "")
            }
        return None

    async def store_pending_scan(
        self,
        scan_id: str,
        odentity: str,
        product_data: Dict[str, Any],
        ttl_seconds: int = 1800
    ):
        """
        Store pending scan for confirmation dialog.

        Args:
            scan_id: Scan identifier
            odentity: User identifier
            product_data: Product and nutrition data
            ttl_seconds: Time to live (default 30 minutes)
        """
        if not self.client:
            await self.connect()

        # Store by scan_id
        scan_key = f"pending_scan:{scan_id}"
        await self.client.setex(
            scan_key,
            ttl_seconds,
            json.dumps({
                "scan_id": scan_id,
                "odentity": odentity,
                "product_data": product_data
            })
        )

        # Store by odentity (for lookup)
        user_key = f"pending_scan:user:{odentity}"
        await self.client.setex(
            user_key,
            ttl_seconds,
            scan_id
        )

        logger.info(f"Stored pending scan {scan_id} for user {odentity}")

    async def get_pending_scan(self, scan_id: str) -> Optional[Dict[str, Any]]:
        """
        Get pending scan by scan_id.

        Args:
            scan_id: Scan identifier

        Returns:
            Pending scan data or None
        """
        if not self.client:
            await self.connect()

        key = f"pending_scan:{scan_id}"
        data = await self.client.get(key)

        if data:
            return json.loads(data)["product_data"]
        return None

    async def get_pending_scan_for_user(self, odentity: str) -> Optional[Dict[str, Any]]:
        """
        Get pending scan for user.

        Args:
            odentity: User identifier

        Returns:
            Pending scan data with scan_id or None
        """
        if not self.client:
            await self.connect()

        # Get scan_id from user key
        user_key = f"pending_scan:user:{odentity}"
        scan_id = await self.client.get(user_key)

        if not scan_id:
            return None

        # Get scan data
        scan_key = f"pending_scan:{scan_id}"
        data = await self.client.get(scan_key)

        if data:
            return json.loads(data)
        return None

    async def clear_pending_scan(self, odentity: str):
        """
        Clear pending scan for user.

        Args:
            odentity: User identifier
        """
        if not self.client:
            await self.connect()

        # Get scan_id
        user_key = f"pending_scan:user:{odentity}"
        scan_id = await self.client.get(user_key)

        if scan_id:
            # Delete both keys
            scan_key = f"pending_scan:{scan_id}"
            await self.client.delete(scan_key, user_key)
            logger.info(f"Cleared pending scan {scan_id} for user {odentity}")


# Global instance
redis_service = RedisService()
