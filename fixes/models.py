"""Database models used by the fixed user module."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from .extensions import db


class TimestampMixin:
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )


class SoftDeleteMixin:
    deleted_at = Column(DateTime, nullable=True)

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None


class User(db.Model, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    nickname = Column(String(50), nullable=False, unique=True)
    avatar = Column(String(255), nullable=True)
    email = Column(String(120), nullable=False, unique=True)
    is_active = Column(Boolean, nullable=False, server_default="1")

    avatar_logs = relationship("UserAvatarLog", back_populates="user")

    def to_profile_dict(self) -> dict:
        return {
            "id": self.id,
            "nickname": self.nickname,
            "avatar": self.avatar,
            "email": self.email,
            "is_active": bool(self.is_active),
        }


class UserAvatarLog(db.Model, TimestampMixin):
    __tablename__ = "user_avatar_log"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    avatar = Column(String(255), nullable=False)
    changed_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    user = relationship("User", back_populates="avatar_logs")

