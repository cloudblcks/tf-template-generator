from typing import Dict

import pytest
from schema import Schema

from models.schemas import MAP_SCHEMA, RESOURCE_SCHEMA, CLOUD_SCHEMA

TEST_DATA_SYS_CONFIGS = [
    pytest.param(
        {"foo": {"resource": "docker"}},
        RESOURCE_SCHEMA,
        id="test_simple_resource_schema",
    ),
    pytest.param(
        {"foo": {"resource": "docker"}},
        MAP_SCHEMA,
        id="test_simple_map_schema",
    ),
    pytest.param(
        {
            "foo": {"resource": "docker", "params": {"lorem": "ipsum", "answer": 42}},
        },
        MAP_SCHEMA,
        id="test_single_resource_map_schema_sample_params",
    ),
    pytest.param(
        {
            "foo": {"resource": "docker"},
            "bar": {"resource": "postgresql"},
        },
        MAP_SCHEMA,
        id="test_multi_resource_map_schema",
    ),
    pytest.param(
        {
            "foo": {"resource": "docker", "params": {}},
        },
        MAP_SCHEMA,
        id="test_single_resource_map_schema_empty_params",
    ),
    pytest.param(
        {
            "foo": {"resource": "docker", "bindings": []},
            "bar": {"resource": "postgresql"},
        },
        MAP_SCHEMA,
        id="test_multi_resource_map_schema_empty_bindings",
    ),
    pytest.param(
        {
            "foo": {"resource": "docker", "bindings": [{"id": "bar", "direction": "to"}]},
            "bar": {"resource": "postgresql"},
        },
        MAP_SCHEMA,
        id="test_multi_resource_map_schema_one_binding",
    ),
    pytest.param(
        {
            "foo": {"resource": "docker", "bindings": [{"id": "bar", "direction": "to"}]},
            "bar": {"resource": "postgresql", "bindings": [{"id": "foo", "direction": "from"}]},
        },
        MAP_SCHEMA,
        id="test_multi_resource_map_schema_two_bindings",
    ),
    pytest.param(
        {
            "foo": {
                "resource": "docker",
                "bindings": [{"id": "bar", "direction": "to"}],
                "params": {"lorem": "ipsum", "answer": 42},
            },
            "bar": {
                "resource": "postgresql",
                "bindings": [{"id": "foo", "direction": "from"}],
                "params": {"foo": "bar", "answer": "42"},
            },
        },
        MAP_SCHEMA,
        id="test_multi_resource_map_schema_two_bindings_and_params",
    ),
    pytest.param(
        {"cloud": "aws", "resources": {"foo": {"resource": "docker"}}},
        CLOUD_SCHEMA,
        id="test_simple_CLOUD_SCHEMA_no_region",
    ),
    pytest.param(
        {"cloud": "aws", "regions": [{"region": "us-east-1", "resources": {"foo": {"resource": "docker"}}}]},
        CLOUD_SCHEMA,
        id="test_simple_CLOUD_SCHEMA_single_region_no_az",
    ),
    pytest.param(
        [{"cloud": "aws", "resources": {"foo": {"resource": "docker"}}}],
        MAP_SCHEMA,
        id="test_simple_map_schema_no_region",
    ),
    pytest.param(
        [{"cloud": "aws", "regions": [{"region": "us-east-1", "resources": {"foo": {"resource": "docker"}}}]}],
        MAP_SCHEMA,
        id="test_simple_map_schema_single_region_no_az",
    ),
]


@pytest.mark.parametrize("data,schema", TEST_DATA_SYS_CONFIGS)
def test_sys_config_passes_schema(data: Dict, schema: Schema):
    assert schema.validate(data)
