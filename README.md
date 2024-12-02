# POC Autodocumentation

This is a simple repository that aims to showcase the viability of using github wiki and github pages as data catalogs 

## Virtual Env
- Windows: `python -m venv venv` -> `.\venv\Scripts\activate`
- Unix: `python -m  venv venv` -> `source venv/bin/activate`

## AWS Setup

- Created new AWS root account using work email
- Created IAM User
    - User details
    - Permissions Options: Attach policies directly
        - AmazonRDSFullAccess
        - AmazonS3FullAccess
        - IAMUserChangePassword
- Created access key
    - Local code
    - Description tag
- Setup AWS CLI on Windows
- Use IAM user on AWS CLI using `aws configure`
- Spun up S3 bucket using aws cli: `aws s3 mb s3://bucket-ame --region us-east-1`
- Spun up RDS Postgres using aws cli:
```bash
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
- Get IP address: `Invoke-RestMethod ifconfig.me/ip`
- Authorize access to IP via security group:
```
aws ec2 authorize-security-group-ingress `
    --group-id sg-somestring `
    --protocol tcp `
    --port 5432 `
    --cidr "YOUR_IP_ADDRESS/32"
```
- Can confirm this works using the `establish_db_connection()` function

## DBT Setup
