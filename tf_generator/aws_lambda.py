import json
import os

from dotenv import load_dotenv

from generator import TerraformGenerator

load_dotenv()


def lambda_handler(event, context):
    generator = TerraformGenerator()
    print(json.dumps(event))
    if "queryStringParameters" in event.keys() and event["queryStringParameters"]:
        args = event["queryStringParameters"]
        if args.get("hosting") == "lambda":
            args["serverless"] = "lambda"
        if args.get("static") == "yes":
            args["static"] = "static"

        templates = generator.generate_template(
            provider=args.get("provider"),
            compute_service=args.get("compute"),
            serverless_service=args.get("serverless"),
            storage_service=args.get("storage"),
            database_service=args.get("db"),
            website_host_service=args.get("static"),
        )
        return {
            "statusCode": 200,
            "body": templates,
        }
    else:
        data = json.loads(event["body"])["cloudblocks_data"]
        templates = generator.generate_template_from_json(data)
        return {"statusCode": 200, "body": templates}
