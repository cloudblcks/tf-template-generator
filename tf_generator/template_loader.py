import io

import boto3

import config


class S3TemplateLoader:
    def __init__(self, bucket: str = None):
        self.s3 = boto3.resource(
            "s3",
            region_name=config.AWS_REGION,
            aws_access_key_id=config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
        )
        if not bucket:
            bucket = config.TEMPLATES_BUCKET
        self.bucket = self.s3.Bucket(bucket)

    def get_file(self, uri):
        file = self.bucket.Object(uri)
        return file.get()["Body"].read().decode("utf-8")
