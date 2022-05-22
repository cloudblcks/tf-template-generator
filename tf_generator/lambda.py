import argparse
import json
import os

from dotenv import load_dotenv

from generator import TerraformGenerator
from models.s3_templates import ServiceProvider

load_dotenv()

TEMPLATES_MAP_PATH = os.path.join(os.getcwd(), "templates_map.json")


def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("provider", choices=[a for a in ServiceProvider])
    parser.add_argument("--compute", type=str)
    parser.add_argument("--serverless", type=str)
    parser.add_argument("--storage", type=str)
    parser.add_argument("--database", type=str)
    parser.add_argument("--website", type=str)

    return parser


def lambda_handler(event, context):
    args = event["queryStringParameters"]
    with open(TEMPLATES_MAP_PATH, "r") as f:
        template_map = json.load(f)
    generator = TerraformGenerator(template_map)
    templates = generator.get_templates(
        provider=args.provider,
        compute_service=args.compute,
        serverless_service=args.serverless,
        storage_service=args.storage,
        database_service=args.database,
        website_host_service=args.website,
    )
    return {
        "statusCode": 200,
        "body": json.dumps(templates),
    }
