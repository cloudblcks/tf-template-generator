import json
from typing import Dict

import pytest

from tf_generator.models.s3_templates import (
    ServiceTemplate,
    ProviderServiceTemplates,
    ServiceCategories,
)

# fmt: off

TEST_DATA_SERVICE_TEMPLATES_TO_DICT = [
    ("ecs", "foo", "bar", "derp", {"service_name": "ecs", "uri": "foo", "outputs_uri": "bar", "variables_uri": "derp"}),
    ("ec2", "s3://foo", "s3://bar", "s3://derp",
     {"service_name": "ec2", "uri": "s3://foo", "outputs_uri": "s3://bar", "variables_uri": "s3://derp"})
]

TEST_DATA_SERVICE_TEMPLATES_FROM_JSON = [
    ('{"service_name": "ecs", "uri": "foo", "outputs_uri": "bar", "variables_uri": "derp"}',
     ServiceTemplate("ecs", "foo", "bar", "derp")),
    ('{"service_name": "ec2", "uri": "s3://foo", "outputs_uri": "s3://bar", "variables_uri": "s3://derp"}',
     ServiceTemplate("ec2", "s3://foo", "s3://bar", "s3://derp")),
]

TEST_DATA_PROVIDER_SERVICE_TEMPLATES_TO_DICT = [
    ({"ecs": ServiceTemplate("ecs", "foo", "bar", "derp")},
     {"ecs": {"service_name": "ecs", "uri": "foo", "outputs_uri": "bar", "variables_uri": "derp"}}),
    ({"ecs": ServiceTemplate("ecs", "foo", "bar", "derp"),
      "ec2": ServiceTemplate("ec2", "s3://foo", "s3://bar", "s3://derp")},
     {"ecs": {"service_name": "ecs", "uri": "foo", "outputs_uri": "bar", "variables_uri": "derp"},
      "ec2": {"service_name": "ec2", "uri": "s3://foo", "outputs_uri": "s3://bar", "variables_uri": "s3://derp"}}),
]

TEST_DATA_PROVIDER_SERVICE_TEMPLATES_FROM_JSON = [
    ('{"ecs": {"service_name": "ecs", "uri": "foo", "outputs_uri": "bar", "variables_uri": "derp"}}',
     ProviderServiceTemplates({"ecs": ServiceTemplate("ecs", "foo", "bar", "derp")})),
    ('''{"ecs": {"service_name": "ecs", "uri": "foo", "outputs_uri": "bar", "variables_uri": "derp"},
    "ec2": {"service_name": "ec2", "uri": "s3://foo", "outputs_uri": "s3://bar", "variables_uri": "s3://derp"}}''',
     ProviderServiceTemplates({"ecs": ServiceTemplate("ecs", "foo", "bar", "derp"),
                               "ec2": ServiceTemplate("ec2", "s3://foo", "s3://bar", "s3://derp")})),
]

TEST_DATA_SERVICE_CATEGORIES_TO_DICT = [
    ({"aws": {"foo": "bar"}},
     {"compute": ProviderServiceTemplates({"ecs": ServiceTemplate("ecs", "foo", "bar", "derp")})},
     {"providers": {"aws": {"foo": "bar"}},
      "compute": {"ecs": {"service_name": "ecs", "uri": "foo", "outputs_uri": "bar", "variables_uri": "derp"}}}),
    ({"aws": {"foo": "bar"}, "gcp": {"lorem": "ipsum"}},
     {"compute": ProviderServiceTemplates({"ecs": ServiceTemplate("ecs", "foo", "bar", "derp")}),
      "storage": ProviderServiceTemplates({"ec2": ServiceTemplate("ec2", "s3://foo", "s3://bar", "s3://derp")})},
     {"providers": {"aws": {"foo": "bar"}, "gcp": {"lorem": "ipsum"}},
      "compute": {"ecs": {"service_name": "ecs", "uri": "foo", "outputs_uri": "bar", "variables_uri": "derp"}},
      "storage": {
          "ec2": {"service_name": "ec2", "uri": "s3://foo", "outputs_uri": "s3://bar", "variables_uri": "s3://derp"}}}),
]

TEST_DATA_SERVICE_CATEGORIES_FROM_JSON = [
    ('''{"providers": {"aws": {"foo": "bar"}},
    "compute": {"ecs": {"service_name": "ecs", "uri": "foo", "outputs_uri": "bar", "variables_uri": "derp"}}}''',
     ServiceCategories({"aws": {"foo": "bar"}},
                       {"compute": ProviderServiceTemplates({"ecs": ServiceTemplate("ecs", "foo", "bar", "derp")})})),
    ('''{"providers": {"aws": {"foo": "bar"}, "gcp": {"lorem": "ipsum"}},
    "compute": {"ecs": {"service_name": "ecs", "uri": "foo", "outputs_uri": "bar", "variables_uri": "derp"}},
    "storage": {"ec2": {"service_name": "ec2", "uri": "s3://foo", "outputs_uri": "s3://bar", "variables_uri": "s3://derp"}}}''',
     ServiceCategories({"aws": {"foo": "bar"}, "gcp": {"lorem": "ipsum"}},
                       {"compute": ProviderServiceTemplates({"ecs": ServiceTemplate("ecs", "foo", "bar", "derp")}),
                        "storage": ProviderServiceTemplates(
                            {"ec2": ServiceTemplate("ec2", "s3://foo", "s3://bar", "s3://derp")})}))
]


# fmt: on


@pytest.mark.parametrize(
    "name,uri,outputs,variables,expected", TEST_DATA_SERVICE_TEMPLATES_TO_DICT
)
def test_service_template_json_deserialisation(
    name: str, uri: str, outputs: str, variables: str, expected: Dict
):
    template = ServiceTemplate(name, uri, outputs, variables)
    assert template.to_dict() == expected
    assert template.to_json() == json.dumps(expected)


@pytest.mark.parametrize("s,expected", TEST_DATA_SERVICE_TEMPLATES_FROM_JSON)
def test_service_template_json_serialisation(s: str, expected: ServiceTemplate):
    template = ServiceTemplate.from_json(s)
    assert template == expected
    assert template.to_json() == expected.to_json()


@pytest.mark.parametrize("data,expected", TEST_DATA_PROVIDER_SERVICE_TEMPLATES_TO_DICT)
def test_provider_service_template_json_deserialisation(
    data: Dict[str, ServiceTemplate], expected: Dict
):
    provider_templates = ProviderServiceTemplates(data)
    assert provider_templates.to_dict() == expected
    assert provider_templates.to_json() == json.dumps(expected)


@pytest.mark.parametrize("s,expected", TEST_DATA_PROVIDER_SERVICE_TEMPLATES_FROM_JSON)
def test_provider_service_template_json_serialisation(s, expected):
    provider_templates = ProviderServiceTemplates.from_json(s)
    assert provider_templates == expected
    assert provider_templates.to_json() == expected.to_json()


@pytest.mark.parametrize(
    "providers,provider_services,expected", TEST_DATA_SERVICE_CATEGORIES_TO_DICT
)
def test_service_categories_json_deserialisation(
    providers: Dict[str, dict],
    provider_services: Dict[str, ProviderServiceTemplates],
    expected: Dict,
):
    service_categories = ServiceCategories(providers, provider_services)
    assert service_categories.to_dict() == expected
    assert service_categories.to_json() == json.dumps(expected)


@pytest.mark.parametrize("s,expected", TEST_DATA_SERVICE_CATEGORIES_FROM_JSON)
def test_service_categories_json_serialisation(s, expected):
    service_categories = ServiceCategories.from_json(s)
    assert service_categories == expected
    assert service_categories.to_json() == expected.to_json()
