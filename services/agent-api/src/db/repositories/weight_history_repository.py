"""
Weight History Repository.
Handles weight tracking CRUD operations.
"""

import logging
from typing import List, Optional
from datetime import datetime, date
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.weight_history import WeightHistory

logger = logging.getLogger(__name__)


class WeightHistoryRepository:
    """Repository for weight history operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_entry(
        self,
        user_id: int,
        weight_kg: float,
        measured_at: Optional[datetime] = None,
        notes: Optional[str] = None
    ) -> WeightHistory:
        """
        Create new weight history entry.

        Args:
            user_id: Database user ID
            weight_kg: Weight in kilograms
            measured_at: When weight was measured (defaults to now)
            notes: Optional notes

        Returns:
            Created WeightHistory entry
        """
        if measured_at is None:
            measured_at = datetime.utcnow()

        entry = WeightHistory(
            user_id=user_id,
            weight_kg=weight_kg,
            measured_at=measured_at,
            notes=notes,
            created_at=datetime.utcnow()
        )

        self.session.add(entry)
        await self.session.flush()
        await self.session.refresh(entry)

        logger.info(f"Created weight entry: user_id={user_id}, weight={weight_kg}kg")
        return entry

    async def get_latest_weight(self, user_id: int) -> Optional[WeightHistory]:
        """
        Get user's latest weight entry.

        Args:
            user_id: Database user ID

        Returns:
            Latest WeightHistory or None
        """
        stmt = (
            select(WeightHistory)
            .where(WeightHistory.user_id == user_id)
            .order_by(WeightHistory.measured_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_weight_history(
        self,
        user_id: int,
        limit: int = 30
    ) -> List[WeightHistory]:
        """
        Get user's weight history.

        Args:
            user_id: Database user ID
            limit: Maximum number of entries to return

        Returns:
            List of WeightHistory entries ordered by date (newest first)
        """
        stmt = (
            select(WeightHistory)
            .where(WeightHistory.user_id == user_id)
            .order_by(WeightHistory.measured_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_weight_on_date(
        self,
        user_id: int,
        target_date: date
    ) -> Optional[WeightHistory]:
        """
        Get weight entry for specific date.

        Args:
            user_id: Database user ID
            target_date: Target date

        Returns:
            WeightHistory for that date or None
        """
        start_datetime = datetime.combine(target_date, datetime.min.time())
        end_datetime = datetime.combine(target_date, datetime.max.time())

        stmt = (
            select(WeightHistory)
            .where(
                and_(
                    WeightHistory.user_id == user_id,
                    WeightHistory.measured_at >= start_datetime,
                    WeightHistory.measured_at <= end_datetime
                )
            )
            .order_by(WeightHistory.measured_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_entry(self, entry_id: int, user_id: int) -> bool:
        """
        Delete weight history entry.

        Args:
            entry_id: Entry ID to delete
            user_id: User ID (for verification)

        Returns:
            True if deleted, False if not found
        """
        stmt = select(WeightHistory).where(
            and_(
                WeightHistory.id == entry_id,
                WeightHistory.user_id == user_id
            )
        )
        result = await self.session.execute(stmt)
        entry = result.scalar_one_or_none()

        if entry:
            await self.session.delete(entry)
            await self.session.flush()
            logger.info(f"Deleted weight entry: id={entry_id}, user_id={user_id}")
            return True

        return False
