from typing import Dict, List, Optional

from tf_generator.models.s3_templates import ServiceCategories, ServiceCategory
from tf_generator.tf_loader import S3TerraformLoader


class TerraformGenerator:
    def __init__(self, templates_map: Dict):
        self.loader = S3TerraformLoader()
        self.templates = ServiceCategories.from_dict(templates_map)

    def get_templates(
        self,
        provider: str,
        compute_service: Optional[str],
        serverless_service: Optional[str],
        storage_service: Optional[str],
        database_service: Optional[str],
        website_host_service: Optional[str],
    ) -> Dict[str, str]:
        # self.templates.load_all()
        templates = {
            ServiceCategory.COMPUTE: self.templates.get(
                ServiceCategory.COMPUTE, provider, compute_service
            )
            if compute_service
            else None,
            ServiceCategory.SERVERLESS: self.templates.get(
                ServiceCategory.SERVERLESS, provider, serverless_service
            )
            if serverless_service
            else None,
            ServiceCategory.STORAGE: self.templates.get(
                ServiceCategory.STORAGE, provider, storage_service
            )
            if storage_service
            else None,
            ServiceCategory.DATABASE: self.templates.get(
                ServiceCategory.DATABASE, provider, database_service
            )
            if database_service
            else None,
            ServiceCategory.WEBSITE_HOST: self.templates.get(
                ServiceCategory.WEBSITE_HOST, provider, website_host_service
            )
            if database_service
            else None,
        }
        return templates
