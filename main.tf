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
  cloud {
    organization = "cloudblocks"

    workspaces {
      name = "template-generator"
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

resource "aws_s3_bucket" "template_bucket" {
  bucket = "cloudblocks-templates"
}

resource "aws_s3_bucket_acl" "template_bucket_acl" {
  bucket = aws_s3_bucket.template_bucket.id
  acl    = "public-read"
}

data "archive_file" "lambda_tf_generator" {
  type = "zip"

  source_dir  = "${path.module}/tf_generator"
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

  runtime       = "python3.9"
  handler       = "lambda.lambda_handler"
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
    Version   = "2012-10-17"
    Statement = [
      {
        Action    = "sts:AssumeRole"
        Effect    = "Allow"
        Sid       = ""
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

resource "aws_iam_user" "github_action_s3_template_syncer" {
  name = "github_action_s3_template_syncer"
}

resource "aws_iam_access_key" "github_action_s3_template_syncer" {
  user = aws_iam_user.github_action_s3_template_syncer.name
}

resource "aws_iam_user_policy" "github_action_s3_template_syncer_policy" {
  name = "github_action_s3_template_syncer_policy"
  user = aws_iam_user.github_action_s3_template_syncer.name

  policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:DeleteObjectVersion",
                "s3:ListBucket",
                "s3:DeleteObject",
                "s3:GetObjectVersion"
            ],
            "Resource": "*"
        }
    ]
}
EOF
}

resource "aws_iam_user" "lambda_template_generator" {
  name = "lambda_template_generator"
}

resource "aws_iam_access_key" "lambda_template_generator" {
  user = aws_iam_user.lambda_template_generator.name
}

resource "aws_iam_user_policy" "lambda_template_generator_policy" {
  name = "lambda_template_generator_policy"
  user = aws_iam_user.lambda_template_generator.name

  policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:ListBucket",
            ],
            "Resource": [
                "arn:aws:s3:::cloudblocks-templates/*"
            ]
        }
    ]
}
EOF
}

resource "aws_apigatewayv2_api" "lambda" {
  name          = "serverless_lambda_gw"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_stage" "lambda" {
  api_id = aws_apigatewayv2_api.lambda.id

  name        = "serverless_lambda_stage"
  auto_deploy = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gw.arn

    format = jsonencode({
      requestId               = "$context.requestId"
      sourceIp                = "$context.identity.sourceIp"
      requestTime             = "$context.requestTime"
      protocol                = "$context.protocol"
      httpMethod              = "$context.httpMethod"
      resourcePath            = "$context.resourcePath"
      routeKey                = "$context.routeKey"
      status                  = "$context.status"
      responseLength          = "$context.responseLength"
      integrationErrorMessage = "$context.integrationErrorMessage"
    }
    )
  }
}

resource "aws_apigatewayv2_integration" "tf-generator" {
  api_id = aws_apigatewayv2_api.lambda.id

  integration_uri    = aws_lambda_function.tf-generator.invoke_arn
  integration_type   = "AWS_PROXY"
  integration_method = "POST"
}

resource "aws_apigatewayv2_route" "tf-generator" {
  api_id = aws_apigatewayv2_api.lambda.id

  route_key = "GET /generate"
  target    = "integrations/${aws_apigatewayv2_integration.tf-generator.id}"
}

resource "aws_cloudwatch_log_group" "api_gw" {
  name = "/aws/api_gw/${aws_apigatewayv2_api.lambda.name}"

  retention_in_days = 30
}

resource "aws_lambda_permission" "api_gw" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.tf-generator.function_name
  principal     = "apigateway.amazonaws.com"

  source_arn = "${aws_apigatewayv2_api.lambda.execution_arn}/*/*"
}