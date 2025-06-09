"""
extensions.py

Defines the shared SQLAlchemy `db` instance and base class
for use across the Flask application to avoid circular imports.
"""

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Declarative base class for all ORM models.
    """
    pass

# Single, shared SQLAlchemy instance
# Import this `db` in your models and routes to avoid circular imports
db = SQLAlchemy(model_class=Base)