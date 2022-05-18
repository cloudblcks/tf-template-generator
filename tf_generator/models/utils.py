import json
from typing import Dict


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
