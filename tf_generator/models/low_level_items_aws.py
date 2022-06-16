import os
import uuid
from dataclasses import dataclass
from typing import Optional, Dict

from jinja2 import Template

from models.s3_templates import ServiceCategories, ServiceCategory, ServiceProvider
from template_loader import S3TemplateLoader

BASE_TEMPLATE_PATH = os.path.join(os.getcwd(), "templates", "base.tf.template")

template_loader = S3TemplateLoader()


@dataclass
class TerraformConfig:
    main: Optional[str]
    variables: Optional[str]
    outputs: Optional[str]


class LowLevelAWSItem:
    def __init__(self, new_id: str):
        self._id: str = new_id

    template: Optional[Template] = None
    variables: Optional[Template] = None
    outputs: Optional[Template] = None

    def generate_config(self) -> TerraformConfig:
        raise NotImplementedError()


class LowLevelInfraItem(LowLevelAWSItem):
    def generate_config(self):
        raise NotImplementedError()


class VPC(LowLevelInfraItem):
    pass


class ALB(LowLevelInfraItem):
    pass


class Cloudfront(LowLevelInfraItem):
    def generate_config(self):
        return TerraformConfig(None, None, None)


class LowLevelComputeItem(LowLevelAWSItem):
    def __init__(self, new_id: str, vpc: VPC, cloudfront: Cloudfront):
        super().__init__(new_id)
        self.vpc: VPC = vpc
        self.cloudfront: Cloudfront = cloudfront

    def generate_config(self):
        raise NotImplementedError()


class LowLevelStorageItem(LowLevelAWSItem):
    def __init__(self, new_id: str):
        super().__init__(new_id)

    def generate_config(self):
        raise NotImplementedError()


class LowLevelDBItem(LowLevelAWSItem):
    def __init__(self, new_id: str, vpc: VPC):
        super().__init__(new_id)
        self.vpc = vpc

    def generate_config(self):
        raise NotImplementedError()


class EC2(LowLevelComputeItem):
    def __init__(self, new_id, vpc: VPC, cloudfront: Cloudfront):
        super().__init__(new_id, vpc, cloudfront)
        self.lb: ALB = ALB(generate_id())


class RDS(LowLevelDBItem):
    pass


class S3(LowLevelStorageItem):
    def __init__(self, new_id: str, templates: ServiceCategories):
        super().__init__(new_id)
        sub_templates = templates.get(ServiceCategory.WEBSITE_HOST, ServiceProvider.AWS, "static")
        print("sub_templates:")
        print(sub_templates)
        if sub_templates.template:
            self.template = Template(sub_templates.template)
        if sub_templates.outputs:
            self.outputs = Template(sub_templates.outputs)
        if sub_templates.variables:
            self.variables = Template(sub_templates.variables)
        self.cloudfront = Cloudfront(generate_id())
        self.cloudfront_www = Cloudfront(generate_id())

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
        cf1 = self.cloudfront.generate_config()
        if cf1.main:
            out_template += cf1.main
        if cf1.variables:
            out_variables += cf1.variables
        if cf1.outputs:
            out_outputs += cf1.outputs
        cf2 = self.cloudfront_www.generate_config()
        if cf2.main:
            out_template += cf2.main
        if cf2.variables:
            out_variables += cf2.variables
        if cf2.outputs:
            out_outputs += cf2.outputs
        return TerraformConfig(out_template, out_variables, out_outputs)


class TerraformGeneratorAWS:
    def __init__(self, ll_map: Dict[str, LowLevelAWSItem]):
        self.ll_map = ll_map

    def generate_string_template(self) -> str:
        out_template = ""
        out_variables = ""
        out_outputs = ""
        print(self.ll_map)
        for item in self.ll_map.values():
            print(item)
            config = item.generate_config()
            out_template += config.main
            out_variables += config.variables
            out_outputs += config.outputs
        return out_variables + out_template + out_variables


def generate_id() -> str:
    return uuid.uuid4().hex
