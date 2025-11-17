from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base, scoped_session
from fixes.config import config
from datetime import datetime

engine = create_engine(config.SQLALCHEMY_DATABASE_URI, connect_args={"check_same_thread": False})
SessionLocal = scoped_session(sessionmaker(bind=engine))
Base = declarative_base()

class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    nickname = Column(String(50), unique=True, nullable=False)
    avatar = Column(String(255))
    email = Column(String(120), unique=True)
    is_active = Column(Boolean, default=True)
    deleted_at = Column(DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "nickname": self.nickname,
            "avatar": self.avatar,
            "email": self.email,
            "is_active": self.is_active,
        }

def init_db():
    Base.metadata.create_all(bind=engine)

# helper to get session
def get_session():
    return SessionLocal()
