import argparse
import json
from typing import Optional, List, Tuple

import cloup
from cloup.constraints import mutually_exclusive
from dotenv import load_dotenv

import schema_validator
import template_writer
from config import TEMPLATES_MAP_PATH, RESOURCE_SETTINGS
from generator import TerraformGenerator
from mapping_loader import load_mapping
from models.data_model import ServiceProvider
from models.tf_type_mapping import ResourceDetails

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
    "output_path",
    "--out",
    "-o",
    default=None,
    help="Path to output file (Recommended to use .tf suffix). If none supplied, will print output to stdout",
)
def build(file, data, output_path):
    """
    Generate Terraform configuration from Cloudblocks mapping file
    """
    if file:
        data = load_mapping(file)
    else:
        data = json.loads(data)

    if not _validate(data, verbose=True)[0]:
        exit("Input was invalid, please run validate to make sure it's valid")

    templates = _build(data)
    if output_path:
        template_writer.write(output_path, templates)
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
    cloup.option(
        "--data",
        "-d",
        type=str,
        help="Inline JSON mapping",
    ),
    constraint=mutually_exclusive,
)
def validate(file, data):
    """
    Check whether given configuration file is valid
    """
    if file:
        data = load_mapping(file)
    else:
        data = json.loads(data)

    return _validate(data, verbose=True)[0]


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
        results = _search(keyword, cloud, tags)
    except KeyError as e:
        print(e)
        return -1

    for resource in results:
        if print_list:
            print(resource.key)
        else:
            print(resource.to_yaml())


def _build(data):
    generator = TerraformGenerator()
    templates = generator.generate_template_from_json(data)
    return templates


def _validate(data, verbose=False) -> Tuple[bool, Optional[str]]:
    is_valid, err_message = schema_validator.validate(data)

    if is_valid:
        print("Configuration is valid")
    elif verbose:
        print(err_message)
    else:
        print("Configuration isn't valid")

    return is_valid, err_message


def _search(keyword: Optional[str], cloud: Optional[str], tags: Optional[List[str]]) -> List[ResourceDetails]:
    try:
        return RESOURCE_SETTINGS.search(keyword, cloud, tags)
    except KeyError as e:
        raise e


if __name__ == "__main__":
    cli()
