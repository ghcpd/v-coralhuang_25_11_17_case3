from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, scoped_session, sessionmaker

Base = declarative_base()


class Database:
    def __init__(self, url: str):
        self.engine = create_engine(url, future=True)
        self.SessionLocal = scoped_session(sessionmaker(bind=self.engine, future=True))

    def create_all(self) -> None:
        Base.metadata.create_all(bind=self.engine)

    @contextmanager
    def session_scope(self, commit: bool = True):
        session = self.SessionLocal()
        try:
            yield session
            if commit:
                session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
