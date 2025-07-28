from sqlmodel import create_engine, SQLModel
from app.core.config import get_settings

settings = get_settings()

engine = create_engine(settings.database_url, echo=True)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
