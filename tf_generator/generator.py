import os
from typing import Dict, Optional, List, Set

from jinja2 import Template

from models.high_level_items import (
    HighLevelCompute,
    HighLevelDB,
    HighLevelInternet,
    HighLevelStorage,
    HighLevelItem,
    HighLevelBinding,
    HighLevelBindingDirection,
    HighLevelItemTypes,
)
from models.low_level_items_aws import (
    LowLevelAWSItem,
    EC2Docker,
    VPC,
    TerraformGeneratorAWS,
    generate_id,
    CloudblocksValidationException,
    S3PublicWebsite,
    LowLevelStorageItem,
    S3,
    LowLevelComputeItem,
)
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
        self.ll_map: Dict[str, LowLevelAWSItem] = {}
        self.ll_list: List[LowLevelAWSItem] = []
        self.loader = S3TemplateLoader()
        self.templates = ServiceCategories.from_dict(templates_map)
        if base_template:
            self.base = Template(base_template)
        else:
            self.get_base_template()

    def get_base_template(self):
        with open(BASE_TEMPLATE_PATH, "r") as f:
            self.base = Template(f.read())

    def get_provider_template(self, provider: str) -> Optional[str]:
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

        return templates  # type: ignore

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

    def generate_template_from_json(self, json_data: List) -> str:
        hl_arr = json_to_high_level_list(json_data)
        self.generate_low_level_aws_map(hl_arr)
        generator = TerraformGeneratorAWS(self.ll_map, self.ll_list)
        provider_template = self.get_provider_template("aws")
        out = self.base.render(
            {
                "providers": provider_template,
                "services": [generator.generate_string_template()],
            }
        )
        return out

    def add_low_level_item(self, item: LowLevelAWSItem):
        self.ll_map[item.uid] = item
        self.ll_list.append(item)

    def generate_low_level_aws_map(self, input_arr: List[HighLevelItemTypes]):
        for item in input_arr:
            if item.uid not in self.ll_map:
                if isinstance(item, HighLevelCompute):
                    self.high_to_low_mapping_compute(item)
                elif isinstance(item, HighLevelDB):
                    self.high_to_low_mapping_db(item)
                elif isinstance(item, HighLevelStorage):
                    self.high_to_low_mapping_storage(item)

    def high_to_low_mapping_storage(self, storage: HighLevelStorage):
        s3: Optional[LowLevelStorageItem] = None
        for _ in (x for x in storage.bindings if x.direction == HighLevelBindingDirection.TO):
            raise CloudblocksValidationException("Storage item cannot bind TO another element")
        for _ in (x for x in storage.bindings if isinstance(x.item, HighLevelDB)):
            raise CloudblocksValidationException("Storage item cannot bind with a database")
        for _ in (x for x in storage.bindings if isinstance(x.item, HighLevelInternet)):
            s3 = S3PublicWebsite(storage.uid)
            self.add_low_level_item(s3)
            break
        if not s3:
            s3 = S3(storage.uid)
            self.add_low_level_item(s3)

    def high_to_low_mapping_compute(self, compute: HighLevelCompute):
        needs_internet_access = False
        for _ in (x for x in compute.bindings if isinstance(x.item, HighLevelInternet)):
            needs_internet_access = True
        vpc: Optional[VPC] = None
        for item in (x for x in compute.bindings if isinstance(x.item, HighLevelCompute)):
            if item.item.uid in self.ll_map:
                linked_compute = self.ll_map[item.item.uid]
                assert isinstance(linked_compute, LowLevelComputeItem)
                vpc = linked_compute.vpc
                break
        if not vpc:
            vpc = VPC(generate_id())
            self.add_low_level_item(vpc)
        linked_storage: Set[LowLevelStorageItem] = set()
        for item in (x for x in compute.bindings if isinstance(x.item, HighLevelStorage)):
            if storage := self.ll_map.get(item.item.uid):
                assert isinstance(storage, LowLevelStorageItem)
                linked_storage.add(storage)
            else:
                assert isinstance(item.item, HighLevelStorage)
                self.high_to_low_mapping_storage(item.item)
                storage = self.ll_map[item.item.uid]
                assert isinstance(storage, LowLevelStorageItem)
                linked_storage.add(storage)
        ec2 = EC2Docker(compute.uid, vpc, needs_internet_access=needs_internet_access, linked_storage=linked_storage)
        self.add_low_level_item(ec2)

    def high_to_low_mapping_db(self, compute: HighLevelDB):
        # rds = RDS(db.uid, self.templates)
        # linked_compute = db.linked_compute(low_level_map)
        # if linked_compute:
        #     rds.vpc = linked_compute[0].vpc
        # else:
        #     rds.vpc = VPC(generate_id())
        # # TODO: handle subnets
        # low_level_map[rds._id] = rds
        pass


def json_to_high_level_list(json_arr: List[Dict]) -> List[HighLevelItemTypes]:
    temp: Dict[str, HighLevelItemTypes] = {}
    for item in json_arr:
        item_type = item["clbksType"]
        uid = item["clbksId"]
        if item_type == "compute":
            temp[uid] = HighLevelCompute(uid)
        elif item_type == "internet":
            temp[uid] = HighLevelInternet(uid)
        elif item_type == "db":
            temp[uid] = HighLevelDB(uid)
        elif item_type == "storage":
            temp[uid] = HighLevelStorage(uid)
    for item in json_arr:
        if new_item := temp[item["clbksId"]]:
            for binding in item["bindings"]:
                binding_id = binding["id"]
                direction = HighLevelBindingDirection.match_string(binding["direction"])
                el = temp[binding_id]
                new_item.bindings.append(HighLevelBinding(el, direction))
    return list(temp.values())


def is_internet_needed(input_arr: List[HighLevelItem]) -> bool:
    for item in input_arr:
        if isinstance(item, HighLevelInternet):
            return True
    return False
