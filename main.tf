terraform {
  required_providers {
	aws = {
	  source  = "hashicorp/aws"
	  version = "~> 4.0.0"
	}
	random = {
	  source  = "hashicorp/random"
	  version = "~> 3.1.0"
	}
	archive = {
	  source  = "hashicorp/archive"
	  version = "~> 2.2.0"
	}
  }

  required_version = "~> 1.0"
}

provider "aws" {
  region = var.aws_region
}

resource "random_pet" "lambda_bucket_name" {
  prefix = "tf-template-generator"
  length = 4
}

resource "aws_s3_bucket" "lambda_bucket" {
  bucket = random_pet.lambda_bucket_name.id

  # acl           = "private"
  force_destroy = true
}

data "archive_file" "lambda_tf_generator" {
  type = "zip"

  source_dir  = "${path.module}/tf-generator"
  output_path = "${path.module}/tf-generator.zip"
}

resource "aws_s3_object" "lambda_tf_generator" {
  bucket = aws_s3_bucket.lambda_bucket.id

  key    = "tf-generator.zip"
  source = data.archive_file.lambda_tf_generator.output_path

  etag = filemd5(data.archive_file.lambda_tf_generator.output_path)
}

resource "aws_lambda_function" "tf-generator" {
  function_name = "tf-generator"

  s3_bucket = aws_s3_bucket.lambda_bucket.id
  s3_key    = aws_s3_object.lambda_tf_generator.key

  runtime = "python3.9"
  handler = "lambda.lambda_handler"
  architectures = ["arm64"]

  source_code_hash = data.archive_file.lambda_tf_generator.output_base64sha256

  role = aws_iam_role.lambda_exec.arn
}

resource "aws_cloudwatch_log_group" "tf-generator" {
  name = "/aws/lambda/${aws_lambda_function.tf-generator.function_name}"

  retention_in_days = 30
}

resource "aws_iam_role" "lambda_exec" {
  name = "serverless_lambda"

  assume_role_policy = jsonencode({
	Version = "2012-10-17"
	Statement = [{
	  Action = "sts:AssumeRole"
	  Effect = "Allow"
	  Sid    = ""
	  Principal = {
		Service = "lambda.amazonaws.com"
	  }
	  }
	]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_policy" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_user" "retool_lambda_invoker" {
  name = "retool_lambda_invoker"
}

resource "aws_iam_access_key" "retool_lambda_invoker" {
  user = aws_iam_user.retool_lambda_invoker.name
}

resource "aws_iam_user_policy" "retool_lambda_invoker_policy" {
  name = "test"
  user = aws_iam_user.retool_lambda_invoker.name

  policy = <<EOF
{
	  "Version": "2012-10-17",
	  "Statement": [
		  {
			  "Effect": "Allow",
			  "Action": [
				  "lambda:ListFunctions",
				  "lambda:InvokeFunction"
			  ],
			  "Resource": "*"
		  }
	  ]
  }
EOF
}