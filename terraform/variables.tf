variable "bucekt_name_input" {
  description = "Name of the input S3 bucket"
  type        = string
}

variable "bucket_name_output" {
  description = "Name of the output S3 bucket"
  type        = string
}

variable "function_name" {
  description = "Name of the Lambda function"
  type        = string
}

variable "runtime" {
  description = "Runtime environment for the Lambda function"
  type        = string
}

variable "handler" {
  description = "Handler for the Lambda function"
  type        = string
}

variable "statement_id" {
  description = "Statement ID for Lambda permission"
  type        = string
}

variable "region" {
  description = "AWS region"
  type        = string 
}

variable "version" {
  description = "Version of the AWS provider"
  type        = string
}