from pathlib import Path
import sys
import pandas as pd
import os 
from github import Github
import logging 
from dotenv import load_dotenv

root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from utilities.database_functions import establish_db_connection, text, Engine
from utilities.logger_config import setup_logger
from data_catalog.queries import HIGH_LEVEL_QUERIES, DETAIL_QUERIES

load_dotenv()

logger = logging.getLogger(__name__)

def get_db_metadata(
        engine: Engine, 
        query_type: str = "high_level",
        object_type: str = "schema"
    ) -> pd.DataFrame:
    """
    Fetches metadata about database objects based on query type and object type.
    
    Args:
        engine: SQLAlchemy engine connection
        query_type: Either 'high_level' or 'detail'
        object_type: Type of object to get metadata for (schema, table, view, function)
    
    Returns:
        DataFrame containing the requested metadata
    """
    try:
        queries = HIGH_LEVEL_QUERIES if query_type == "high_level" else DETAIL_QUERIES

        if object_type not in queries:
            raise ValueError(f"Invalid object_type: {object_type}. Must be one of {list(queries.keys())}")

        query = queries[object_type]

        with engine.connect() as conn:
            return pd.read_sql_query(text(query), conn)

    except Exception as e:
        logger.error(f"Something went wrong in extracting db catalog to dataframe: {str(e)}")
        raise

def format_for_markdown(df: pd.DataFrame, object_type: str, query_type: str = "high_level") -> str:
    """
    Formats a DataFrame into markdown based on object type
    """
    content = ""
    
    if object_type == "schema":
        content = "# Database Schema Overview\n\n"
        content += "| Schema | Owner | Tables | Views | Functions |\n"
        content += "|--------|-------|---------|--------|------------|\n"
        
        for _, row in df.iterrows():
            content += f"| {row['schema_name']} | {row['owner']} | {row['table_count']} | {row['view_count']} | {row['function_count']} |\n"
    
    elif object_type == "table":
        if query_type == "high_level":
            content = "# Database Tables\n\n"
            current_schema = None
            
            for _, row in df.iterrows():
                if current_schema != row['schema']:
                    current_schema = row['schema']
                    content += f"\n## Schema: {current_schema}\n\n"
                    content += "| Table | Owner | Has Indexes | Has Rules | Has Triggers |\n"
                    content += "|-------|--------|-------------|------------|---------------|\n"
                
                content += f"| {row['table_name']} | {row['owner']} | {row['has_indexes']} | {row['has_rules']} | {row['has_triggers']} |\n"

        else:
            content = "# Table Details\n\n"
            current_schema = None
            current_table = None
            current_owner = None
            
            for _, row in df.iterrows():
                if current_schema != row['schema'] or current_table != row['table_name']:
                    current_schema = row['schema']
                    current_table = row['table_name']
                    current_owner = row['owner']
                    content += f"\n## {current_schema}.{current_table}\n\n"
                    content += f"**Owner:** {current_owner}\n\n"
                    content += "| Column | Type | Nullable | Default |\n"
                    content += "|--------|------|----------|----------|\n"
                
                content += f"| {row['column_name']} | {row['data_type']} | {row['is_nullable']} | {row['column_default']} |\n"            
    
    elif object_type == "view":
        content = "# Database Views\n\n"
        current_schema = None
        
        for _, row in df.iterrows():
            if current_schema != row['schema']:
                current_schema = row['schema']
                content += f"\n## Schema: {current_schema}\n\n"
                content += "| View Name | Type | Owner | Definition |\n"
                content += "|-----------|------|-------|------------|\n"
            
            # Format the definition with proper escaping and code block
            sql_def = row['definition'].replace('\n', '<br>').replace('|', '\\|')
            content += f"| {row['view_name']} | {row['view_type']} | {row['owner']} | <pre>{sql_def}</pre> |\n"

    elif object_type == "function":
        content = "# Database Functions\n\n"
        current_schema = None
        
        for _, row in df.iterrows():
            if current_schema != row['schema']:
                current_schema = row['schema']
                content += f"\n## Schema: {current_schema}\n\n"
                content += "| Function Name | Type | Owner | Arguments | Returns | Definition |\n"
                content += "|---------------|------|--------|-----------|----------|------------|\n"
            
            # Format the definition with proper escaping and code block
            sql_def = row['definition'].replace('\n', '<br>').replace('|', '\\|') if row['definition'] else ''
            
            content += (f"| {row['function_name']} | {row['function_type']} | {row['owner']} | "
                    f"{row['arguments']} | {row['return_type']} | <pre>{sql_def}</pre> |\n")
    
    return content


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


# We will use GitHub Actions to do GitHub things instead of writing python for it
# def update_github_wiki(
#     gh_token: str,
#     repo_name: str,
#     page_name: str,
#     content: str 
# ) -> None:
#     """
#     Updates or creates a GitHub wiki page
#     """
#     # TO DO: Implement Markdown formatting logic for each object type
#     pass




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

        for obj_type in HIGH_LEVEL_QUERIES.keys():
            df = get_db_metadata(engine, "high_level", obj_type)
            content = format_for_markdown(df, obj_type, "high_level")
            save_to_file(content, f"{obj_type}_overview")

        for obj_type in DETAIL_QUERIES.keys():
            df = get_db_metadata(engine, "details", obj_type)
            content = format_for_markdown(df, obj_type, "details")            
            save_to_file(content, f"{obj_type}_details")
            
        logger.info("Successfully generated all documentation files")

    except Exception as e:
        logger.error(f"Something went wrong in the data catalog function: {str(e)}")
        sys.exit(1)