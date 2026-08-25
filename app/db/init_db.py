import logging
from app.db.session import engine, SessionLocal
from app.models.base import Base
import app.models  # noqa: F401 — registers all models with Base metadata
from app.db.seed_db import seed_db

logger = logging.getLogger(__name__)


def init_db(seed: bool = False) -> None:
    """
    Initialize the database.

    Args:
        seed: If True, seed the database with initial data after creating tables
    """
    try:
        # Base.metadata.create_all(bind=engine)
        logger.info("Tables created successfully.")

        if seed:
            db = SessionLocal()
            try:
                seed_db(db)
                logger.info("Database seeded successfully.")
            except Exception as e:
                logger.error(f"Error seeding database: {e}")
                raise
            finally:
                db.close()
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise
 