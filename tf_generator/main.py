import argparse
import json
import os

import click
import cloup
from cloup.constraints import mutually_exclusive
from dotenv import load_dotenv

import schema_validator
from generator import TerraformGenerator
from mapping_loader import load_mapping
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


def parse_old():
    parser = get_parser()
    args = parser.parse_args()

    with open(TEMPLATES_MAP_PATH, "r") as f:
        template_map = json.load(f)
    generator = TerraformGenerator(template_map)
    template = generator.generate_template(
        provider=args.provider,
        compute_service=args.compute,
        serverless_service=args.serverless,
        storage_service=args.storage,
        database_service=args.database,
        website_host_service=args.website,
    )

    print(template)


@cloup.group()
def cli():
    pass


@cli.command()
@click.option(
    "--file",
    "-f",
    help="""Path to mapping file, in either JSON or YAML formats
    Valid filetypes: .json .yml .yaml""",
)
@click.option(
    "--out",
    "-o",
    default=None,
    help="Path to output file (Recommended to use .tf suffix). If none supplied, will print output to stdout",
)
@click.option(
    "--config",
    "-c",
    default=None,
    help="Path to configuration python file. (Dangerous, use only to edit default values)",
)
def parse(file, out, config):
    """
    Generate Terraform configuration from Cloudblocks mapping file
    """
    pass


@cli.command()
@cloup.option_group(
    "Data Sources",
    cloup.option(
        "--file",
        "-f",
        help="""Path to mapping file, in either JSON or YAML formats
    Valid filetypes: .json .yml .yaml""",
    ),
    cloup.option("--data", "-d", help="Inline JSON mapping"),
    constraint=mutually_exclusive,
)
def validate(file, data):
    """
    Check whether given configuration file is valid
    """
    if file:
        data = load_mapping(file)

    if schema_validator.validate(data):
        print("Configuration is valid")
    else:
        print("Configuration isn't valid")


if __name__ == "__main__":
    cli()
