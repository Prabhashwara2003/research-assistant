from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Session

from app.core.config import settings


engine = create_engine(
    url  = settings.database_url,
    connect_args= {"check_same_thread" :False})
    
SessionLocal = sessionmaker(
    bind =engine,
    autoflush=False,
    expire_on_commit=False
    )

class Base(DeclarativeBase):
    pass

def get_db():
    database : Session = SessionLocal()
    
    try:
        yield database
    finally:
        database.close()
    