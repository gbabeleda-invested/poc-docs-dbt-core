from dagster import EnvVar # Use like os.getenv() but during runtime
from dagster_aws.s3 import S3Resource
# from dagster_postgres import 


poc_s3_resource = S3Resource(
    aws_access_key_id=EnvVar("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=EnvVar("AWS_SECRET_ACCESS_KEY"),
    region_name="us-east-1"
)

