import json
import uuid


class LowLevelAWSItem:
    def __init__(self, new_id: str):
        self.id: str = new_id

    def generate_cdktf_config(self):
        raise NotImplementedError()


class LowLevelInfraItem(LowLevelAWSItem):
    def generate_cdktf_config(self):
        raise NotImplementedError()


class VPC(LowLevelInfraItem):
    pass


class ALB(LowLevelInfraItem):
    pass


class Cloudfront(LowLevelInfraItem):
    pass


class LowLevelComputeItem(LowLevelAWSItem):
    def __init__(self, new_id: str, vpc: VPC, cloudfront: Cloudfront):
        super().__init__(new_id)
        self.vpc: VPC = vpc
        self.cloudfront: Cloudfront = cloudfront

    def generate_cdktf_config(self):
        raise NotImplementedError()


class LowLevelStorageItem(LowLevelAWSItem):
    def __init__(self, new_id: str, cloudfront: Cloudfront):
        super().__init__(new_id)
        self.cloudfront: Cloudfront = cloudfront

    def generate_cdktf_config(self):
        raise NotImplementedError()


class LowLevelDBItem(LowLevelAWSItem):
    def __init__(self, new_id: str, vpc: VPC):
        super().__init__(new_id)
        self.vpc = vpc

    def generate_cdktf_config(self):
        raise NotImplementedError()


class EC2(LowLevelComputeItem):
    def __init__(self, new_id, vpc: VPC, cloudfront: Cloudfront):
        super().__init__(new_id, vpc, cloudfront)
        self.lb: ALB = ALB(generate_id())


class RDS(LowLevelDBItem):
    pass


class S3(LowLevelStorageItem):
    pass


class TerraformStackGeneratorAWS:
    def __init__(self, ll_map: {str: LowLevelAWSItem}):
        self.ll_map = ll_map

    def generate_string_template(self) -> str:
        return str(json.dumps(self.ll_map))


def generate_id() -> str:
    return uuid.uuid4().hex
