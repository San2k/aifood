"""Initial database schema

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-01-25 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create ENUM types
    op.execute("CREATE TYPE usergoal AS ENUM ('weight_loss', 'muscle_gain', 'maintenance', 'health')")
    op.execute("CREATE TYPE activitylevel AS ENUM ('sedentary', 'lightly_active', 'moderately_active', 'very_active', 'extremely_active')")
    op.execute("CREATE TYPE measurementsystem AS ENUM ('metric', 'imperial')")
    op.execute("CREATE TYPE mealtype AS ENUM ('breakfast', 'lunch', 'dinner', 'snack')")
    op.execute("CREATE TYPE inputtype AS ENUM ('text', 'photo', 'custom', 'mixed')")

    # Create user_profile table
    op.create_table(
        'user_profile',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('telegram_id', sa.BigInteger(), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=True),
        sa.Column('first_name', sa.String(length=255), nullable=True),
        sa.Column('last_name', sa.String(length=255), nullable=True),

        # User Goals
        sa.Column('goal', postgresql.ENUM('weight_loss', 'muscle_gain', 'maintenance', 'health', name='usergoal'), nullable=True),
        sa.Column('target_calories', sa.Integer(), nullable=True),
        sa.Column('target_protein', sa.Integer(), nullable=True),
        sa.Column('target_carbs', sa.Integer(), nullable=True),
        sa.Column('target_fat', sa.Integer(), nullable=True),
        sa.Column('target_fiber', sa.Integer(), nullable=True),

        # User Metrics
        sa.Column('age', sa.Integer(), nullable=True),
        sa.Column('gender', sa.String(length=20), nullable=True),
        sa.Column('height_cm', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('weight_kg', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('activity_level', postgresql.ENUM('sedentary', 'lightly_active', 'moderately_active', 'very_active', 'extremely_active', name='activitylevel'), nullable=True),

        # Preferences
        sa.Column('timezone', sa.String(length=50), nullable=False, server_default='UTC'),
        sa.Column('language_code', sa.String(length=10), nullable=False, server_default='en'),
        sa.Column('measurement_system', postgresql.ENUM('metric', 'imperial', name='measurementsystem'), nullable=False, server_default='metric'),

        # Metadata
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_active_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),

        sa.PrimaryKeyConstraint('id', name=op.f('pk_user_profile')),
        sa.UniqueConstraint('telegram_id', name=op.f('uq_user_profile_telegram_id'))
    )
    op.create_index(op.f('ix_telegram_id'), 'user_profile', ['telegram_id'], unique=False)

    # Create food_log_entry table
    op.create_table(
        'food_log_entry',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),

        # Food Identification
        sa.Column('food_id', sa.String(length=255), nullable=True),
        sa.Column('food_name', sa.String(length=500), nullable=False),
        sa.Column('brand_name', sa.String(length=255), nullable=True),
        sa.Column('is_custom', sa.Boolean(), nullable=False, server_default='false'),

        # Serving Information
        sa.Column('serving_id', sa.String(length=255), nullable=True),
        sa.Column('serving_description', sa.String(length=500), nullable=True),
        sa.Column('serving_size', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('serving_unit', sa.String(length=50), nullable=True),
        sa.Column('number_of_servings', sa.Numeric(precision=10, scale=2), nullable=False, server_default='1.0'),

        # Nutrition Data
        sa.Column('calories', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('protein', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('carbohydrates', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('fat', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('saturated_fat', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('polyunsaturated_fat', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('monounsaturated_fat', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('trans_fat', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('cholesterol', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('sodium', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('potassium', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('fiber', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('sugar', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('vitamin_a', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('vitamin_c', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('calcium', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('iron', sa.Numeric(precision=10, scale=2), nullable=True),

        # Meal Context
        sa.Column('meal_type', postgresql.ENUM('breakfast', 'lunch', 'dinner', 'snack', name='mealtype'), nullable=True),
        sa.Column('consumed_at', sa.DateTime(timezone=True), nullable=False),

        # Source Tracking
        sa.Column('input_type', postgresql.ENUM('text', 'photo', 'custom', 'mixed', name='inputtype'), nullable=False, server_default='text'),
        sa.Column('original_input', sa.Text(), nullable=True),
        sa.Column('label_scan_id', sa.BigInteger(), nullable=True),

        # Metadata
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),

        sa.ForeignKeyConstraint(['user_id'], ['user_profile.id'], name=op.f('fk_food_log_entry_user_id_user_profile'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_food_log_entry'))
    )
    op.create_index(op.f('ix_food_log_user_id'), 'food_log_entry', ['user_id'], unique=False)
    op.create_index(op.f('ix_food_log_consumed_at'), 'food_log_entry', ['consumed_at'], unique=False)
    op.create_index(op.f('ix_food_log_created_at'), 'food_log_entry', ['created_at'], unique=False)
    op.create_index(op.f('ix_food_log_user_consumed'), 'food_log_entry', ['user_id', 'consumed_at'], unique=False)

    # Create conversation_state table
    op.create_table(
        'conversation_state',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('current_node', sa.String(length=100), nullable=True),
        sa.Column('graph_state', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('pending_clarifications', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('selected_food_candidates', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('pending_food_entry', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),

        sa.ForeignKeyConstraint(['user_id'], ['user_profile.id'], name=op.f('fk_conversation_state_user_id_user_profile'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_conversation_state')),
        sa.UniqueConstraint('conversation_id', name=op.f('uq_conversation_state_conversation_id'))
    )
    op.create_index(op.f('ix_conversation_user_id'), 'conversation_state', ['user_id'], unique=False)
    op.create_index(op.f('ix_conversation_id'), 'conversation_state', ['conversation_id'], unique=False)
    op.create_index(op.f('ix_conversation_expires_at'), 'conversation_state', ['expires_at'], unique=False)
    op.create_index(op.f('ix_conversation_is_active'), 'conversation_state', ['is_active'], unique=False)


def downgrade() -> None:
    # Drop tables
    op.drop_index(op.f('ix_conversation_is_active'), table_name='conversation_state')
    op.drop_index(op.f('ix_conversation_expires_at'), table_name='conversation_state')
    op.drop_index(op.f('ix_conversation_id'), table_name='conversation_state')
    op.drop_index(op.f('ix_conversation_user_id'), table_name='conversation_state')
    op.drop_table('conversation_state')

    op.drop_index(op.f('ix_food_log_user_consumed'), table_name='food_log_entry')
    op.drop_index(op.f('ix_food_log_created_at'), table_name='food_log_entry')
    op.drop_index(op.f('ix_food_log_consumed_at'), table_name='food_log_entry')
    op.drop_index(op.f('ix_food_log_user_id'), table_name='food_log_entry')
    op.drop_table('food_log_entry')

    op.drop_index(op.f('ix_telegram_id'), table_name='user_profile')
    op.drop_table('user_profile')

    # Drop ENUM types
    op.execute("DROP TYPE IF EXISTS inputtype")
    op.execute("DROP TYPE IF EXISTS mealtype")
    op.execute("DROP TYPE IF EXISTS measurementsystem")
    op.execute("DROP TYPE IF EXISTS activitylevel")
    op.execute("DROP TYPE IF EXISTS usergoal")
