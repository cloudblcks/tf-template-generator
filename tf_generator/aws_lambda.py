import json
import os

from dotenv import load_dotenv

from generator import TerraformGenerator
import main

load_dotenv()
TEMPLATES_MAP_PATH = os.path.join(os.getcwd(), "templates_map.json")


def lambda_handler_old(event, context):
    with open(TEMPLATES_MAP_PATH, "r") as f:
        template_map = json.load(f)
        generator = TerraformGenerator(template_map)
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


def lambda_handler_new(event, context):
    print(json.dumps(event))
    request = json.loads(event["body"])
    action = request.get("action")
    if action == "validate":
        results = main._validate(request.get("data"))
    elif action == "build":
        results = main._build(request.get("data"))
    elif action == "search":
        search_results = main._search(request.get("keyword"), request.get("cloud"), request.get("tags"))
        results = [result.to_json() for result in search_results]
    else:
        raise KeyError(f"Action {action} not recognised")

    return {"statusCode": 200, "body": results}
