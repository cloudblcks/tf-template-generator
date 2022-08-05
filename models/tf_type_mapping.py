from dataclasses import dataclass
from typing import Dict, List, Optional, Union

from models.data_model import ServiceProvider, ResourceCategory
from models.utils import JsonSerialisable


@dataclass
class ResourceDetails(JsonSerialisable):
    key: str
    category: ResourceCategory
    tags: Optional[List[str]]
    clouds: List[ServiceProvider]
    description: Optional[str]
    params: Optional[str]

    @classmethod
    def from_dict(cls, d: Dict[str, str]):
        if "all" in d.get("clouds"):
            clouds = list(ServiceProvider.all())
        else:
            clouds = [ServiceProvider.get(cloud) for cloud in d.get("clouds")]

        category = ResourceCategory.get(d.get("category"))

        return cls(
            key=d.get("key"),
            category=category,
            tags=d.get("tags") or [],
            clouds=clouds,
            description=d.get("description") or "",
            params=d.get("params") or [],
        )

    def __eq__(self, other: "ResourceDetails"):
        return (
            self.key == other.key
            and self.category == other.category
            and self.tags == other.tags
            and self.clouds == other.clouds
            and self.description == other.description
            and self.params == other.params
        )

    def __lt__(self, other):
        return self.key < other.key

    def __repr__(self):
        return self.to_json()

    def to_dict(self) -> Dict:
        return {
            self.key: {
                "category": self.category,
                "tags": self.tags,
                "clouds": [c.value for c in self.clouds],
                "description": self.description,
                "params": self.params,
            }
        }

    @staticmethod
    def matches_cloud(resource: "ResourceDetails", cloud: str) -> bool:
        return cloud in resource.clouds

    @staticmethod
    def matches_tag(resource: "ResourceDetails", tag: str) -> bool:
        return tag in resource.tags

    @staticmethod
    def matches_keyword(resource: "ResourceDetails", keyword: str) -> bool:
        return (
            keyword == resource.key
            or keyword in resource.category
            or keyword in resource.tags
            or keyword in resource.clouds
            or keyword in resource.description.lower()
            or keyword in resource.params
        )


@dataclass
class ResourceMap(JsonSerialisable):
    resources: List[ResourceDetails]

    @classmethod
    def from_dict(cls, d: Union[List, Dict]):
        return cls(resources=[ResourceDetails.from_dict(x) for x in d])

    def get(self, key: str) -> ResourceDetails:
        key = key.lower()
        for resource in self.resources:
            if resource.key == key:
                return resource

        raise KeyError(f"No resource with key {key} found")

    def search(
        self,
        keyword: str,
        cloud: Optional[str],
        tags: Optional[List[str]],
        sort_results: bool = True,
    ) -> List[ResourceDetails]:
        results = self._filter_resources(keyword, cloud, tags)

        if not results:
            raise KeyError("No resources found matching your search")

        if sort_results and results:
            return sorted(list(results))

        return list(results)

    def _filter_resources(self, keyword, cloud, tags):
        results = self.resources

        if keyword:
            keyword = keyword.lower()
            results = filter(lambda x: ResourceDetails.matches_keyword(x, keyword), self.resources)

        if cloud:
            results = filter(lambda x: ResourceDetails.matches_cloud(x, cloud), results)

        if tags:
            for tag in tags:
                results = filter(lambda x: ResourceDetails.matches_tag(x, tag), results)

        return results
