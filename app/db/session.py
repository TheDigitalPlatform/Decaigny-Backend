from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings
 
# Create SQLAlchemy engine
engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
 
# Create sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
 
# Create declarative base
Base = declarative_base()
 
# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
 