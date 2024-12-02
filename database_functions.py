import logging
import os
import sys
from dotenv import load_dotenv

from sqlalchemy import create_engine, text, Engine
from sqlalchemy.exc import SQLAlchemyError
from urllib.parse import quote_plus

from logger_config import setup_logger

load_dotenv()

logger = logging.getLogger(__name__)

def establish_db_connection(
        host: str,
        database: str, 
        user: str,
        password: str,
        port: str = "5432"
) -> Engine:
    """
    Establish connection to a postgresql database using sqlalchemy
    """

    try: 
        escaped_user = quote_plus(user)
        escaped_password = quote_plus(password)

        connection_string = f"postgresql://{escaped_user}:{escaped_password}@{host}:{port}/{database}"

        engine = create_engine(
            connection_string,
            pool_pre_ping=True, # Verify connection before using
            pool_size=5,        # Set pool size
            pool_recycle=3600,  # Recycle connections hourly
            max_overflow=10     # Allow extra connections
        )

        with engine.connect() as conn:
            conn.execute(text("select 1"))
            logger.info(f"Data base connection established to {user}@{host}:{port}/{database}")

        return engine
    
    except SQLAlchemyError as e:
        logger.error(f"Failed to establish connection to {user}@{host}:{port}/{database}")
        raise


if __name__ == "__main__":
    setup_logger()

    try:
        engine = establish_db_connection(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT')
        )

    except Exception as e:
        logger.error(f"Something went wrong in the db function: {str(e)}")
        sys.exit(1)

    