import os
from typing import Dict, Optional

from jinja2 import Template
from models.s3_templates import (
    ProviderTemplate,
    ServiceCategories,
    ServiceCategory,
    ServiceTemplate,
)
from template_loader import S3TemplateLoader

BASE_TEMPLATE_PATH = os.path.join(os.getcwd(), "templates", "base.tf.template")


class TerraformGenerator:
    def __init__(self, templates_map: Dict, base_template: str = None):
        self.loader = S3TemplateLoader()
        self.templates = ServiceCategories.from_dict(templates_map)
        if base_template:
            self.base = Template(base_template)
        else:
            self.get_base_template()

    def get_base_template(self):
        with open(BASE_TEMPLATE_PATH, "r") as f:
            self.base = Template(f.read())

    def get_provider_template(self, provider: str) -> str:
        provider_template: ProviderTemplate = self.templates.providers.get(provider)
        if not provider_template:
            raise KeyError(f"No provider named [{provider}] found")

        provider_template.load(self.loader)
        return provider_template.template

    def get_service_templates(
        self,
        provider: str,
        compute_service: Optional[str],
        serverless_service: Optional[str],
        storage_service: Optional[str],
        database_service: Optional[str],
        website_host_service: Optional[str],
    ) -> Dict[str, ServiceTemplate]:
        templates = {}

        if compute_service:
            templates[ServiceCategory.COMPUTE] = self.templates.get(ServiceCategory.COMPUTE, provider, compute_service)
        if serverless_service:
            templates[ServiceCategory.SERVERLESS] = self.templates.get(
                ServiceCategory.SERVERLESS, provider, serverless_service
            )
        if storage_service:
            templates[ServiceCategory.STORAGE] = self.templates.get(ServiceCategory.STORAGE, provider, storage_service)
        if database_service:
            templates[ServiceCategory.DATABASE] = self.templates.get(
                ServiceCategory.DATABASE, provider, database_service
            )
        if website_host_service:
            templates[ServiceCategory.WEBSITE_HOST] = self.templates.get(
                ServiceCategory.WEBSITE_HOST, provider, website_host_service
            )

        return templates

    def generate_template(self, providers: [str], compute_services):

        pass

    def generate_template(
        self,
        provider: str,
        compute_service: Optional[str],
        serverless_service: Optional[str],
        storage_service: Optional[str],
        database_service: Optional[str],
        website_host_service: Optional[str],
    ) -> str:
        provider_template = self.get_provider_template(provider)
        service_templates = self.get_service_templates(
            provider,
            compute_service,
            serverless_service,
            storage_service,
            database_service,
            website_host_service,
        )
        return self.base.render(
            {
                "providers": provider_template,
                "services": [value for value in service_templates.values() if value],
            }
        )
