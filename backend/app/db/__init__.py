import app.db.models
from app.settings.local import settings

from fastapi import Depends
from sqlalchemy import create_engine
from sqlmodel import Session, SQLModel, create_engine
from typing import Annotated

db_config = settings.db_config
db_url = f"postgresql://{db_config["POSTGRES_USER"]}:{db_config["POSTGRES_PASSWORD"]}@{db_config["POSTGRES_HOST"]}:{db_config["POSTGRES_PORT"]}/{db_config["POSTGRES_DB"]}"

engine = create_engine(db_url)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


DBSession = Annotated[Session, Depends(get_session)]
