import io

import boto3

import config


class S3TerraformLoader:
    def __init__(self):
        self.s3 = boto3.resource(
            "s3",
            region_name=config.AWS_REGION,
            aws_access_key_id=config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
        )
        self.bucket = self.s3.Bucket(config.TEMPLATES_BUCKET)

    def get_file(self, uri):
        file = self.bucket.Object(uri)
        return file.get()["Body"].read().decode("utf-8")
