import json
from dataclasses import asdict, dataclass
from enum import Enum
from itertools import chain
from typing import Dict

import yaml


@dataclass
class JsonSerialisable:
    @classmethod
    def from_dict(cls, d: Dict):
        raise NotImplementedError()

    @classmethod
    def from_json(cls, d: str):
        return cls.from_dict(json.loads(d))

    def to_dict(self) -> Dict:
        return {key: value for key, value in asdict(self).items() if value}

    def to_json(self, pretty=False) -> str:
        if pretty:
            return json.dumps(self.to_dict(), indent=2)
        return json.dumps(self.to_dict())

    def to_yaml(self) -> str:
        return yaml.dump(self.to_dict())
