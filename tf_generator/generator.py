import os
from typing import Dict, Optional, List, Set

from jinja2 import Template

from models.high_level_items import (
    HighLevelResource,
    HighLevelBindingDirection,
    HighLevelMap,
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
    EC2,
)
from models.s3_templates import (
    ProviderTemplate,
    ServiceCategories,
    ServiceTemplate,
)
from models.tf_type_mapping import ResourceCategory
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
            templates[ResourceCategory.DOCKER] = self.templates.get(ResourceCategory.DOCKER, provider, compute_service)
        if serverless_service:
            templates[ResourceCategory.SERVERLESS] = self.templates.get(
                ResourceCategory.SERVERLESS, provider, serverless_service
            )
        if storage_service:
            templates[ResourceCategory.STORAGE] = self.templates.get(
                ResourceCategory.STORAGE, provider, storage_service
            )
        if database_service:
            templates[ResourceCategory.DATABASE] = self.templates.get(
                ResourceCategory.DATABASE, provider, database_service
            )
        if website_host_service:
            templates[ResourceCategory.WEBSITE_HOST] = self.templates.get(
                ResourceCategory.WEBSITE_HOST, provider, website_host_service
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

    def generate_template_from_json(self, json_data: List[Dict]) -> str:
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

    def generate_low_level_aws_map(self, input_arr: HighLevelMap):
        for item in input_arr.resources:
            if item.uid not in self.ll_map:
                if item.category == ResourceCategory.DOCKER:
                    self.high_to_low_mapping_docker(item)
                elif item == ResourceCategory.DATABASE:
                    self.high_to_low_mapping_db(item)
                elif item.category == ResourceCategory.STORAGE:
                    self.high_to_low_mapping_storage(item)

    def high_to_low_mapping_storage(self, storage: HighLevelResource):
        s3: Optional[LowLevelStorageItem] = None
        for _ in (x for x in storage.bindings if x.direction == HighLevelBindingDirection.TO):
            raise CloudblocksValidationException("Storage item cannot bind TO another element")
        for _ in (x for x in storage.bindings if x.target.category == ResourceCategory.DATABASE):
            raise CloudblocksValidationException("Storage item cannot bind with a database")
        for _ in (x for x in storage.bindings if x.target.category == ResourceCategory.INTERNET):
            s3 = S3PublicWebsite(storage.uid)
            self.add_low_level_item(s3)
            break
        if not s3:
            if "bucket_name" in storage.params:
                bucket_name = storage.params["bucket_name"]
                assert isinstance(bucket_name, str)
                self.add_low_level_item(S3(storage.uid, bucket_name))
            else:
                self.add_low_level_item(S3(storage.uid))

    def high_to_low_mapping_compute(self, compute: HighLevelResource):
        needs_internet_access = False
        vpc: Optional[VPC] = None
        for item in (
            x
            for x in compute.bindings
            if (x.target.category == ResourceCategory.COMPUTE or x.target.category == ResourceCategory.DOCKER)
        ):
            if item.target.uid in self.ll_map:
                linked_compute = self.ll_map[item.target.uid]
                assert isinstance(linked_compute, LowLevelComputeItem)
                vpc = linked_compute.vpc
                break
        if not vpc:
            num_of_azs: Optional[int] = None
            if "num_of_azs" in compute.params:
                assert str(compute.params["num_of_azs"]).isnumeric()
                num_of_azs = int(str(compute.params["num_of_azs"]))
            vpc = VPC(generate_id(), num_of_azs=num_of_azs)
            self.add_low_level_item(vpc)
        linked_storage: Set[LowLevelStorageItem] = set()
        for item in (x for x in compute.bindings if x.target == ResourceCategory.STORAGE):
            if storage := self.ll_map.get(item.target.uid):
                assert isinstance(storage, LowLevelStorageItem)
                linked_storage.add(storage)
            else:
                assert item.target == ResourceCategory.STORAGE
                self.high_to_low_mapping_storage(item.target)
                storage = self.ll_map[item.target.uid]
                assert isinstance(storage, LowLevelStorageItem)
                linked_storage.add(storage)

        assert isinstance(compute.params["aws_ami"], str)
        aws_ami: str = compute.params["aws_ami"]

        assert isinstance(compute.params["aws_instance_type"], str)
        aws_ec2_instance_type: str = compute.params["aws_instance_type"]

        instance_count: Optional[int] = None
        if "instance_count" in compute.params:
            assert str(compute.params["instance_count"]).isnumeric()
            instance_count = int(str(compute.params["instance_count"]))

        if "is_public" in compute.params:
            assert str(compute.params["is_public"]).isnumeric()
            needs_internet_access = bool(str(compute.params["is_public"]))

        user_data: Optional[str] = None
        if "user_data" in compute.params:
            assert isinstance(compute.params["user_data"], str)
            user_data = compute.params["user_data"]

        ec2 = EC2(
            compute.uid,
            vpc=vpc,
            aws_ami=aws_ami,
            aws_ec2_instance_type=aws_ec2_instance_type,
            instance_count=instance_count,
            user_data=user_data,
            needs_internet_access=needs_internet_access,
            linked_storage=linked_storage,
        )
        self.add_low_level_item(ec2)

    def high_to_low_mapping_docker(self, docker: HighLevelResource):
        needs_internet_access = False
        # for _ in (x for x in compute.bindings if x.target.category == ResourceCategory.INTERNET):
        #     needs_internet_access = True
        vpc: Optional[VPC] = None
        for item in (x for x in docker.bindings if x.target.category == ResourceCategory.DOCKER):
            if item.target.uid in self.ll_map:
                linked_compute = self.ll_map[item.target.uid]
                assert isinstance(linked_compute, LowLevelComputeItem)
                vpc = linked_compute.vpc
                break
        if not vpc:
            num_of_azs: Optional[int] = None
            if "num_of_azs" in docker.params:
                assert str(docker.params["num_of_azs"]).isnumeric()
                num_of_azs = int(str(docker.params["num_of_azs"]))
            vpc = VPC(generate_id(), num_of_azs=num_of_azs)
            self.add_low_level_item(vpc)
        linked_storage: Set[LowLevelStorageItem] = set()
        for item in (x for x in docker.bindings if x.target == ResourceCategory.STORAGE):
            if storage := self.ll_map.get(item.target.uid):
                assert isinstance(storage, LowLevelStorageItem)
                linked_storage.add(storage)
            else:
                assert item.target == ResourceCategory.STORAGE
                self.high_to_low_mapping_storage(item.target)
                storage = self.ll_map[item.target.uid]
                assert isinstance(storage, LowLevelStorageItem)
                linked_storage.add(storage)
        cluster_name: Optional[str] = None
        if "aws_ecs_cluster_name" in docker.params:
            assert isinstance(docker.params["aws_ecs_cluster_name"], str)
            cluster_name = docker.params["aws_ecs_cluster_name"]

        assert isinstance(docker.params["aws_ami"], str)
        aws_ami: str = docker.params["aws_ami"]

        assert isinstance(docker.params["aws_instance_type"], str)
        aws_ec2_instance_type: str = docker.params["aws_instance_type"]

        assert isinstance(docker.params["image_url"], str)
        image_url: str = docker.params["image_url"]

        assert isinstance(docker.params["container_name"], str)
        container_name: str = docker.params["container_name"]

        cpu_cores: Optional[int] = None
        if "cpu_cores" in docker.params:
            assert str(docker.params["cpu_cores"]).isnumeric()
            cpu_cores = int(str(docker.params["cpu_cores"]))

        memory: Optional[int] = None
        if "memory" in docker.params:
            assert str(docker.params["memory"]).isnumeric()
            memory = int(str(docker.params["memory"]))

        desired_count: Optional[int] = None
        if "desired_count" in docker.params:
            assert str(docker.params["desired_count"]).isnumeric()
            desired_count = int(str(docker.params["desired_count"]))

        assert isinstance(docker.params["healthcheck_path"], str)
        healthcheck_path: str = docker.params["healthcheck_path"]

        assert str(docker.params["autoscale_min"]).isnumeric()
        autoscale_min = int(str(docker.params["autoscale_min"]))

        assert str(docker.params["autoscale_max"]).isnumeric()
        autoscale_max = int(str(docker.params["autoscale_max"]))

        assert str(docker.params["autoscale_target"]).isnumeric()
        autoscale_target = int(str(docker.params["autoscale_target"]))

        ssh_pubkey: Optional[str] = None
        if "ssh_pubkey" in docker.params:
            assert isinstance(docker.params["ssh_pubkey"], str)
            ssh_pubkey = docker.params["ssh_pubkey"]

        if "is_public" in docker.params:
            assert str(docker.params["is_public"]).isnumeric()
            needs_internet_access = bool(str(docker.params["is_public"]))

        assert isinstance(docker.params["volume_path"], str)
        volume_path: str = docker.params["volume_path"]

        assert isinstance(docker.params["volume_name"], str)
        volume_name: str = docker.params["volume_name"]

        ec2 = EC2Docker(
            docker.uid,
            vpc,
            healthcheck_path=healthcheck_path,
            aws_ami=aws_ami,
            aws_ec2_instance_type=aws_ec2_instance_type,
            aws_ecs_cluster_name=cluster_name,
            image_url=image_url,
            container_name=container_name,
            volume_path=volume_path,
            volume_name=volume_name,
            cpu_cores=cpu_cores,
            memory=memory,
            desired_count=desired_count,
            autoscale_min=autoscale_min,
            autoscale_max=autoscale_max,
            autoscale_target=autoscale_target,
            needs_internet_access=needs_internet_access,
            ssh_pubkey=ssh_pubkey,
            linked_storage=linked_storage,
        )
        self.add_low_level_item(ec2)

    def high_to_low_mapping_db(self, compute: HighLevelResource):
        # rds = RDS(db.uid, self.templates)
        # linked_compute = db.linked_compute(low_level_map)
        # if linked_compute:
        #     rds.vpc = linked_compute[0].vpc
        # else:
        #     rds.vpc = VPC(generate_id())
        # # TODO: handle subnets
        # low_level_map[rds._id] = rds
        pass


def json_to_high_level_list(data: List[Dict]) -> HighLevelMap:
    # TODO: Add support for multiple clouds (this is hard coded to a single cloud instance)
    return HighLevelMap.from_dict(data[0])


def is_internet_needed(input_arr: List[HighLevelResource]) -> bool:
    for item in input_arr:
        if item.category == ResourceCategory.INTERNET:
            return True
    return False
