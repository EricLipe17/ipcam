from app.settings.local import settings

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

db_config = settings.db_config
db_url = f"postgres://{db_config["POSTGRES_USER"]}:{db_config["POSTGRES_PASSWORD"]}@{db_config["POSTGRES_HOST"]}:{db_config["POSTGRES_PORT"]}/{db_config["POSTGRES_DB"]}"

engine = create_engine(db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
