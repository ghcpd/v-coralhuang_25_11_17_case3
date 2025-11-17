from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String

from fixes.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    nickname = Column(String(50), nullable=False)
    avatar = Column(String(255), nullable=True)
    email = Column(String(120), unique=True, nullable=True)
    is_active = Column(Boolean, default=True)
    deleted_at = Column(DateTime, nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nickname": self.nickname,
            "avatar": self.avatar,
            "email": self.email,
            "is_active": bool(self.is_active),
        }

    @property
    def is_soft_deleted(self) -> bool:
        return self.deleted_at is not None


class AvatarLog(Base):
    __tablename__ = "user_avatar_log"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    avatar_url = Column(String(255), nullable=False)
    changed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
