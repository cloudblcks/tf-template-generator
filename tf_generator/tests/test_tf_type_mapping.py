from typing import Dict, List

import pytest

from models.tf_type_mapping import ResourceMap, ResourceDetails

TEST_DATA_BIGTABLE_MAPPING = {
    "key": "bigtable",
    "clouds": ["gcp"],
    "tags": ["database", "gcp-only"],
    "description": "Google's NoSQL database for 1TB+ systems",
}
TEST_DATA_DOCKER_MAPPING = {
    "key": "docker",
    "aliases": ["docker-container", "docker-stateful"],
    "clouds": ["all"],
    "tags": ["compute", "cloud-agnostic", "serverless"],
    "description": "Generic docker container running in the cloud",
}
TEST_DATA_POSTGRES_MAPPING = {
    "key": "postgresql",
    "aliases": ["postgres"],
    "clouds": ["all"],
    "tags": ["database", "rdbms", "sql"],
    "description": "Open source relational database (SQL-RDBMS)",
}
TEST_DATA_S3_MAPPING = {
    "key": "s3",
    "clouds": ["aws"],
    "tags": ["storage", "aws-only"],
    "description": "Amazon Web Services static storage",
    "params": [
        {
            "param": "bucket_name",
            "description": "Unique identifier for the bucket. Must be unique across all AWS accounts",
            "data_type": "string",
        }
    ],
}
TEST_DATA_MAPPING = [
    TEST_DATA_BIGTABLE_MAPPING,
    TEST_DATA_DOCKER_MAPPING,
    TEST_DATA_POSTGRES_MAPPING,
    TEST_DATA_S3_MAPPING,
]


@pytest.fixture
def resource_map() -> ResourceMap:
    return ResourceMap.from_dict(TEST_DATA_MAPPING)


def _get_resource_details(key: str) -> ResourceDetails:
    data = {
        "bigtable": TEST_DATA_BIGTABLE_MAPPING,
        "docker": TEST_DATA_DOCKER_MAPPING,
        "postgresql": TEST_DATA_POSTGRES_MAPPING,
        "s3": TEST_DATA_S3_MAPPING,
    }.get(key)
    return ResourceDetails.from_dict(data)


@pytest.mark.parametrize(
    "test_data",
    [TEST_DATA_S3_MAPPING, TEST_DATA_DOCKER_MAPPING, TEST_DATA_POSTGRES_MAPPING],
)
def test_resource_map_getter(test_data: Dict, resource_map: ResourceMap):
    resource = resource_map.get(test_data.get("key"))
    assert resource == ResourceDetails.from_dict(test_data)


@pytest.mark.parametrize(
    "search_params,expected_keys",
    [
        pytest.param({}, ["bigtable", "docker", "postgresql", "s3"], id="test_no_keyword"),
        pytest.param({"keyword": "docker"}, ["docker"], id="test_search_by_key"),
        pytest.param({"keyword": "docker-container"}, ["docker"], id="test_search_by_alias"),
        pytest.param({"keyword": "Generic docker"}, ["docker"], id="test_search_by_keyword_in_description"),
        pytest.param({"cloud": "aws"}, ["docker", "postgresql", "s3"], id="test_filter_by_cloud"),
        pytest.param({"tags": ["database"]}, ["bigtable", "postgresql"], id="test_filter_by_db_tag"),
        pytest.param({"cloud": "aws", "tags": ["database"]}, ["postgresql"], id="test_filter_by_db_tag_and_cloud"),
    ],
)
def test_resource_map_search(search_params: Dict, expected_keys: List[str], resource_map: ResourceMap):
    keyword = search_params.get("keyword")
    cloud = search_params.get("cloud")
    tags = search_params.get("tags")
    results = resource_map.search(keyword, cloud, tags)

    assert len(results) == len(expected_keys)
    for key in expected_keys:
        assert _get_resource_details(key) in results
