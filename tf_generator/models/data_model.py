from dataclasses import dataclass
from enum import auto
from typing import Dict, Optional, Set, Union

from strenum import LowercaseStrEnum

from models.utils import JsonSerialisable


# noinspection PyArgumentList
class ServiceProvider(LowercaseStrEnum):
    AWS = auto()
    AZURE = auto()
    GCP = auto()
    HEROKU = auto()
    KUBERNETES = auto()

    @staticmethod
    def all() -> Set["ServiceProvider"]:
        return {
            ServiceProvider.AWS,
            ServiceProvider.AZURE,
            ServiceProvider.GCP,
            ServiceProvider.HEROKU,
            ServiceProvider.KUBERNETES,
        }

    @staticmethod
    def get(key: str) -> "ServiceProvider":
        return ServiceProvider[key.upper()]


# noinspection PyArgumentList
class ResourceCategory(LowercaseStrEnum):
    DOCKER = auto()
    COMPUTE = auto()
    SERVERLESS = auto()
    DATABASE = auto()
    STORAGE = auto()
    WEBSITE_HOST = auto()
    INTERNET = auto()
    THIRD_PARTY = auto()

    @staticmethod
    def all() -> Set["ResourceCategory"]:
        return {
            ResourceCategory.DOCKER,
            ResourceCategory.COMPUTE,
            ResourceCategory.STORAGE,
            ResourceCategory.DATABASE,
            ResourceCategory.INTERNET,
            ResourceCategory.THIRD_PARTY,
        }

    @staticmethod
    def get(key: str) -> "ResourceCategory":
        if key:
            return ResourceCategory[key.upper()]
        raise KeyError(f"Category {key} not recognised")

    @staticmethod
    def values() -> list[str]:
        return [x.value for x in ResourceCategory]


@dataclass
class ProviderTemplate(JsonSerialisable):
    name: ServiceProvider
    uri: str
    template: Optional[str] = None

    @classmethod
    def from_dict(cls, d: Dict[str, Union[str, ServiceProvider, Optional[str]]]):
        return cls(
            name=d.get("name"),
            uri=d.get("uri"),
            template=d.get("template"),
        )

    def to_dict(self) -> Dict:
        d = {"name": str(self.name), "uri": self.uri}
        if self.template:
            d["template"] = self.template

        return d


@dataclass
class ServiceTemplate(JsonSerialisable):
    service_name: str
    uri: str
    outputs_uri: Optional[str] = None
    variables_uri: Optional[str] = None
    template: Optional[str] = None
    outputs: Optional[str] = None
    variables: Optional[str] = None

    @classmethod
    def from_dict(cls, d: Dict[str, str]):
        return cls(
            service_name=d.get("service_name"),
            uri=d.get("uri"),
            outputs_uri=d.get("outputs_uri"),
            variables_uri=d.get("variables_uri"),
            template=d.get("template"),
            outputs=d.get("outputs"),
            variables=d.get("variables"),
        )
