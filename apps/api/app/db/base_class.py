from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all ForgeMind models.

    All models should inherit from this class. Alembic uses
    Base.metadata to detect schema changes for migrations.
    """

    pass
