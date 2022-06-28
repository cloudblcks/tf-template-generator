import argparse
import json
from typing import Optional, List

import cloup
import schema_validator
import template_writer
from cloup.constraints import mutually_exclusive
from config import TEMPLATES_MAP_PATH, RESOURCE_SETTINGS
from dotenv import load_dotenv
from generator import TerraformGenerator
from mapping_loader import load_mapping
from models.s3_templates import ServiceProvider

load_dotenv()


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
@cloup.option(
    "--out",
    "-o",
    default=None,
    help="Path to output file (Recommended to use .tf suffix). If none supplied, will print output to stdout",
)
def parse(file, data, out):
    """
    Generate Terraform configuration from Cloudblocks mapping file
    """
    if file:
        data = load_mapping(file)

    with open(TEMPLATES_MAP_PATH, "r") as f:
        template_map = json.load(f)
        generator = TerraformGenerator(template_map)
    templates = generator.generate_template_from_json(data)
    if out:
        template_writer.write(out, templates)
    else:
        print(templates)

    return templates


@cli.command()
@cloup.option_group(
    "Data Sources",
    cloup.option(
        "--file",
        "-f",
        help="""
        Path to mapping file, in either JSON or YAML formats
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


@cli.command()
@cloup.argument(
    "keyword",
    type=str,
    help="Search for any resources that mention given keyword",
    required=False,
)
@cloup.option(
    "--cloud",
    "-c",
    type=str,
    help="Filter for resources within specific cloud provider",
)
@cloup.option(
    "tags",
    "--tag",
    "-t",
    type=str,
    help="Filter for resources with specific tag",
    multiple=True,
)
@cloup.option(
    "print_list",
    "--list",
    "-l",
    is_flag=True,
    default=False,
    help="Only list resource keys rather than details",
)
def search(keyword: Optional[str], cloud: Optional[str], tags: Optional[List[str]], print_list: bool = False):
    """
    List supported resources
    """
    try:
        results = RESOURCE_SETTINGS.search(keyword, cloud, tags)
    except KeyError as e:
        print(e)
        return -1

    for resource in results:
        if print_list:
            print(resource.key)
        else:
            print(resource.to_yaml())


if __name__ == "__main__":
    cli()
