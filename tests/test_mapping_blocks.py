import json
from typing import List

import pytest
from models.mapping_blocks import Resource, ResourceParameter

# fmt: off

TEST_DATA_ATTRIBUTES = [
    ("foo", "bar", {"name": "foo", "value": "bar"}),
    ("foo", 1, {"name": "foo", "value": 1}),
    ("foo", {"lorem": "ipsum"}, {"name": "foo", "value": {"lorem": "ipsum"}}),
    ("foo", {"lorem": ["ipsum", "dolor", "sit", "amet"]},
     {"name": "foo", "value": {"lorem": ["ipsum", "dolor", "sit", "amet"]}}),
    ("foo", {"lorem": {"ipsum": "dolor", "sit": "amet"}},
     {"name": "foo", "value": {"lorem": {"ipsum": "dolor", "sit": "amet"}}}),
]
TEST_DATA_RESOURCES = [
    ("foo", "resource", ["lorem", "ipsum"], [],
     {"identifier": "foo", "block_type": "resource", "tags": ["lorem", "ipsum"]}),
    ("foo", "resource", ["lorem", "ipsum"], [ResourceParameter("foo", "bar")],
     {"identifier": "foo", "block_type": "resource", "tags": ["lorem", "ipsum"],
      "parameters": [{"name": "foo", "value": "bar"}]}),
    ("foo", "resource", ["lorem", "ipsum"], [ResourceParameter("foo", "bar"), ResourceParameter("lorem", "ipsum")],
     {"identifier": "foo", "block_type": "resource", "tags": ["lorem", "ipsum"],
      "parameters": [{"name": "foo", "value": "bar"}, {"name": "lorem", "value": "ipsum"}]}),
]


# fmt: on


@pytest.mark.parametrize("name,value,expected", TEST_DATA_ATTRIBUTES)
def test_resource_param_json_serialisation(name, value, expected):
    attribute = ResourceParameter(name, value)
    assert attribute.to_dict() == expected
    assert attribute.to_json() == json.dumps(expected)


@pytest.mark.parametrize("identifier,block_type,tags,attributes,expected", TEST_DATA_RESOURCES)
def test_resource_json_serialisation(
    identifier: str,
    block_type: str,
    tags: List[str],
    attributes: List[ResourceParameter],
    expected,
):
    block = Resource(identifier, block_type, tags, attributes)
    assert block.to_dict() == expected
    assert block.to_json() == json.dumps(expected)
