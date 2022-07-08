import os
import uuid
from dataclasses import dataclass
from typing import Optional, Dict, Set, List

import petname
from jinja2 import Template

from models.s3_templates import ServiceTemplate
from template_loader import S3TemplateLoader

BASE_TEMPLATE_PATH = os.path.join(os.getcwd(), "templates", "base.tf.template")

template_loader = S3TemplateLoader()


class CloudblocksValidationException(Exception):
    def __init__(self, message, errors=None):
        super().__init__(message)
        if errors is None:
            errors = []
        self.errors = errors


@dataclass
class TerraformConfig:
    main: Optional[str]
    variables: Optional[str]
    outputs: Optional[str]


class LowLevelAWSItem:
    def __init__(self, new_id: str, depends_on: Set["LowLevelAWSItem"] = None):
        if depends_on is None:
            depends_on = set()
        self.uid: str = new_id
        self.depends_on = depends_on

    template: Template
    variables: Template
    outputs: Template

    def generate_config(self) -> TerraformConfig:
        raise NotImplementedError()


class LowLevelSharedItem(LowLevelAWSItem):
    def generate_config(self):
        raise NotImplementedError()


class VPC(LowLevelSharedItem):
    def __init__(self, new_id: str, depends_on: Set["LowLevelAWSItem"] = None):
        super().__init__(new_id, depends_on)
        self.template = load_template("templates/vpc/main.tf.template")
        self.variables = load_template("templates/vpc/variables.tf.template")

    def generate_config(self) -> TerraformConfig:
        out_template = ""
        out_variables = ""
        if self.template:
            out_template = self.template.render({"vpc_uid": self.uid})
        if self.variables:
            out_variables = self.variables.render({"vpc_uid": self.uid})
        return TerraformConfig(out_template, out_variables, "")


class LowLevelComputeItem(LowLevelAWSItem):
    def __init__(self, new_id: str, vpc: VPC, depends_on: Set["LowLevelAWSItem"] = None):
        if depends_on is None:
            depends_on = set()
        depends_on.add(vpc)
        super().__init__(new_id, depends_on)
        self.vpc: VPC = vpc

    def generate_config(self):
        raise NotImplementedError()


class LowLevelStorageItem(LowLevelAWSItem):
    def __init__(self, new_id: str, depends_on: Set["LowLevelAWSItem"] = None):
        super().__init__(new_id, depends_on)

    def generate_config(self):
        raise NotImplementedError()


class LowLevelDBItem(LowLevelAWSItem):
    def __init__(self, new_id: str, vpc: VPC):
        super().__init__(new_id)
        self.vpc = vpc

    def generate_config(self):
        raise NotImplementedError()


class EC2Docker(LowLevelComputeItem):
    # TODO: add branches for public vs non public access
    def __init__(
        self,
        new_id,
        vpc: VPC,
        aws_ami: str,
        aws_ec2_instance_type: str,
        image_url: str,
        container_name: str,
        healthcheck_path: str,
        autoscale_min: int,
        autoscale_max: int,
        autoscale_target: int,
        cpu_cores: int = 10,
        memory: int = 512,
        desired_count: int = 1,
        aws_ecs_cluster_name: Optional[str] = None,
        ssh_pubkey: Optional[str] = None,
        needs_internet_access=False,
        linked_storage: Set[LowLevelStorageItem] = None,
        depends_on: Set["LowLevelAWSItem"] = None,
    ):
        if aws_ecs_cluster_name is None:
            aws_ecs_cluster_name = f"ecs-{new_id}-{petname.Generate(3)}"
        self.aws_ecs_cluster_name = aws_ecs_cluster_name
        if ssh_pubkey is None:
            ssh_pubkey = "~/.ssh/id_rsa.pub"
        if depends_on is None:
            depends_on = set()
        if not linked_storage:
            linked_storage = set()
        depends_on.update(linked_storage)
        depends_on.add(vpc)
        super().__init__(new_id, vpc, depends_on)
        self.linked_storage = linked_storage
        self.template = load_template("templates/ecs/main.tf.template")
        self.aws_ami = aws_ami
        self.aws_ec2_instance_type = aws_ec2_instance_type
        self.task_definition_family_name = f"taskdef-{new_id}-{petname.Generate(3)}"
        self.image_url = image_url
        self.cpu_cores = cpu_cores
        self.memory = memory
        self.desired_count = desired_count
        self.healthcheck_path = healthcheck_path
        self.autoscale_min = autoscale_min
        self.autoscale_max = autoscale_max
        self.autoscale_target = autoscale_target
        self.ssh_pubkey = ssh_pubkey
        self.container_name = container_name

    def generate_config(self) -> TerraformConfig:
        out_template = ""
        if self.template:
            out_template = self.template.render(
                {
                    "uid": self.uid,
                    "vpc_uid": self.vpc.uid,
                    "s3_buckets": self.linked_storage,
                    "aws_ecs_cluster_name": self.aws_ecs_cluster_name,
                    "aws_ami": self.aws_ami,
                    "aws_ec2_instance_type": self.aws_ec2_instance_type,
                    "task_definition_family_name": self.task_definition_family_name,
                    "image_url": self.image_url,
                    "cpu_cores": self.cpu_cores,
                    "memory": self.memory,
                    "desired_count": self.desired_count,
                    "healthcheck_path": self.healthcheck_path,
                    "autoscale_min": self.autoscale_min,
                    "autoscale_max": self.autoscale_max,
                    "autoscale_target": self.autoscale_target,
                    "ssh_pubkey": self.ssh_pubkey,
                    "container_name": self.container_name,
                }
            )

        return TerraformConfig(out_template, "", "")


class RDS(LowLevelDBItem):
    pass


class S3(LowLevelStorageItem):
    def __init__(self, new_id: str, bucket_name: str = None, depends_on: Set["LowLevelAWSItem"] = None):
        super().__init__(new_id, depends_on)
        self.template = load_template("templates/s3/main.tf.template")
        if not bucket_name:
            bucket_name = f"s3-{new_id}-{petname.Generate(3)}"
        self.bucket_name = bucket_name

    def generate_config(self) -> TerraformConfig:
        out_template = self.template.render({"uid": self.uid, "bucket_name": self.bucket_name})
        return TerraformConfig(out_template, "", "")


class S3PublicWebsite(LowLevelStorageItem):
    # TODO: add templates for S3 website
    def __init__(self, new_id: str, depends_on: Set["LowLevelAWSItem"] = None):
        super().__init__(new_id, depends_on)

    def generate_config(self) -> TerraformConfig:
        out_template = ""
        out_variables = ""
        out_outputs = ""
        if self.template:
            out_template += self.template.render({})
        if self.variables:
            out_variables += self.variables.render({})
        if self.outputs:
            out_outputs += self.outputs.render({})
        return TerraformConfig(out_template, out_variables, out_outputs)


def compile_item(compiled, item, out_outputs, out_template, out_variables):
    if not compiled[item.uid]:
        config = item.generate_config()
        out_template += config.main if config.main else ""
        out_variables += config.variables if config.variables else ""
        out_outputs += config.outputs if config.outputs else ""
        compiled[item.uid] = True
        return out_outputs, out_template, out_variables
    else:
        return "", "", ""


class TerraformGeneratorAWS:
    def __init__(self, ll_map: Dict[str, LowLevelAWSItem], ll_list: List[LowLevelAWSItem]):
        self.ll_map = ll_map
        self.ll_list = ll_list

    def generate_string_template(self) -> ServiceTemplate:
        compiled: Dict[str, bool] = {item.uid: False for item in self.ll_list}
        out_template = ""
        out_variables = ""
        out_outputs = ""

        for item in self.ll_list:
            if len(item.depends_on) > 0:
                for dep in item.depends_on:
                    out_outputs, out_template, out_variables = compile_item(
                        compiled, dep, out_outputs, out_template, out_variables
                    )
            # checking one more time in case it was already generated via dependencies
            if not compiled[item.uid]:
                out_outputs, out_template, out_variables = compile_item(
                    compiled, item, out_outputs, out_template, out_variables
                )

        out = ServiceTemplate(
            service_name="All services",
            uri="",
            outputs_uri=None,
            variables_uri=None,
            template=out_template,
            variables=out_variables,
            outputs=out_outputs,
        )
        return out


def generate_id() -> str:
    return uuid.uuid4().hex


def load_template(path: str) -> Template:
    with open(path, "r") as f:
        data = f.read()
        return Template(data)
