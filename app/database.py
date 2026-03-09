import os
import time
import logging
from psycopg2.pool import ThreadedConnectionPool
from psycopg2 import OperationalError
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

pool: ThreadedConnectionPool = None


def init_db(retries: int = 5, delay: int = 2) -> None:
    """Initialize connection pool with retry logic for container startup race."""
    global pool
    database_url = os.getenv("DATABASE_URL")
    for attempt in range(retries):
        try:
            pool = ThreadedConnectionPool(
                minconn=1,
                maxconn=10,
                dsn=database_url
            )
            logger.info("Database connection pool initialized successfully")
            return
        except OperationalError as e:
            logger.warning(f"Database not ready, attempt {attempt + 1}/{retries}. Retrying in {delay}s...")
            time.sleep(delay)
    raise RuntimeError("Could not connect to the database after multiple retries")


def get_connection():
    """Borrow a connection from the pool."""
    return pool.getconn()


def release_connection(conn) -> None:
    """Return a connection back to the pool."""
    pool.putconn(conn)


def close_pool() -> None:
    """Close all connections in the pool on app shutdown."""
    if pool:
        pool.closeall()
        logger.info("Database connection pool closed")