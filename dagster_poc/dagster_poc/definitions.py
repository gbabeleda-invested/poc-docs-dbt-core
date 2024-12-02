from dagster import Definitions, load_assets_from_modules

from . import assets  # noqa: TID252
from .resources import poc_s3_resource, dbt_resource

all_assets = load_assets_from_modules([assets])

defs = Definitions(
    assets=all_assets,
    resources={
        "s3" : poc_s3_resource,
        "dbt" : dbt_resource
    }
)
