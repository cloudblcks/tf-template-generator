from dataclasses import dataclass
from typing import Dict, List, Union, Optional

import cdktf

from models.utils import JsonSerialisable


@dataclass
class ResourceParameter(JsonSerialisable):
    name: str
    value: Union[str, int, List["ResourceParameter"], Dict]

    @classmethod
    def from_dict(cls, d):
        return cls(name=d["name"], value=d["value"])


@dataclass
class Provider(JsonSerialisable):
    name: str
    version: str
    attributes: List[ResourceParameter]

    @classmethod
    def from_dict(cls, d):
        return cls(
            name=d["name"],
            version=d["version"],
            attributes=[a.from_dict() for a in d["attributes"]],
        )


@dataclass
class Resource(JsonSerialisable):
    identifier: str
    block_type: str
    tags: List[str]  # TODO: Decide if labels should be flat or linked tree
    parameters: List[ResourceParameter]
    tf_type: Optional[cdktf.Resource]

    @classmethod
    def from_dict(cls, d):
        tf_type = None
        return cls(
            identifier=d["identifier"],
            block_type=d["type"],
            tags=d["tags"],
            parameters=[ResourceParameter(key, value) for key, value in d["params"].items()],
            tf_type=tf_type,
        )

    def validate(self) -> bool:
        return True
