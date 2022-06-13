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
        self.lb: ALB = ALB(generateId())


class RDS(LowLevelDBItem):
    pass


class S3(LowLevelStorageItem):
    pass


def generateId() -> str:
    return uuid.uuid4().hex
