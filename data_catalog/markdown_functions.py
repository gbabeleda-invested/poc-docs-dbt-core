import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

def format_title(text: str) -> str:
    """Convert snake case to Title Case"""
    return " ".join(word.title() for word in text.split("_"))

def generate_home_page(query_dict: dict) -> str:
    """
    Generates the content for the Home.md landing page using the query dictionary keys

    Args: 
        query_dict: Dictionary containing catalog queries

    Returns:
        str: Formatted markdown content for the home page
    """
    content = """# Data Catalog Documentation

Welcome to the Data Catalog! This wiki contains automatically generated documentation about our data warehouse objects.

## Available Documentation

"""
    for catalog_name in query_dict.keys():
        display_name = format_title(catalog_name)
        link_name = catalog_name
        content += f"* [{display_name}]({link_name})\n"
    
    content += """
## Documentation Updates
This documentation is automatically generated and updated whenever changes are pushed to the main branch.
"""
    return content

def format_for_markdown(
    catalog_dataframe: pd.DataFrame,
    catalog_name: str
) -> str:
    """
    Formats a DataFrame into markdown based on object type

    Args:
        catalog_dataframe: DataFrame containing catalog data
        catalog_name: NAme of the catalog being documented

    Returns:
        str: Formatted markdown content

    Raises:
        Exception: If something goes wrong with formatting
    """
    try: 
        catalog_headers = catalog_dataframe.columns 
        header_row = " | ".join(str(header).replace("_", " ").title() for header in catalog_headers)
        separator = "|".join("-" * len(header) for header in catalog_headers)

        content = f"# {format_title(catalog_name)}\n\n"
        content += f"| {header_row} |\n"
        content += f"| {separator} |\n"

        for _, row in catalog_dataframe.iterrows():
            formatted_values = []
            for col, val in row.items():
                if col.lower() == "definition":
                    # Format SQL definitions with line breaks and escape pipes
                    formatted_val = f"<pre>{str(val).replace('\n', '<br>').replace('|', '\\|')}</pre>"
                else:
                    formatted_val = str(val)
                formatted_values.append(formatted_val)

            row_content = " | ".join(formatted_values)
            content += f"| {row_content} |\n"

        return content

    except Exception as e:
        logger.error(f"Something went wrong formatting {catalog_name} to markdown: {str(e)}")
        raise
