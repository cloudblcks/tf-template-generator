from dataclasses import dataclass
from typing import Dict, List

from models.utils import JsonSerialisable


# class CloudRegionConfig(JsonSerialisable):
#     @classmethod
#     def from_dict(cls, d: Dict):
#         pass


@dataclass
class CloudProviderConfig(JsonSerialisable):
    default_region: str
    regions: List[str]

    @classmethod
    def from_dict(cls, d: Dict):
        return cls(default_region=d.get("default"), regions=d.get("regions"))


@dataclass
class CloudConfig(JsonSerialisable):
    clouds: Dict[str, CloudProviderConfig]
    DEFAULT_CLOUD = "aws"

    @classmethod
    def from_dict(cls, d: Dict):
        return cls(clouds={key: CloudProviderConfig.from_dict(value) for key, value in d.items()})

    def get(self, cloud: str):
        return self.clouds.get(cloud)

    @property
    def providers(self):
        return self.clouds.keys()
