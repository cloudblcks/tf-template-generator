import json
from dataclasses import dataclass
from typing import List


class JsonSerialisable:
    def to_dict(self):
        raise NotImplementedError()

    def to_json(self):
        return json.dumps(self.to_dict())


@dataclass
class TerraformAttribute(JsonSerialisable):
    name: str
    value: str

    def to_dict(self):
        return {
            "name": self.name,
            "value": self.value,
        }


@dataclass
class Provider(JsonSerialisable):
    name: str
    version: str
    attributes: List[TerraformAttribute]

    def to_dict(self):
        return {
            "name": self.name,
            "version": self.version,
            "attributes": [a.to_dict for a in self.attributes]
        }


@dataclass
class Resource(JsonSerialisable):
    name: str
    block_type: str
    labels: List[str]  # TODO: Decide if labels should be flat or linked tree
    attributes: List[TerraformAttribute]

    def to_dict(self):
        return {
            "name": self.name,
            "block_type": self.block_type,
            "labels": self.labels,
            "attributes": [a.to_dict for a in self.attributes]
        }
