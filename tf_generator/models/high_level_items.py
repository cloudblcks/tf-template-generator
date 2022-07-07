import itertools
from dataclasses import dataclass
from enum import auto
from typing import List, Dict, Optional, Tuple

from strenum import LowercaseStrEnum

from config import RESOURCE_SETTINGS, CLOUD_PROVIDER_SETTINGS
from models.low_level_items_aws import LowLevelAWSItem, LowLevelComputeItem, CloudblocksValidationException
from models.s3_templates import ServiceProvider
from models.tf_type_mapping import ResourceDetails, ResourceCategory
from models.utils import JsonSerialisable


class HighLevelBindingDirection(LowercaseStrEnum):
    TO = auto()
    FROM = auto()
    BOTH = auto()

    @staticmethod
    def match_string(string: str) -> "HighLevelBindingDirection":
        if string == "to":
            return HighLevelBindingDirection.TO
        elif string == "from":
            return HighLevelBindingDirection.FROM
        elif string == "both":
            return HighLevelBindingDirection.BOTH
        raise CloudblocksValidationException("Unsupported binding direction")


HIGH_LEVEL_BINDING_DIRECTIONS = [x for x in HighLevelBindingDirection]


class HighLevelResource(JsonSerialisable):
    def __init__(
        self,
        uid: str,
        key: str,
        bindings: List["HighLevelBinding"] = None,
        params: Dict[str, object] = None,
    ):
        self.uid: str = uid
        self.bindings: List[HighLevelBinding] = bindings or []
        self.params: Dict[str, object] = params or {}
        self.resource: ResourceDetails = RESOURCE_SETTINGS.get(key)

    @classmethod
    def from_dict(cls, d: Dict, uid: str = None):
        if not uid:
            uid = d.get("id")

        # bindings = [HighLevelBinding(target_key=x["id"], direction=x["direction"]) for x in d.get("bindings", [])]

        return cls(
            uid=uid,
            key=d.get("resource"),
            bindings=[],
            params=d.get("params"),
        )

    @property
    def category(self) -> ResourceCategory:
        return self.resource.category

    def needs_internet(self) -> bool:
        for item in self.bindings:
            if item.target.category == ResourceCategory.INTERNET:
                return True
        return False

    def linked_compute(self, input_map: Dict[str, LowLevelAWSItem]) -> List[LowLevelComputeItem]:
        out = []
        for x in self.bindings:
            if x.target.category == ResourceCategory.COMPUTE and x.target.uid in list(input_map):
                item = input_map[x.target.uid]
                assert isinstance(item, LowLevelComputeItem)
                out.append(item)
        return out


@dataclass
class HighLevelBinding:
    direction: HighLevelBindingDirection
    target: HighLevelResource


@dataclass
class HighLevelMap(JsonSerialisable):
    cloud_provider: ServiceProvider
    region_resources: Dict[str, List[HighLevelResource]]

    @classmethod
    def from_dict(cls, d: Dict):
        cloud_provider = ServiceProvider.get(d.get("cloud", ServiceProvider.AWS.value))
        cloud_provider_config = CLOUD_PROVIDER_SETTINGS.get(cloud_provider)

        region = d.get("region", cloud_provider_config.default_region)
        bindings: List[Dict] = []
        if "regions" not in d:
            resources, new_bindings = cls._extract_resources(d["resources"])
            bindings.extend(new_bindings)
            instance = cls(cloud_provider, {region: resources})

        else:
            resources = {}
            for region_resources in d["regions"]:
                region = region_resources.get("region")
                resources[region], new_bindings = cls._extract_resources(region_resources["resources"])
                bindings.extend(new_bindings)
            instance = cls(cloud_provider, resources)

        for binding in bindings:
            resource = instance.get(binding["from"])
            resource.bindings.append(
                HighLevelBinding(target=instance.get(binding["to"]), direction=binding["direction"])
            )
        # for r in instance.resources:
        #     for binding in r.bindings:
        #         if not binding.target:
        #             binding.target = instance.get(binding.target_key)

        return instance

    @staticmethod
    def _extract_resources(d: Dict) -> Tuple[List[HighLevelResource], List[Dict]]:
        resources: List[HighLevelResource] = []
        bindings: List[Dict] = []
        for key, value in d.items():
            resources.append(HighLevelResource.from_dict(value, uid=key))
            bindings.extend(
                [
                    {"from": key, "to": binding["id"], "direction": binding["direction"]}
                    for binding in value.get("bindings", [])
                ]
            )
        return resources, bindings

    @staticmethod
    def _get_resource_from_key(resources: List[HighLevelResource], uid: str) -> HighLevelResource:
        for resource in resources:
            if resource.uid == uid:
                return resource

        raise KeyError(f"No resource with uid {uid} found")

    @property
    def resources(self) -> List[HighLevelResource]:
        return list(itertools.chain(*self.region_resources.values()))

    def __getitem__(self, item):
        return self.get(item)

    def get(self, uid: str, region: Optional[str] = None) -> HighLevelResource:
        if region:
            return self._get_resource_from_key(self.region_resources[region], uid)

        return self._get_resource_from_key(self.resources, uid)
