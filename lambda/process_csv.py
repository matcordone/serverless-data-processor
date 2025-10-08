import csv
import io
import logging
import os
from pathlib import Path
from typing import Iterable, Optional

import boto3


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """
    Lambda entry point triggered by an S3 `ObjectCreated` event.
    It downloads the CSV uploaded to the input bucket, filters rows where the salary
    column is greater than 1000, and writes a minimal CSV with name + salary to the
    output bucket.
    """
    s3 = boto3.client("s3")

    record = event["Records"][0]
    source_bucket = record["s3"]["bucket"]["name"]
    source_key = record["s3"]["object"]["key"]
    output_bucket = os.environ["OUTPUT_BUCKET"]

    logger.info("Processing file s3://%s/%s", source_bucket, source_key)

    try:
        response = s3.get_object(Bucket=source_bucket, Key=source_key)
        csv_body = response["Body"].read().decode("utf-8")
    except Exception as exc:
        logger.exception("Failed to download object %s from bucket %s", source_key, source_bucket)
        raise exc

    rows = list(csv.DictReader(io.StringIO(csv_body)))
    if not rows:
        logger.warning("Uploaded CSV is empty; nothing to process.")
        return {"status": "empty_csv"}

    salary_column = _detect_column(rows[0].keys(), {"salary", "salario", "income", "sueldos", "wage"})
    if salary_column is None:
        message = "The uploaded CSV does not contain a salary column."
        logger.error(message)
        raise ValueError(message)

    name_column = _detect_column(rows[0].keys(), {"name", "nombre", "employee", "persona"})

    filtered_rows = []
    for row in rows:
        salary_value = _parse_salary(row.get(salary_column))
        if salary_value is not None and salary_value > 1000:
            entry = {"salary": salary_value}
            if name_column:
                entry["name"] = row.get(name_column, "").strip()
            filtered_rows.append(entry)

    logger.info("Filtered dataset contains %d rows out of %d", len(filtered_rows), len(rows))

    if not filtered_rows:
        logger.info("No rows matched the salary criteria; skipping upload.")
        return {"status": "no_results"}

    target_key = _build_output_key(source_key)
    output_buffer = io.StringIO()

    fieldnames = ["name", "salary"] if name_column else ["salary"]
    writer = csv.DictWriter(output_buffer, fieldnames=fieldnames)
    writer.writeheader()
    for row in filtered_rows:
        writer.writerow(row)

    try:
        s3.put_object(
            Bucket=output_bucket,
            Key=target_key,
            Body=output_buffer.getvalue().encode("utf-8"),
            ContentType="text/csv",
        )
    except Exception as exc:
        logger.exception("Failed to upload filtered CSV to s3://%s/%s", output_bucket, target_key)
        raise exc

    logger.info("Filtered CSV successfully stored at s3://%s/%s", output_bucket, target_key)
    return {"status": "success", "output_key": target_key}


def _detect_column(columns: Iterable[str], known_labels: set[str]) -> Optional[str]:
    """Return the first column name matching any of the expected labels."""
    for column in columns:
        if column and column.strip().lower() in known_labels:
            return column
    return None


def _parse_salary(raw_value: Optional[str]) -> Optional[float]:
    """Convert the salary column to float, handling thousands separators and blank cells."""
    if raw_value is None:
        return None
    cleaned = raw_value.strip().replace(",", "")
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except ValueError:
        logger.warning("Unable to parse salary value '%s'; skipping row.", raw_value)
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
