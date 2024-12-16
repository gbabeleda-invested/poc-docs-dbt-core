import sys
import os 
import logging 
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import Engine, text

root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from utilities.database_functions import establish_db_connection
from utilities.logger_config import setup_logger
from data_catalog.queries import query_dict
from data_catalog.markdown_functions import generate_home_page, format_for_markdown

load_dotenv()
logger = logging.getLogger(__name__)

def get_db_catalog(
        engine: Engine, 
        catalog_name: str,
        query: str
    ) -> pd.DataFrame:
    """
    Gets a dataframe of a schema/table/view/function data catalog from a postgres database
    
    Args:
        engine: SQLAlchemy engine connection
        catalog_name: Name of the catalog being queried from queries.py
        object_type: AQL query to execute
    
    Returns:
        DataFrame containing the catalog

    Raises:
        Exception: If database query faila
    """
    try:
        with engine.connect() as conn:
            catalog_dataframe = pd.read_sql_query(text(query), conn)
            logger.info(f"Successfully fetched: {catalog_name}")
            return catalog_dataframe

    except Exception as e:
        logger.error(f"Something went wrong in extracting db catalog to dataframe: {str(e)}")
        raise


def save_to_file(content: str, filename: str, directory: str = "catalog_docs") -> None:
    """
    Saves markdown content to a file in the data_dump directory at project root
    
    Args:
        content: Markdown content to save
        filename: Name of the file without extension
        directory: Directory name (relative to project root)
    """
    # Get project root directory (where we see data_dump, docs, etc.)
    root_dir = Path(__file__).parent.parent
    
    # Create data_dump directory if it doesn't exist
    dump_dir = root_dir / directory
    dump_dir.mkdir(parents=True, exist_ok=True)
    
    # Write content to file
    filepath = dump_dir / f"{filename}.md"
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    
    logger.info(f"Written markdown content to {filepath}")


if __name__ == "__main__":

    try:
        setup_logger()
        engine, tunnel = establish_db_connection(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            use_ssh=True,
            ssh_host=os.getenv('BASTION_HOST'),
            ssh_username=os.getenv('BASTION_USER'),
            ssh_private_key=os.getenv('SSH_PRIVATE_KEY'),
            remote_host=os.getenv('DB_HOST')
        )         

        # Generate Home Page
        home_content = generate_home_page(query_dict)
        save_to_file(home_content, "Home") # This will create Home.md


        for catalog_name, query in query_dict.items():
            try:
                catalog_dataframe = get_db_catalog(engine, catalog_name, query)

                content = format_for_markdown(catalog_dataframe, catalog_name)

                save_to_file(content, catalog_name)

            except Exception as e:
                logger.error(f"Failed to process catalog {catalog_name}: {str(e)}")
                raise

    except Exception as e:
        logger.error(f"Something went wrong in the data catalog function: {str(e)}")
        sys.exit(1)

    finally:
        if engine:
            engine.dispose()
        if tunnel:
            tunnel.close()