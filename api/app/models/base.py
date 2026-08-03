"""SQLAlchemy declarative Base, re-exported from app.database.

Kept here so model modules can do `from .base import Base` (a common SQLAlchemy
pattern) without coupling every model to the database module's location. The
single source of truth for the Base is `app.database.Base`; this module just
forwards the import.
"""
from ..database import Base

__all__ = ["Base"]