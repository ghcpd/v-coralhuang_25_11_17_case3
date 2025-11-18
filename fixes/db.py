import os
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, func, text
from sqlalchemy.orm import sessionmaker, declarative_base, scoped_session
from sqlalchemy.exc import SQLAlchemyError
import datetime

from .config import config

Base = declarative_base()

# Lazy engine/session creation: engine and session factory will be created on first use
_engine = None
_SessionLocal = None
# Keep engine exported for compatibility; will be set when created
engine = None


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


def _get_engine():
    global _engine, engine
    # Determine current desired URL from env or config
    db_url = os.getenv("DATABASE_URL") or config.SQLALCHEMY_DATABASE_URI
    if _engine is None:
        print(f"[db] creating engine for db_url={db_url}")
        _engine = create_engine(db_url, echo=False)
        engine = _engine
        return _engine
    # If the env var changed since the engine was created, recreate engine
    try:
        current_url = str(_engine.url)
    except Exception:
        current_url = None
    if current_url != db_url:
        print(f"[db] db_url changed from {current_url} to {db_url}, recreating engine")
        _engine = create_engine(db_url, echo=False)
        engine = _engine
    return _engine


def _get_session_factory():
    global _SessionLocal, _engine
    db_url = os.getenv("DATABASE_URL") or config.SQLALCHEMY_DATABASE_URI
    # recreate session factory if engine changed (db_url changed)
    if _SessionLocal is None:
        engine = _get_engine()
        _SessionLocal = scoped_session(sessionmaker(bind=engine))
        return _SessionLocal
    try:
        engine_url = str(_engine.url) if _engine is not None else None
    except Exception:
        engine_url = None
    if engine_url != db_url:
        # recreate backing engine and session factory
        engine = _get_engine()
        _SessionLocal = scoped_session(sessionmaker(bind=engine))
    return _SessionLocal


def init_db():
    # In test mode, and when using a sqlite file, ensure we recreate the file so tests start with a clean DB
    db_url = os.getenv("DATABASE_URL") or config.SQLALCHEMY_DATABASE_URI
    if os.getenv("FLASK_ENV") == "test" and db_url.startswith("sqlite:///"):
        # Remove the existing sqlite file if present BEFORE creating engine
        path = db_url.replace("sqlite:///", "")
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass
    engine = _get_engine()
    Base.metadata.create_all(bind=engine)


def db_session():
    """Provide a session context manager."""
    session_factory = _get_session_factory()
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


# For tests & celery usage
def get_session():
    sf = _get_session_factory()
    try:
        print(f"[db] get_session using engine url={_engine.url if _engine is not None else None}")
    except Exception:
        pass
    return sf()
