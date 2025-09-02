from sqlalchemy import create_engine
from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker, declarative_base
import os

load_dotenv() 
uri = os.getenv("database_uri")

if not uri:
    raise ValueError("Database URI is not set in environment variables.")

engine = create_engine(uri, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()