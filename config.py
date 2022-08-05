import json
import os

import boto3

from models.provider_config import CloudConfig
from models.tf_type_mapping import ResourceMap

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

AWS_REGION = "us-west-1"

TEMPLATES_BUCKET = "cloudblocks-templates"
GENERATED_TF_BUCKET = "cloudblocks-generated-tf"

AWS_ACCESS_KEY_ID = os.getenv("AWS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_KEY")

TEMPLATES_MAP_PATH = os.path.join(BASE_DIR, "data", "templates_map.json")

_CLOUD_PROVIDER_CONFIG_PATH = os.path.join(BASE_DIR, "data", "cloud_providers.json")
with open(_CLOUD_PROVIDER_CONFIG_PATH, "r") as f:
    CLOUD_PROVIDER_SETTINGS = CloudConfig.from_dict(json.load(f))

_CLOUD_RESOURCES_CONFIG_PATH = os.path.join(BASE_DIR, "data", "resources.json")
with open(_CLOUD_RESOURCES_CONFIG_PATH, "r") as f:
    RESOURCE_SETTINGS = ResourceMap.from_dict(json.load(f))


def get_aws_secret(var_key):
    """Return the secret value from an AWS secret."""
    secrets_client = boto3.client("secretsmanager")
    secret = secrets_client.get_secret_value(SecretId=f"arn:aws:secretsmanager:{var_key}")
    return secret["SecretString"]


def get_environ_or_aws_secret(env_var):
    """
    Return the value of an environment variable or AWS secret.

    It checks an environment variable, and if its value points
    to an AWS secret, retrieve it and return it instead.
    """
    env_var_value = os.getenv(env_var)
    if not env_var_value:
        # Use `get_aws_secret()` from previous example.
        return get_aws_secret(env_var)

    return env_var_value
