import os
from dotenv import load_dotenv
from datetime import date
from pathlib import Path
import sys

import pandas as pd

from dagster import asset, AssetExecutionContext
from dagster_aws.s3 import S3Resource
from dagster_dbt import DbtCliResource, dbt_assets

# Add utilities to Python path
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))  # Insert at beginning of path

from utilities.database_functions import establish_db_connection, text
from .resources import poc_s3_resource, dbt_project

load_dotenv()


bucket_name = "gio-poc-docs-bucket"
test_csv = "platform_transactions.csv"
schema = "public"
table = "events_table"


@asset
def daily_platform_transactions(
    context: AssetExecutionContext, 
    s3: S3Resource = poc_s3_resource
) -> pd.DataFrame:
    """
    The CSV in the S3 bucket
    """
    try:
        obj = s3.get_client().get_object(
            Bucket=bucket_name,
            Key=test_csv
        )

        df = pd.read_csv(obj["Body"])
        context.log.info("Sucessfully read the platform transaction cSV")

        return df

    except Exception as e:
        context.log.error(f"Failed to turn S3 CSV into DF: {str(e)}")
        raise

@asset() # dont use deps here because we insert as parameter
def events_table(
    context: AssetExecutionContext,
    daily_platform_transactions: pd.DataFrame
) -> None:
    """
    
    """
    try:
        engine = establish_db_connection(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT')         
        )

        create_if_not_exist = f"""
        create table if not exists {schema}.{table} (
            transaction_id INT,
            purchase_price FLOAT,
            product_value FLOAT,
            product_name TEXT,
            first_name TEXT,
            last_name TEXT,
            email TEXT,
            gender TEXT,
            customer_country TEXT,
            client_country TEXT,
            transaction_date DATE            
        )
        """

        with engine.begin() as conn:
            conn.execute(text(create_if_not_exist))
            context.log.info(f"{schema}.{table} exists")

        daily_platform_transactions["transaction_date"] = date.today()

        with engine.begin() as conn:
            daily_platform_transactions.to_sql(
                name=table,
                schema=schema,
                con=conn,
                if_exists="append",
                index=False
            )

        context.log.info(f"Successfully uploaded to the table: {len(daily_platform_transactions)} rows")


    except Exception as e:
        context.log.error(f"Something went wrong with creating/uploading to events table: {str(e)}")
        raise

@dbt_assets(
        manifest=dbt_project.manifest_path,
)
def dbt_project_assets(
    context: AssetExecutionContext,
    dbt: DbtCliResource
):
    yield from dbt.cli(["build"], context=context).stream()