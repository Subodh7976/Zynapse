from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from typing import Dict, Any
import os

from .models import Base, Source, Conversation

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set")
engine = create_engine(DATABASE_URL, echo=False, pool_recycle=3600)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_db_and_tables():
    print("Creating database tables (if they don't exist)...")
    try:
        Base.metadata.create_all(bind=engine)
        print("Tables checked/created.")
    except Exception as e:
        print(f"Error creating tables: {e}")
        raise


@contextmanager
def db_session():
    connection = engine.connect()
    session = SessionLocal(bind=connection)

    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
        connection.close()


def create_conversation(conversation: Conversation):
    with db_session() as session:
        session.add(conversation)
    return conversation.id


def get_conversation(conversation_id: int):
    with db_session() as session:
        return session.query(Conversation).filter(Conversation.id == conversation_id).first()


def upload_source(source: Source):
    with db_session() as session:
        session.add(source)
    return source.id


def update_conversation(conversation_id: str, update_data: Dict[str, Any]):
    with db_session() as session:
        conv = session.query(Conversation).filter(
            Conversation.id == conversation_id).first()

        if not conv:
            return

        for key, value in update_data.items():
            if hasattr(conv, key):
                setattr(conv, key, value)

    return conv


def get_source(source_id: str):
    with db_session() as session:
        return session.query(Source).filter(Source.id == source_id).first()


def get_all_source(conversation_id: str):
    with db_session() as session:
        return session.query(Source).filter(Source.conversation_id == conversation_id).all()
