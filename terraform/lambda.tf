resource "aws_lambda_function" "process_csv" {
    function_name = "process_csv_lambda"
    role = aws_iam_role.lambda_execution_role.arn
    handler = "process_csv.lambda_handler"
    runtime = "python3.13"
    filename = data.archive_file.lambda_zip.output_path
    source_code_hash = data.archive_file.lambda_zip.output_base64sha256
    timeout = 30
    memory_size = 128

    environment {
        variables = {
            INPUT_BUCKET  = aws_s3_bucket.input_bucket.bucket
            OUTPUT_BUCKET = aws_s3_bucket.output_bucket.bucket
        }
    }
}

resource "aws_lambda_permission" "allow_s3_invoke" {
    statement_id = "AllowS3Invoke"
    action = "lambda:invokeFunction"
    function_name = aws_lambda_function.process_csv.function_name
    principal = "s3.amazonaws.com"
    source_arn = "${aws_s3_bucket.input_bucket.arn}"
  
}

data "archive_file" "lambda_zip" {
    type        = "zip"
    source_file = "${path.module}/../lambda/process_csv.py"
    output_path = "${path.module}/../lambda/process_csv.zip"
}