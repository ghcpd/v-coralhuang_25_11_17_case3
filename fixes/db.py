from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, func, text
from sqlalchemy.orm import sessionmaker, declarative_base, scoped_session
from sqlalchemy.exc import SQLAlchemyError
import datetime

from .config import config

Base = declarative_base()

engine = create_engine(config.SQLALCHEMY_DATABASE_URI, echo=False)
SessionLocal = scoped_session(sessionmaker(bind=engine))


class EntityModel(Base):
    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    @classmethod
    def get(cls, session, **kwargs):
        return session.query(cls).filter_by(**kwargs).first()

    def to_dict(self):
        data = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        # filter out datetimes
        for k, v in data.items():
            if isinstance(v, datetime.datetime):
                data[k] = v.isoformat()
        return data


def init_db():
    Base.metadata.create_all(bind=engine)


def db_session():
    """Provide a session context manager."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


# For tests & celery usage
def get_session():
    return SessionLocal()
