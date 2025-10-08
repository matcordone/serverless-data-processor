resource "aws_s3_bucket" "input_bucket" {
  bucket = var.bucekt_name_input

  tags = {
    Name        = "InputBucket"
    Environment = "test"
  }
}

resource "aws_s3_bucket" "output_bucket" {
  bucket = var.bucket_name_output

  tags = {
    Name        = "OutputBucket"
    Environment = "test"
  }
}

resource "aws_s3_bucket_policy" "lambda_access_policy_input" {
  bucket = aws_s3_bucket.input_bucket.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowLambdaS3Access"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject"
        ]
        Resource = [
          "${aws_s3_bucket.input_bucket.arn}/*"
        ]
        Principal = {
            AWS = "${aws_iam_role.lambda_execution_role.arn}"
        }
      }
    ]
  })

}
resource "aws_s3_bucket_policy" "lambda_access_policy_output" {
  bucket = aws_s3_bucket.output_bucket.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowLambdaS3Access"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject"
        ]
        Resource = [
          "${aws_s3_bucket.output_bucket.arn}/*"
        ]
        Principal = {
            AWS = "${aws_iam_role.lambda_execution_role.arn}"
        }
      }
    ]
  })

}

resource "aws_s3_bucket_notification" "trigger" {
    bucket = aws_s3_bucket.input_bucket.id
    lambda_function {
        lambda_function_arn = aws_lambda_function.process_csv.arn
        events = ["s3:ObjectCreated:*"]      
    }
}