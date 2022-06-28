import os
import uuid
from dataclasses import dataclass
from typing import Optional, Dict, Set, List

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
    # TODO: add proper storage access permissions
    # TODO: add branches for public vs non public access
    def __init__(
        self,
        new_id,
        vpc: VPC,
        needs_internet_access=False,
        linked_storage: Set[LowLevelStorageItem] = None,
        depends_on: Set["LowLevelAWSItem"] = None,
    ):
        if depends_on is None:
            depends_on = set()
        if not linked_storage:
            linked_storage = set()
        depends_on.update(linked_storage)
        depends_on.add(vpc)
        super().__init__(new_id, vpc, depends_on)
        self.linked_storage = linked_storage
        self.template = load_template("templates/ecs/main.tf.template")
        self.variables = load_template("templates/ecs/variables.tf.template")

    def generate_config(self) -> TerraformConfig:
        out_template = ""
        out_variables = ""
        if self.template:
            out_template = self.template.render({"uid": self.uid, "vpc_uid": self.vpc.uid})
        if self.variables:
            out_variables = self.variables.render({"uid": self.uid, "vpc_uid": self.vpc.uid})
        return TerraformConfig(out_template, out_variables, "")


class RDS(LowLevelDBItem):
    pass


class S3(LowLevelStorageItem):
    def __init__(self, new_id: str, depends_on: Set["LowLevelAWSItem"] = None):
        super().__init__(new_id, depends_on)
        self.template = load_template("templates/s3/main.tf.template")
        self.variables = load_template("templates/s3/variables.tf.template")

    def generate_config(self) -> TerraformConfig:
        out_template = self.template.render({"uid": self.uid})
        out_variables = self.variables.render({"uid": self.uid})
        return TerraformConfig(out_template, out_variables, "")


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
    config = item.generate_config()
    out_template += config.main if config.main else ""
    out_variables += config.variables if config.variables else ""
    out_outputs += config.outputs if config.outputs else ""
    compiled[item.uid] = True
    return out_outputs, out_template, out_variables


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
            if not compiled[item.uid]:
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
