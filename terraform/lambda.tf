resource "aws_lambda_function" "process_csv" {
    function_name = var.function_name
    role = aws_iam_role.lambda_execution_role.arn
    handler = var.handler
    runtime = var.runtime
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
    statement_id = var.statement_id
    action = "lambda:invokeFunction"
    function_name = aws_lambda_function.process_csv.function_name
    principal = "s3.amazonaws.com"
    source_arn = "${aws_s3_bucket.input_bucket.arn}"
  
}

data "archive_file" "lambda_zip" {
    type        = "zip"
    source_file = var.source_file
    output_path = var.output_path
}