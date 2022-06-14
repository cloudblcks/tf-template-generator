import os
from typing import Dict, Optional

from jinja2 import Template
from models.s3_templates import (
    ProviderTemplate,
    ServiceCategories,
    ServiceCategory,
    ServiceTemplate,
)

from models.high_level_items import (
    HighLevelCompute,
    HighLevelDB,
    HighLevelInternet,
    HighLevelStorage,
    HighLevelItem,
    HighLevelItemType,
    HighLevelBinding,
    HighLevelBindingDirection,
)

from models.low_level_items_aws import (
    LowLevelAWSItem,
    Cloudfront,
    S3,
    EC2,
    VPC,
    RDS,
    TerraformGeneratorAWS,
    generate_id,
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

    def generate_template_from_json(self, json_data: []) -> str:
        hl_arr = json_to_high_level_list(json_data)
        ll_map = generate_low_level_aws_map(hl_arr)
        generator = TerraformGeneratorAWS(ll_map)
        return generator.generate_string_template()


def json_to_high_level_list(json_arr: []) -> [HighLevelItem]:
    out: [HighLevelItem] = []
    for item in json_arr:
        new_item: Optional[HighLevelItem] = None
        item_type = item["clbksType"]
        _id = item["clbksId"]
        bindings = item["bindings"]
        match item_type:
            case "compute":
                new_item = HighLevelCompute(_id)
            case "db":
                new_item = HighLevelDB(_id)
            case "storage":
                new_item = HighLevelStorage(_id)
        for binding in bindings:
            binding_id = binding["id"]
            direction = HighLevelBindingDirection.match_string(binding["direction"])
            for el in out:
                if el.id == binding_id:
                    new_item.bindings.append(HighLevelBinding(el, direction))
    return out


def generate_low_level_aws_map(input_arr: [HighLevelItem]) -> {str: LowLevelAWSItem}:
    cloudfront: Optional[Cloudfront] = None
    low_level_map = {str: LowLevelAWSItem}
    input_computes, input_dbs, input_storages = breakdown_input_arr(input_arr)
    internet_item = get_internet_item(input_arr)
    if internet_item:
        cloudfront = Cloudfront(internet_item.id)
        low_level_map[internet_item.id] = cloudfront
    for storage in input_storages:
        s3 = S3(storage.id)
        if storage.needs_internet() and cloudfront:
            s3.cloudfront = cloudfront
        low_level_map[storage.id] = s3
    for compute in input_computes:
        ec2 = EC2(compute.id)
        linked_compute = compute.linkedCompute(low_level_map)
        if linked_compute:
            ec2.vpc = linked_compute[0].vpc
        else:
            ec2.vpc = VPC(generate_id())
        # TODO: handle subnets
        if compute.needs_internet:
            ec2.cloudfront = cloudfront
        low_level_map[compute.id] = ec2
    for db in input_dbs:
        rds = RDS(db.id)
        linked_compute = db.linkedCompute(low_level_map)
        if linked_compute:
            rds.vpc = linked_compute[0].vpc
        else:
            rds.vpc = VPC(generate_id())
        # TODO: handle subnets
        low_level_map[rds.id] = rds
    return low_level_map


def breakdown_input_arr(input_arr: [HighLevelItem]) -> ([HighLevelCompute], [HighLevelDB], [HighLevelStorage]):
    computes = [HighLevelCompute]
    dbs = [HighLevelDB]
    storages = [HighLevelStorage]
    for item in input_arr:
        match item.gettype():
            case HighLevelItemType.COMPUTE:
                computes.append(item)
                break
            case HighLevelItemType.DB:
                dbs.append(item)
                break
            case HighLevelItemType.STORAGE:
                storages.append(item)
                break
    return computes, dbs, storages


def is_internet_needed(input_arr: [HighLevelItem]) -> bool:
    return len(get_internet_item(input_arr).bindings) > 0


def get_internet_item(input_arr: [HighLevelItem]) -> HighLevelInternet:
    for item in input_arr:
        if item.gettype == HighLevelItemType.INTERNET:
            return item
