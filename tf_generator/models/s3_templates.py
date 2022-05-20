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
    outputs_uri: Optional[str] = None
    variables_uri: Optional[str] = None
    template: Optional[str] = None
    outputs: Optional[str] = None
    variables: Optional[str] = None

    @classmethod
    def from_dict(cls, d: Dict):
        return cls(
            service_name=d.get("service_name"),
            uri=d.get("uri"),
            outputs_uri=d.get("outputs_uri"),
            variables_uri=d.get("variables_uri"),
            template=d.get("template"),
            outputs=d.get("outputs"),
            variables=d.get("variables"),
        )

    def load(self) -> None:
        if self.template:
            return

        loader = S3TerraformLoader()
        self.template = loader.get_file(self.uri)

        if self.outputs_uri:
            self.outputs = loader.get_file(self.outputs_uri)

        if self.variables_uri:
            self.variables = loader.get_file(self.variables_uri)


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

    def get(self, service_key) -> ServiceTemplate:
        if not self.templates.get(service_key):
            raise ValueError(f"No service template with key [{service_key}] found")

        return self.templates.get(service_key)


@dataclass
class ServiceCategoryProviders(JsonSerialisable):
    services: Dict[str, ProviderServiceTemplates]

    @classmethod
    def from_dict(cls, d: Dict):
        return cls(
            services={
                key: ProviderServiceTemplates.from_dict(value)
                for key, value in d.items()
            }
        )

    def to_dict(self) -> Dict:
        return {key: value.to_dict() for key, value in self.services.items()}

    def get(self, provider, service_key) -> ServiceTemplate:
        if not self.services.get(service_key):
            raise ValueError(f"No service with key [{service_key}] found")

        return self.services.get(provider).get(service_key)


@dataclass
class ServiceCategories(JsonSerialisable):
    providers: Dict[str, ProviderTemplate]
    provider_services: Dict[str, ServiceCategoryProviders]

    @classmethod
    def from_dict(cls, d: Dict):
        providers = d.pop("providers")
        return cls(
            providers={
                key: ProviderTemplate.from_dict(value)
                for key, value in providers.items()
            },
            provider_services={
                key: ServiceCategoryProviders.from_dict(value)
                for key, value in d.items()
            },
        )

    def to_dict(self) -> Dict:
        return {
            "providers": {
                key: value.to_dict() for key, value in self.providers.items()
            },
            **{key: value.to_dict() for key, value in self.provider_services.items()},
        }

    def get(self, category: str, provider: str, name: str) -> ServiceTemplate:
        if not self.provider_services.get(category):
            raise KeyError(f"No category named [{category}] found")

        return self.provider_services.get(category).get(provider, name)
