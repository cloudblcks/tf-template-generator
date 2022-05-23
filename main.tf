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



resource "aws_s3_bucket" "template_bucket" {
  bucket = "cloudblocks-templates"
}

resource "aws_s3_bucket_acl" "template_bucket_acl" {
  bucket = aws_s3_bucket.template_bucket.id
  acl    = "public-read"
}


data "aws_caller_identity" "current" {}

locals {
  prefix              = "git"
  account_id          = data.aws_caller_identity.current.account_id
  ecr_repository_name = "${local.prefix}-tf-generator-lambda-container"
  ecr_image_tag       = "latest"
}

resource "aws_ecr_repository" "repo" {
  name = local.ecr_repository_name
}

resource "null_resource" "ecr_image" {
  triggers = {
    python_file = sha1(join("", [for f in fileset("${path.module}", "tf_generator/**") : filesha1(f)]))
  }

  provisioner "local-exec" {
    command = <<EOF
           aws ecr get-login-password --region ${var.aws_region} | docker login --username AWS --password-stdin ${local.account_id}.dkr.ecr.${var.aws_region}.amazonaws.com
           cd ${path.module}/tf_generator
           docker build -t ${aws_ecr_repository.repo.repository_url}:${local.ecr_image_tag} .
           docker push ${aws_ecr_repository.repo.repository_url}:${local.ecr_image_tag}
       EOF
  }
}

data "aws_ecr_image" "lambda_image" {
  depends_on = [
    null_resource.ecr_image
  ]
  repository_name = local.ecr_repository_name
  image_tag       = local.ecr_image_tag
}

resource "aws_lambda_function" "tf-generator" {
  depends_on = [
    null_resource.ecr_image
  ]
  architectures = ["arm64"]
  function_name = "tf-generator"
  timeout       = 63
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.repo.repository_url}@${data.aws_ecr_image.lambda_image.id}"

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
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Sid    = ""
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
  inline_policy {
    name = "s3_templates_access"

    policy = jsonencode({
      Version = "2012-10-17"
      Statement = [
        {
          Action   = ["s3:GetObject"]
          Effect   = "Allow"
          Resource = "arn:aws:s3:::cloudblocks-templates/*"
        },
      ]
    })
  }
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
