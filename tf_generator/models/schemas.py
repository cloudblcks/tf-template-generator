import json
from typing import Dict

from schema import Schema, And, Use, Optional, Or, SchemaError

from config import CLOUD_PROVIDER_SETTINGS
from models.high_level_items import HIGH_LEVEL_ITEM_TYPES, HIGH_LEVEL_BINDING_DIRECTIONS

DEFAULT_PROVIDER = "aws"


class CloudSchema(Schema):
    def validate(self, data: Dict, _is_region_schema=True, **kwargs):
        # TODO: set defaults by per-client feature flag
        super(CloudSchema, self).validate(data, _is_region_schema=False, kwargs=kwargs)
        if not _is_region_schema:  # Needed to avoid improper recursion
            return data

        cloud_provider = data.get("cloud")
        if not cloud_provider:
            cloud_provider = DEFAULT_PROVIDER

        if cloud_provider not in CLOUD_PROVIDER_SETTINGS.providers:
            raise SchemaError(
                f"Cloud provider {cloud_provider} not recognised. Valid clouds: {CLOUD_PROVIDER_SETTINGS.providers}"
            )

        if "regions" not in data:
            return data

        cloud_provider_regions = CLOUD_PROVIDER_SETTINGS.get(cloud_provider).regions
        invalid_regions = []
        for d in data.get("regions"):
            region = d.get("region")
            if region not in cloud_provider_regions:
                invalid_regions.append(region)

        if invalid_regions:
            raise SchemaError(
                f"""Regions {invalid_regions} not recognised for cloud provider {cloud_provider}.
                Valid regions:{cloud_provider_regions}"""
            )

        return data


RESOURCE_SCHEMA = Schema(
    {
        "category": And(Use(str), lambda s: s in HIGH_LEVEL_ITEM_TYPES),
        "id": str,
        Optional("bindings"): [
            {
                "id": str,
                "direction": And(Use(str), lambda s: s in HIGH_LEVEL_BINDING_DIRECTIONS),
            }
        ],
        Optional("params"): Or({str: object}, {}),
    }
)

REGION_SCHEMA = {
    "region": str,
    # If VPC isn't defined, assume everything is under a single network
    Optional("networks"): [
        {
            Optional("name"): str,
            Optional("availability_zones"): [str],
            "resources": [RESOURCE_SCHEMA],
        }
    ],
    Optional("resources"): [RESOURCE_SCHEMA],
}

CLOUD_SCHEMA = CloudSchema(
    {
        "cloud": str,
        Optional("regions"): [REGION_SCHEMA],
        Optional("resources"): [RESOURCE_SCHEMA],
    },
)

MAP_SCHEMA = Schema(
    [
        Or(
            CLOUD_SCHEMA,
            RESOURCE_SCHEMA,
        )
    ]
)
