import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.user import Base

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://user:password@db:3306/outsource_db"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
