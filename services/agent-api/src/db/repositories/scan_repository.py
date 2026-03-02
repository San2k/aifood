"""
Repository for label_scans table operations.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import Optional, List
from decimal import Decimal
from datetime import datetime

from ..models.label_scan import LabelScan


class ScanRepository:
    """Repository for label scan CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_scan(
        self,
        scan_id: str,
        odentity: str,
        photo_url: str,
        status: str = 'processing'
    ) -> LabelScan:
        """
        Create a new label scan record.

        Args:
            scan_id: Unique scan identifier (UUID)
            odentity: User identifier
            photo_url: URL of the nutrition label photo
            status: Initial status (default: 'processing')

        Returns:
            Created LabelScan instance
        """
        scan = LabelScan(
            scan_id=scan_id,
            odentity=odentity,
            photo_url=photo_url,
            status=status,
        )

        self.session.add(scan)
        await self.session.flush()
        await self.session.refresh(scan)

        return scan

    async def get_scan_by_id(self, scan_id: str) -> Optional[LabelScan]:
        """
        Get scan by scan_id.

        Args:
            scan_id: Scan identifier

        Returns:
            LabelScan or None if not found
        """
        stmt = select(LabelScan).where(LabelScan.scan_id == scan_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_scan(
        self,
        scan_id: str,
        **updates
    ) -> Optional[LabelScan]:
        """
        Update scan fields.

        Args:
            scan_id: Scan identifier
            **updates: Fields to update

        Returns:
            Updated LabelScan or None if not found
        """
        scan = await self.get_scan_by_id(scan_id)

        if scan:
            for key, value in updates.items():
                if hasattr(scan, key):
                    setattr(scan, key, value)

            await self.session.flush()
            await self.session.refresh(scan)

        return scan

    async def update_scan_status(
        self,
        scan_id: str,
        status: str,
        error_message: Optional[str] = None
    ) -> Optional[LabelScan]:
        """
        Update scan status.

        Args:
            scan_id: Scan identifier
            status: New status
            error_message: Optional error message if status is 'failed'

        Returns:
            Updated LabelScan or None if not found
        """
        updates = {'status': status}

        if status == 'failed' and error_message:
            updates['error_message'] = error_message

        if status == 'pending_confirmation':
            updates['processed_at'] = datetime.utcnow()

        if status == 'confirmed':
            updates['confirmed_at'] = datetime.utcnow()

        return await self.update_scan(scan_id, **updates)

    async def get_pending_scans_by_user(
        self,
        odentity: str
    ) -> List[LabelScan]:
        """
        Get all pending scans for a user.

        Args:
            odentity: User identifier

        Returns:
            List of LabelScan with status='pending_confirmation'
        """
        stmt = select(LabelScan).where(
            LabelScan.odentity == odentity,
            LabelScan.status == 'pending_confirmation'
        ).order_by(LabelScan.created_at.desc())

        result = await self.session.execute(stmt)
        return list(result.scalars().all())
