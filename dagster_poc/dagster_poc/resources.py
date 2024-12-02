from pathlib import Path

from dagster import EnvVar # Use like os.getenv() but during runtime
from dagster_aws.s3 import S3Resource
from dagster_dbt import DbtCliResource, DbtProject


poc_s3_resource = S3Resource(
    aws_access_key_id=EnvVar("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=EnvVar("AWS_SECRET_ACCESS_KEY"),
    region_name="us-east-1"
)


DBT_PROJECT_DIR = Path(__file__).parent.parent.parent / "dbt_poc"
DBT_PROFILES_DIR = Path.home() / ".dbt" # points to C:\Users\gioab\.dbt

dbt_project = DbtProject(
    project_dir=str(DBT_PROJECT_DIR)
)


dbt_resource = DbtCliResource(
    project_dir=dbt_project,
    profiles_dir=str(DBT_PROFILES_DIR) 
)