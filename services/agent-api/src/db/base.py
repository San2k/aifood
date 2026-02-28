"""
SQLAlchemy declarative base.
All models should inherit from Base.
"""

from sqlalchemy.orm import declarative_base

# Create declarative base for all models
Base = declarative_base()

# Import all models here to ensure they're registered with Base
# This is important for Alembic migrations to work correctly
__all__ = ["Base"]
