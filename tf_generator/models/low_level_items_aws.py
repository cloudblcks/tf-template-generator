import json
import uuid


class LowLevelAWSItem:
    def __init__(self, new_id: str):
        self.id: str = new_id


class LowLevelInfraItem(LowLevelAWSItem):
    pass


class VPC(LowLevelInfraItem):
    pass


class ALB(LowLevelInfraItem):
    pass


class Cloudfront(LowLevelInfraItem):
    pass


class LowLevelComputeItem(LowLevelAWSItem):
    cloudfront: Cloudfront
    vpc: VPC


class LowLevelStorageItem(LowLevelAWSItem):
    cloudfront: Cloudfront


class LowLevelDBItem(LowLevelAWSItem):
    vpc: VPC


class EC2(LowLevelComputeItem):
    def __init__(self, new_id):
        super().__init__(new_id)
        self.lb: ALB = ALB(generate_id())


class RDS(LowLevelDBItem):
    pass


class S3(LowLevelStorageItem):
    pass


class TerraformGeneratorAWS:
    def __init__(self, ll_map: {str: LowLevelAWSItem}):
        self.ll_map = ll_map

    def generate_string_template(self) -> str:
        return str(json.dumps(self.ll_map))


def generate_id() -> str:
    return uuid.uuid4().hex
