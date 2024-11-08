from sqlmodel import create_engine, SQLModel, Session
from logger import get_logger
from config import DATABASE_URL
import time 

logger = get_logger(__name__)

engine = create_engine(DATABASE_URL)

def create_db_and_tables():
    
    # wait db warming up
    time.sleep(15)

    SQLModel.metadata.create_all(engine)

def get_db_session():
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()




