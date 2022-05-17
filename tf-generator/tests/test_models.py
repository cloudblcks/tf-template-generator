import pytest

from models import TerraformAttribute

TEST_DATA_ATTRIBUTES = [
    ("foo", "bar", {"name": "foo", "value": "bar"}),
    ("foo", 1, {"name": "foo", "value": 1}),
]


@pytest.mark.parametrize("name,value,expected", TEST_DATA_ATTRIBUTES)
def test_tf_attribute_json_serialisation(name, value, expected):
    attribute = TerraformAttribute(name, value)
    assert attribute.to_json() == expected
