from dataclasses import dataclass
from typing import Dict, List, Union

from tf_generator.models.utils import JsonSerialisable


@dataclass
class TerraformAttribute(JsonSerialisable):
    name: str
    value: Union[str, int, List["TerraformAttribute"], Dict]

    @classmethod
    def from_dict(cls, d):
        return cls(name=d["name"], value=d["value"])

    def to_dict(self):
        value = self.value
        if isinstance(self.value, TerraformAttribute):
            value = self.value.to_dict()
        return {
            "name": self.name,
            "value": value,
        }


@dataclass
class Provider(JsonSerialisable):
    name: str
    version: str
    attributes: List[TerraformAttribute]

    @classmethod
    def from_dict(cls, d):
        return cls(
            name=d["name"],
            version=d["version"],
            attributes=[a.from_dict() for a in d["attributes"]],
        )

    def to_dict(self):
        return {
            "name": self.name,
            "version": self.version,
            "attributes": [a.to_dict() for a in self.attributes],
        }


@dataclass
class Resource(JsonSerialisable):
    identifier: str
    block_type: str
    labels: List[str]  # TODO: Decide if labels should be flat or linked tree
    attributes: List[TerraformAttribute]

    @classmethod
    def from_dict(cls, d):
        return cls(
            identifier=d["identifier"],
            block_type=d["block_type"],
            labels=d["labels"],
            attributes=[a.from_dict() for a in d["attributes"]],
        )

    def to_dict(self):
        return {
            "identifier": self.identifier,
            "block_type": self.block_type,
            "labels": self.labels,
            "attributes": [a.to_dict() for a in self.attributes],
        }
