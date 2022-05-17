from dataclasses import dataclass
from typing import List


class JsonSerialisable:
    def to_json(self):
        raise NotImplementedError()


@dataclass
class TerraformAttribute(JsonSerialisable):
    name: str
    value: str

    def to_json(self):
        return {
            "name": self.name,
            "value": self.value,
        }


@dataclass
class Provider(JsonSerialisable):
    name: str
    version: str
    attributes: List[TerraformAttribute]

    def to_json(self):
        return {
            "name": self.name,
            "version": self.version,
            "attributes": [a.to_json for a in self.attributes]
        }


@dataclass
class Resource(JsonSerialisable):
    name: str
    block_type: str
    labels: List[str]  # TODO: Decide if labels should be flat or linked tree
    attributes: List[TerraformAttribute]

    def to_json(self):
        return {
            "name": self.name,
            "block_type": self.block_type,
            "labels": self.labels,
            "attributes": [a.to_json for a in self.attributes]
        }
