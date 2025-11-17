# _*_ coding: utf-8 _*_
"""
Database initialization and models.
Uses SQLAlchemy for ORM and proper session management.
"""

from datetime import datetime
from typing import Any, Optional, Type, TypeVar

from sqlalchemy import Column, Integer, String, Boolean, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Create declarative base
EntityModel = declarative_base()

# Global session factory (to be initialized by app)
_session_factory: Optional[sessionmaker] = None


def init_db(database_url: str, echo: bool = False, 
           pool_size: int = 10, max_overflow: int = 20) -> sessionmaker:
    """
    Initialize database connection and session factory.
    
    Args:
        database_url: SQLAlchemy database URL
        echo: Whether to echo SQL queries
        pool_size: Connection pool size
        max_overflow: Maximum overflow connections
        
    Returns:
        Session factory
    """
    # Use StaticPool for SQLite in-memory databases
    kwargs = {
        "echo": echo,
    }
    
    if "sqlite:///:memory:" in database_url:
        kwargs["connect_args"] = {"check_same_thread": False}
        kwargs["poolclass"] = StaticPool
    else:
        kwargs["pool_size"] = pool_size
        kwargs["max_overflow"] = max_overflow
    
    engine = create_engine(database_url, **kwargs)
    
    # Create session factory
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    
    # Create all tables
    EntityModel.metadata.create_all(engine)
    
    global _session_factory
    _session_factory = session_factory
    
    return session_factory


def get_session() -> Session:
    """Get a new database session."""
    if _session_factory is None:
        raise RuntimeError("Database not initialized. Call init_db first.")
    return _session_factory()


def close_session(session: Session) -> None:
    """Close a database session."""
    if session:
        session.close()


T = TypeVar("T", bound="EntityModel")


class BaseMixin:
    """Base mixin for common model methods."""

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True, comment="Soft delete timestamp")
    is_active = Column(Boolean, default=True, nullable=False, comment="Soft delete flag")

    @classmethod
    def get(cls: Type[T], session: Optional[Session] = None, **kwargs) -> Optional[T]:
        """
        Get a single record by filters, excluding soft-deleted records.
        
        Args:
            session: Database session (uses global if not provided)
            **kwargs: Filter criteria
            
        Returns:
            Model instance or None
        """
        if session is None:
            session = get_session()
            should_close = True
        else:
            should_close = False
        
        try:
            # Always exclude soft-deleted records
            query = session.query(cls).filter(
                cls.is_active == True,
                cls.deleted_at == None
            )
            
            # Apply filters
            for key, value in kwargs.items():
                if hasattr(cls, key):
                    query = query.filter(getattr(cls, key) == value)
            
            return query.first()
        finally:
            if should_close:
                close_session(session)

    @classmethod
    def get_all(cls: Type[T], session: Optional[Session] = None, **kwargs) -> list[T]:
        """
        Get multiple records by filters, excluding soft-deleted records.
        
        Args:
            session: Database session (uses global if not provided)
            **kwargs: Filter criteria
            
        Returns:
            List of model instances
        """
        if session is None:
            session = get_session()
            should_close = True
        else:
            should_close = False
        
        try:
            # Always exclude soft-deleted records
            query = session.query(cls).filter(
                cls.is_active == True,
                cls.deleted_at == None
            )
            
            # Apply filters
            for key, value in kwargs.items():
                if hasattr(cls, key):
                    query = query.filter(getattr(cls, key) == value)
            
            return query.all()
        finally:
            if should_close:
                close_session(session)

    def soft_delete(self) -> None:
        """Mark record as deleted without removing from database."""
        self.is_active = False
        self.deleted_at = datetime.utcnow()

    def restore(self) -> None:
        """Restore a soft-deleted record."""
        self.is_active = True
        self.deleted_at = None


class User(EntityModel, BaseMixin):
    """User model with soft delete support."""
    __tablename__ = "user"

    nickname = Column(String(50), unique=True, nullable=False)
    avatar = Column(String(255), nullable=True, comment="avatar url")
    email = Column(String(120), unique=True, nullable=True)

    def to_dict(self) -> dict[str, Any]:
        """
        Convert model to dictionary, excluding internal attributes.
        
        Returns:
            Dict with only public attributes
        """
        return {
            "id": self.id,
            "nickname": self.nickname,
            "avatar": self.avatar,
            "email": self.email,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<User(id={self.id}, nickname={self.nickname}, email={self.email})>"
