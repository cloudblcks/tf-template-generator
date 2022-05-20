from dataclasses import dataclass
from typing import Dict, Optional

from tf_generator.models.utils import JsonSerialisable
from tf_generator.tf_loader import S3TerraformLoader


@dataclass
class ProviderTemplate(JsonSerialisable):
    name: str
    uri: str
    template: Optional[str] = None

    @classmethod
    def from_dict(cls, d: Dict):
        return cls(name=d.get("name"), uri=d.get("uri"), template=d.get("template"))

    def load(self) -> None:
        if self.template:
            return

        loader = S3TerraformLoader()
        self.template = loader.get_file(self.uri)


@dataclass
class ServiceTemplate(JsonSerialisable):
    service_name: str
    uri: str
    outputs_uri: Optional[str]
    variables_uri: Optional[str]

    @classmethod
    def from_dict(cls, d: Dict):
        return cls(
            service_name=d["service_name"],
            uri=d["uri"],
            outputs_uri=d["outputs_uri"],
            variables_uri=d["variables_uri"],
        )


@dataclass
class ProviderServiceTemplates(JsonSerialisable):
    templates: Dict[str, ServiceTemplate]

    @classmethod
    def from_dict(cls, d: Dict):
        return cls(
            templates={
                key: ServiceTemplate.from_dict(value) for key, value in d.items()
            }
        )

    def to_dict(self) -> Dict:
        return {key: value.to_dict() for key, value in self.templates.items()}


@dataclass
class ServiceCategories(JsonSerialisable):
    providers: Dict[str, dict]
    provider_services: Dict[str, ProviderServiceTemplates]

    @classmethod
    def from_dict(cls, d: Dict):
        providers = d.pop("providers")
        return cls(
            providers=providers,
            provider_services={
                key: ProviderServiceTemplates.from_dict(value)
                for key, value in d.items()
            },
        )

    def to_dict(self) -> Dict:
        return {
            "providers": self.providers,
            **{key: value.to_dict() for key, value in self.provider_services.items()},
        }
