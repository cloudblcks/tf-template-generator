# Output value definitions

output "lambda_bucket_name" {
  description = "Name of the S3 bucket used to store function code."

  value = aws_s3_bucket.lambda_bucket.id
}

output "function_name" {
  description = "Name of the Lambda function."

  value = aws_lambda_function.tf-generator.function_name
}

output "base_url" {
  description = "Base URL for API Gateway stage."

  value = aws_apigatewayv2_stage.lambda.invoke_url
}

output "github_s3_syncer_access_key" {
  description = "Github S3 syncer user access key"
  sensitive = true
  value = aws_iam_access_key.github_action_s3_template_syncer.id
}

output "github_s3_syncer_access_secret" {
  description = "Github S3 syncer user access secret"
  sensitive = true
  value = aws_iam_access_key.github_action_s3_template_syncer.secret
}