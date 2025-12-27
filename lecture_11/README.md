# AWS Infrastructure Automation (Boto3)

Simple Python project to deploy a 3-tier AWS architecture (VPC, EC2, RDS) using Boto3.

## 🚀 Setup

1. **Install Dependencies**
   ```bash
   poetry install
   ```

2. **Configure Credentials**
   Create a `.env` file in this folder:
   ```ini
   aws_access_key_id=YOUR_ACCESS_KEY
   aws_secret_access_key=YOUR_SECRET_KEY
   aws_session_token=YOUR_SESSION_TOKEN
   aws_region_name=us-east-1
   ```

## 🏃‍♂️ Usage

Run the main script to build everything:

```bash
python main.py
```

## 📂 Files
- **`main.py`**: Entry point. Change resource names here.
- **`vpc.py`, `ec2.py`, `rds.py`**: Helper functions for AWS resources.
