# Serverless Data Processor

## Overview
Serverless Data Processor is a Terraform-driven AWS stack that ingests CSV files from an S3 bucket, processes them with a Lambda function, and writes the filtered output to a second bucket. The example Lambda included in this repo keeps rows where the salary field is greater than 1000 USD and emits a compact CSV containing the employee names and their salaries.

Although the bundled function performs salary filtering, you can replace it with any Python handler that makes sense for your workload. The surrounding infrastructure (IAM role, buckets, permissions, deployment workflow) is generic and reusable for other serverless data-processing tasks triggered by S3 uploads.

## Architecture
- **Input bucket** – receives CSV uploads that trigger the Lambda through S3 event notifications.
- **Lambda function** – downloads the uploaded CSV, applies the transformation, and stores the result.
- **Output bucket** – stores processed CSV files under the `filtered/` prefix.
- **IAM role and policies** – grant the Lambda access to S3 and CloudWatch Logs.
- **GitHub Actions workflow** – replaces the input CSV simple via `aws s3 cp`, making it easy to kick off processing through Git pushes.

## Prerequisites
- Terraform v1.3+ (tested with 1.9.x)
- Python 3.10+ for local development (Lambda runtime uses Python 3.13)
- AWS CLI configured with access to deploy S3, Lambda, and IAM resources
- An AWS account with permissions to create the above resources
- GitHub repository secrets `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` if you plan to run the provided workflow

## Initial Setup
1. **Install dependencies (optional):**
   ```bash
   cd lambda
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt  # currently empty because Lambda only needs stdlib
   ```
2. **Zip the Lambda package (Terraform can do this for you via `data "archive_file"` if configured).**
3. **Configure Terraform:**
   ```bash
   cd terraform
   terraform init
   terraform plan
   terraform apply
   ```
   Customise bucket names or regions via `terraform.tfvars`.

## GitHub Actions Workflow
The workflow in `.github/workflows/deply.yml` keeps the input bucket synchronized with `lambda/employees.csv`. On every push to `main` that changes the CSV (or when run manually), the job:
1. Authenticates with AWS using repository secrets.
2. Purges existing files from the input bucket (configurable).
3. Uploads the latest CSV.

This provides a minimal CICD hook for data-driven deployments. You can extend the workflow with linting, packaging, or Terraform deploy steps as needed.

## Customisation
### Replace the Lambda Logic
1. Edit `lambda/process_csv.py` with your own transformation.
2. Update or add any Python dependencies in `lambda/requirements.txt`.
3. Recreate the deployment package or layer.

### Adjust Infrastructure
- Modify bucket prefixes or naming in `terraform/s3.tf`.
- Update IAM permissions in `terraform/iam.tf` if your function needs other services.
- Alter environment variables in `terraform/lambda.tf` to pass custom configuration.

### Workflow Optimisation
- Change the trigger paths or branches in `.github/workflows/deply.yml`.
- Add build steps (tests, zip creation, Terraform apply) before the upload.
- Swap the S3 sync logic for your own pipelines (e.g., AWS CodePipeline, Step Functions).

## Testing Locally
You can simulate the Lambda logic without deploying:
```bash
source lambda/.venv/bin/activate
python lambda/process_csv.py  # wrap logic in a __main__ guard if desired
```
Or mimic the event payload in a simple script and call `lambda_handler` directly.

## Operational Notes
- **Error Handling:** CloudWatch Logs capture any failures. Watch for warnings about missing columns or parsing issues.
- **Scaling:** S3 + Lambda scales automatically. Concurrency limits depend on your AWS account defaults.
- **Costs:** S3 storage, Lambda invocations, and CloudWatch logging incur standard AWS fees.

## Why This Boilerplate?
- Rapid prototype for CSV processing triggered by uploads.
- Infrastructure as Code ensures reproducibility and easy teardown.
- Minimal workflow integration so data updates through Git automatically reach S3.

Feel free to fork it, swap the Lambda for any processing logic you need (image resizing, metadata enrichment, format conversion), or harden the workflow with approvals and artifacts. The core pattern remains the same: S3 events kick off lightweight compute that writes results back to S3. Have fun customising it to your use case!
