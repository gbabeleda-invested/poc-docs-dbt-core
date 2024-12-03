# Data Platform POC Auto-Documentation

This repository demonstrates an automated data documentation system using GitHub Wiki and GitHub Pages as data catalogs. It integrates AWS infrastructure, dbt for transformations, and Dagster for extraction/loading/orchestration and as a platform central tool

### [DBT Doc Site](https://gbabeleda-invested.github.io/poc-docs-dbt-core/#!/overview)

### Next Steps
- Automate DBT Docs site -> GitHub Pages via GitHub Actions
- Do a manual run of data warehouse documentation -> GitHub Wiki
- Automate data warehouse documentation -> GitHub Wiki




# Project Structure 
```
root/
├── .nojekyll              # Prevents GitHub Pages from using Jekyll processing
├── docs/                  # Generated DBT documentation
│   ├── catalog.json       # DBT catalog information
│   ├── graph.gpickle     # DAG visualization data
│   ├── index.html        # Main documentation page
│   └── manifest.json     # DBT manifest information
├── dagster_poc/
│   └── dagster_poc/            
│       ├── assets.py          # Dagster asset definitions
│       ├── resources.py       # Resource configurations
│       └── definitions.py     # Dagster job definitions
├── dbt_poc/
│   ├── models/
│   │   ├── base_models.sql    # Base dbt models
│   │   └── report_models.sql  # Reporting dbt models
│   ├── dbt_project.yml       # DBT project configuration
│   └── packages.yml          # DBT package dependencies
└── README.md                 # Project documentation
```

# Documentation Setup
## DBT
### Generate DBT documentation locally

```bash
cd dbt_poc
dbt docs generate
```

This creates the following files in the `target/` directory
- `catalog.json`: Contains information about database objects
- `manifest.json`: Contains information about your DBT project
- `graph.gpickle`: Contains DAG visualization data
- `index.html`: Main documentation interface

Create GitHub Pages Directory
```bash
mkdir docs
cp dbt_poc.target* docs/
```

Prevent Jekyll Processing
```bash
touch .nojekyll
```

Configure GitHub Pages
- Go to repository Settings -> Pages
- Set Source to "Deploy from a branch"
- Select `main` branch
- Set folder to `/docs`
- Commit and push changes

### Generate DBT Documentation automatically via GitHub Actions

Facing some issue w/ Security Group stuff for AWS during `dbt debug`. Opening up RDS to all traffic temporarily.

In production for `dataops` need to add
- `SSH_PRIVATE_KEY`
- `SSH_HOST`
- `SSH_USER`

## Data Warehouse

WIP



# Infrastructure and Development Setup
### Virtual Environment
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Unix
python -m venv venv
source venv/bin/activate
```

### AWS Infrastructure setup
Account Setup
- Create AWS root acc w/ work email
- Create IAM user w/ following permissions:
    - AmazonRDSFullAccess
    - AmazonS3FullAccess
    - IAMUserChangePassword
    - AmazonEC2FullAccess
- Generate Acces Key for local development

AWS CLI Configuration
```bash
aws configure # Use IAM user credentials
```

Resource Creation
```bash
# Create S3 bucket
aws s3 mb s3://bucket-name --region us-east-1

# Create RDS PostgreSQL instance
aws rds create-db-instance `
    --db-instance-identifier "db-name" `
    --db-instance-class "db.t3.micro" `
    --engine "postgres" `
    --master-username "db_user" `
    --master-user-password "db_password" `
    --allocated-storage 20 `
    --publicly-accessible `
    --port 5432
```

Security Configuration
```bash
# Get IP Address
Invoke-RestMethod ifconfig.me/ip

# Configure Security Group
aws ec2 authorize-security-group-ingress `
    --group-id sg-somestring `
    --protocol tcp `
    --port 5432 `
    --cidr "YOUR_IP_ADDRESS/32"
```
- You can confirm this works programatically and through a platform like pgAdmin4

### DBT Setup
Initial Configuration
```bash
dbt init
```
- Creates profiles.yml in `~/.dbt/`
- Run `dbt debug` to validation connection
- Modify `profiles.yaml` to setup `dev` and `prod`

Project Dependencies (Optional): Add following to `packages.yaml`
```yaml
packages:
  - package: dbt-labs/audit_helper
    version: 0.10.0
  - package: dbt-labs/dbt_utils
    version: 1.1.1
  - package: dbt-labs/codegen
    version: 0.12.1
```

Data Models
- Source: `public.events_table`  
- Base Model: `dbt.base_events`
- Report Models:
    - `dbt.marketing_report`
    - `dbt.finance_report`

### Dagster Setup
Project Creation
```bash
dagster project scaffod --name dagster_poc
```

Dagster Dependency Management
- Done via pyproject.toml to be in line with modern best practices
```toml
[project]
name = "dagster_poc"
version = "0.1.0"
description = "Were using dagster 1.9 so dependencies will be handled here"
readme = "README.md"
requires-python = ">=3.9,<3.13"
dependencies = [
    "dagster==1.9",
    "dagster-cloud",
    "dagster-aws",
    "dagster-dbt",
    "dagster-postgres",
    "boto3",
    "pandas",
    "psycopg2-binary",
    "sqlalchemy",
    "python-dotenv"
]

[project.optional-dependencies]
dev = [
    "dagster-webserver", 
    "pytest",
]

[build-system]
requires = ["setuptools"]
build-backend = "setuptools.build_meta"

[tool.dagster]
module_name = "dagster_poc.definitions"
code_location_name = "dagster_poc"
```

Install Development Dependencies
```bash
pip install -e ".[dev]"
```

## Data Pipeline Integration
### Events Table
- Generated and populated entirey via Dagster using S3 and RDS

### DBT Models Configuration
- Profiles point at either `dev` or `prod`
- All models are just views

```yaml
# profiles.yaml
dbt_poc:
  outputs:
    dev:
      dbname: some_dbname
      host: some_host
      pass: some_pass
      port: some_port
      schema: some_schema
      threads: some_thread
      type: postgres
      user: some_user
    prod:
        # same as above
  target: prod

# dbt_project.yaml
models:
  dbt_poc:
    +materialized: view
```

### Dagster-DBT Integration
Loading DBT models as Dagster Assets
- Point to the DBT Project and turn it into an object
- Associate DBT Project object with DBT Resource
- Use DBT Project object with DBT assets decorator to load all models as assets

```python
# resources.py
from pathlib import Path
from dagster_dbt import DbtCliResource, DbtProject

DBT_PROJECT_DIR = Path(__file__).parent.parent.parent / "dbt_poc"
DBT_PROFILES_DIR = Path.home() / ".dbt"

dbt_project = DbtProject(
    project_dir=str(DBT_PROJECT_DIR)
)

dbt_resource = DbtCliResource(
    project_dir=dbt_project,
    profiles_dir=str(DBT_PROFILES_DIR)
)

# assets.py
@dbt_assets(
    manifest=dbt_project.manifest_path,
)
def dbt_project_assets(context: AssetExecutionContext, dbt: DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()
```


Upstream Dependencies
- Need to associate proper metadata to pure dagster upstream assets in  `sources.yaml`
```yaml
# sources.yml
sources:
  - name: dagster
    schema: public
    tables:
      - name: events_table
        description: Raw platform transactions data from daily CSV loads
        meta:
          dagster:
            asset_key: ["events_table"]
        columns:
          - name: event_id
            description: Unique identifier for each event
``` 

## Development Tools
- DBT Power User (VS Code Extension)
- AWS CLI
- Dagster UI for debugging