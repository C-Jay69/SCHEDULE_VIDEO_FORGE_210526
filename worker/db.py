import os
import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add api to path for models
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api"))

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://videoforge:videoforge_secret@postgres:5432/videoforge")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db_session():
    return SessionLocal()
