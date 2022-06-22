import json
from typing import Dict

import yaml


class MappingFileTypes:
    JSON = ["json"]
    YAML = ["yml", "yaml"]


VALID_FILE_SUFFIXES = MappingFileTypes.JSON + MappingFileTypes.YAML


def load_mapping(file_path: str) -> Dict:
    file_suffix = file_path.split(".")[-1]

    if file_suffix in MappingFileTypes.JSON:
        return _load_json_mapping(file_path)

    if file_suffix in MappingFileTypes.YAML:
        return _load_yaml_mapping(file_path)

    raise ValueError(f"File {file_path} does not have a valid suffix. Possible values: {VALID_FILE_SUFFIXES}")


def _load_json_mapping(file_path: str) -> Dict:
    with open(file_path, "r") as f:
        return json.load(f)


def _load_yaml_mapping(file_path: str) -> Dict:
    with open(file_path, "r") as f:
        return yaml.load(f, yaml.BaseLoader)
