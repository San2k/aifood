"""Add weight_history table

Revision ID: 003_weight_history
Revises: 002_fatsecret_oauth
Create Date: 2026-02-07

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003_weight_history'
down_revision = '002_fatsecret_oauth'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add weight_history table."""
    op.create_table(
        'weight_history',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('weight_kg', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('measured_at', sa.DateTime(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['user_profile.id'], ondelete='CASCADE')
    )

    op.create_index('ix_weight_history_user_id', 'weight_history', ['user_id'])
    op.create_index('ix_weight_history_measured_at', 'weight_history', ['measured_at'])


def downgrade() -> None:
    """Remove weight_history table."""
    op.drop_index('ix_weight_history_measured_at', 'weight_history')
    op.drop_index('ix_weight_history_user_id', 'weight_history')
    op.drop_table('weight_history')
