"""Add FatSecret OAuth fields to user_profile

Revision ID: 002_fatsecret_oauth
Revises: 001_initial_schema
Create Date: 2026-02-03 17:20:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_fatsecret_oauth'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add FatSecret OAuth fields."""
    # Add FatSecret integration columns
    op.add_column('user_profile', sa.Column('fatsecret_user_id', sa.String(255), nullable=True))
    op.add_column('user_profile', sa.Column('fatsecret_access_token', sa.String(512), nullable=True))
    op.add_column('user_profile', sa.Column('fatsecret_refresh_token', sa.String(512), nullable=True))
    op.add_column('user_profile', sa.Column('fatsecret_token_expires_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('user_profile', sa.Column('fatsecret_connected', sa.Boolean(), nullable=False, server_default='false'))

    # Add index for fatsecret_user_id
    op.create_index('ix_user_profile_fatsecret_user_id', 'user_profile', ['fatsecret_user_id'])


def downgrade() -> None:
    """Remove FatSecret OAuth fields."""
    # Drop index first
    op.drop_index('ix_user_profile_fatsecret_user_id', 'user_profile')

    # Drop columns
    op.drop_column('user_profile', 'fatsecret_connected')
    op.drop_column('user_profile', 'fatsecret_token_expires_at')
    op.drop_column('user_profile', 'fatsecret_refresh_token')
    op.drop_column('user_profile', 'fatsecret_access_token')
    op.drop_column('user_profile', 'fatsecret_user_id')
