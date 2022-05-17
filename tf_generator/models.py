import json
from dataclasses import dataclass
from typing import List


class JsonSerialisable:
    @classmethod
    def from_dict(cls, d: Dict):
        raise NotImplementedError()

    @classmethod
    def from_json(cls, d: str):
        return cls.from_dict(json.loads(d))

    def to_dict(self) -> Dict:
        raise NotImplementedError()

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


@dataclass
class TerraformAttribute(JsonSerialisable):
    name: str
    value: Union[str, int, List["TerraformAttribute"], Dict]

    @classmethod
    def from_dict(cls, d):
        return cls(name=d["name"], value=d["value"])

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
    name: str
    block_type: str
    labels: List[str]  # TODO: Decide if labels should be flat or linked tree
    attributes: List[TerraformAttribute]

    @classmethod
    def from_dict(cls, d):
        return cls(
            name=d["name"],
            block_type=d["block_type"],
            labels=d["labels"],
            attributes=[a.from_dict() for a in d["attributes"]],
        )

    def to_dict(self):
        return {
            "name": self.name,
            "block_type": self.block_type,
            "labels": self.labels,
            "attributes": [a.to_dict() for a in self.attributes],
        }
