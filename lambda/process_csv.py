import io
import logging
import os
from pathlib import Path

import boto3
import pandas as pd


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """
    Lambda entry point triggered by an S3 `ObjectCreated` event.
    It downloads the CSV uploaded to the input bucket, filters rows where the salary
    column is greater than 1000, and writes the filtered dataset to the output bucket.
    """
    s3 = boto3.client("s3")

    record = event["Records"][0]
    source_bucket = record["s3"]["bucket"]["name"]
    source_key = record["s3"]["object"]["key"]
    output_bucket = os.environ["OUTPUT_BUCKET"]

    logger.info("Processing file s3://%s/%s", source_bucket, source_key)

    try:
        response = s3.get_object(Bucket=source_bucket, Key=source_key)
        csv_body = response["Body"].read()
    except Exception as exc:
        logger.exception("Failed to download object %s from bucket %s", source_key, source_bucket)
        raise exc

    df = pd.read_csv(io.BytesIO(csv_body))

    salary_column = _detect_salary_column(df)
    if salary_column is None:
        message = "The uploaded CSV does not contain a salary column."
        logger.error(message)
        raise ValueError(message)

    filtered_df = df[df[salary_column] > 1000]
    logger.info("Filtered dataset contains %d rows out of %d", len(filtered_df), len(df))

    name_column = _detect_name_column(df)
    if name_column:
        result_df = filtered_df[[name_column, salary_column]].copy()
    else:
        result_df = filtered_df[[salary_column]].copy()
        logger.warning(
            "Name column not found; output CSV will include only the salary column."
        )

    result_df.rename(columns={salary_column: "salary"}, inplace=True)
    if name_column:
        result_df.rename(columns={name_column: "name"}, inplace=True)

    target_key = _build_output_key(source_key)
    csv_buffer = io.StringIO()
    result_df.to_csv(csv_buffer, index=False)

    try:
        s3.put_object(
            Bucket=output_bucket,
            Key=target_key,
            Body=csv_buffer.getvalue().encode("utf-8"),
            ContentType="text/csv",
        )
    except Exception as exc:
        logger.exception("Failed to upload filtered CSV to s3://%s/%s", output_bucket, target_key)
        raise exc

    logger.info("Filtered CSV successfully stored at s3://%s/%s", output_bucket, target_key)


def _detect_salary_column(df: pd.DataFrame) -> str | None:
    """Return the column name representing salary (case-insensitive) or None if not found."""
    known_labels = {"salary", "salario", "income", "sueldos", "wage"}
    for column in df.columns:
        if column.strip().lower() in known_labels:
            return column
    return None


def _detect_name_column(df: pd.DataFrame) -> str | None:
    """Return the column name representing person's name (case-insensitive) or None if not found."""
    known_labels = {"name", "nombre", "employee", "persona"}
    for column in df.columns:
        if column.strip().lower() in known_labels:
            return column
    return None


def _build_output_key(source_key: str) -> str:
    """
    Build the output object key based on the source key.
    Files are placed under the `filtered/` prefix and keep the original name.
    """
    filename = Path(source_key).name
    parent = Path(source_key).parent
    if parent == Path("."):
        return f"filtered/{filename}"
    return str(parent / "filtered" / filename)
