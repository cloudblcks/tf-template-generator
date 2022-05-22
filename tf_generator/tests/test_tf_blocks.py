import json
from typing import List

import pytest

from models.tf_blocks import Resource, TerraformAttribute

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
     {"identifier": "foo", "block_type": "resource", "labels": ["lorem", "ipsum"], "attributes": []}),
    ("foo", "resource", ["lorem", "ipsum"], [TerraformAttribute("foo", "bar")],
     {"identifier": "foo", "block_type": "resource", "labels": ["lorem", "ipsum"],
      "attributes": [{"name": "foo", "value": "bar"}]}),
    ("foo", "resource", ["lorem", "ipsum"], [TerraformAttribute("foo", "bar"), TerraformAttribute("lorem", "ipsum")],
     {"identifier": "foo", "block_type": "resource", "labels": ["lorem", "ipsum"],
      "attributes": [{"name": "foo", "value": "bar"}, {"name": "lorem", "value": "ipsum"}]}),
]


# fmt: on


@pytest.mark.parametrize("name,value,expected", TEST_DATA_ATTRIBUTES)
def test_tf_attribute_json_serialisation(name, value, expected):
    attribute = TerraformAttribute(name, value)
    assert attribute.to_dict() == expected
    assert attribute.to_json() == json.dumps(expected)


@pytest.mark.parametrize(
    "identifier,block_type,labels,attributes,expected", TEST_DATA_RESOURCES
)
def test_resource_json_serialisation(
    identifier: str,
    block_type: str,
    labels: List[str],
    attributes: List[TerraformAttribute],
    expected,
):
    block = Resource(identifier, block_type, labels, attributes)
    assert block.to_dict() == expected
    assert block.to_json() == json.dumps(expected)
