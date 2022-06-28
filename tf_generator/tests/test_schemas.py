from typing import Dict

import pytest
from schema import Schema

from models.schemas import MAP_SCHEMA, RESOURCE_SCHEMA, CLOUD_SCHEMA

TEST_DATA_SYS_CONFIGS = [
    pytest.param(
        {"category": "compute", "id": "foo"},
        RESOURCE_SCHEMA,
        id="test_simple_resource_schema",
    ),
    pytest.param(
        [{"category": "compute", "id": "foo"}],
        MAP_SCHEMA,
        id="test_simple_map_schema",
    ),
    pytest.param(
        [
            {"category": "compute", "id": "foo", "params": {"lorem": "ipsum", "answer": 42}},
        ],
        MAP_SCHEMA,
        id="test_single_resource_map_schema_sample_params",
    ),
    pytest.param(
        [
            {"category": "compute", "id": "foo"},
            {"category": "storage", "id": "bar"},
        ],
        MAP_SCHEMA,
        id="test_multi_resource_map_schema",
    ),
    pytest.param(
        [
            {"category": "compute", "id": "foo", "params": {}},
        ],
        MAP_SCHEMA,
        id="test_single_resource_map_schema_empty_params",
    ),
    pytest.param(
        [
            {"category": "compute", "id": "foo", "bindings": []},
            {"category": "storage", "id": "bar"},
        ],
        MAP_SCHEMA,
        id="test_multi_resource_map_schema_empty_bindings",
    ),
    pytest.param(
        [
            {"category": "compute", "id": "foo", "bindings": [{"id": "bar", "direction": "to"}]},
            {"category": "storage", "id": "bar"},
        ],
        MAP_SCHEMA,
        id="test_multi_resource_map_schema_one_binding",
    ),
    pytest.param(
        [
            {"category": "compute", "id": "foo", "bindings": [{"id": "bar", "direction": "to"}]},
            {"category": "storage", "id": "bar", "bindings": [{"id": "foo", "direction": "from"}]},
        ],
        MAP_SCHEMA,
        id="test_multi_resource_map_schema_two_bindings",
    ),
    pytest.param(
        [
            {
                "category": "compute",
                "id": "foo",
                "bindings": [{"id": "bar", "direction": "to"}],
                "params": {"lorem": "ipsum", "answer": 42},
            },
            {
                "category": "storage",
                "id": "bar",
                "bindings": [{"id": "foo", "direction": "from"}],
                "params": {"foo": "bar", "answer": "42"},
            },
        ],
        MAP_SCHEMA,
        id="test_multi_resource_map_schema_two_bindings_and_params",
    ),
    pytest.param(
        {"cloud": "aws", "resources": [{"category": "compute", "id": "foo"}]},
        CLOUD_SCHEMA,
        id="test_simple_CLOUD_SCHEMA_no_region",
    ),
    pytest.param(
        {"cloud": "aws", "regions": [{"region": "us-east-1", "resources": [{"category": "compute", "id": "foo"}]}]},
        CLOUD_SCHEMA,
        id="test_simple_CLOUD_SCHEMA_single_region_no_az",
    ),
    pytest.param(
        [{"cloud": "aws", "resources": [{"category": "compute", "id": "foo"}]}],
        MAP_SCHEMA,
        id="test_simple_map_schema_no_region",
    ),
    pytest.param(
        [{"cloud": "aws", "regions": [{"region": "us-east-1", "resources": [{"category": "compute", "id": "foo"}]}]}],
        MAP_SCHEMA,
        id="test_simple_map_schema_single_region_no_az",
    ),
]


@pytest.mark.parametrize("data,schema", TEST_DATA_SYS_CONFIGS)
def test_sys_config_passes_schema(data: Dict, schema: Schema):
    assert schema.validate(data)
