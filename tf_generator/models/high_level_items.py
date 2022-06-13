from abc import abstractmethod, ABC
from enum import Enum

from low_level_items_aws import LowLevelAWSItem, LowLevelComputeItem


class HighLevelItemType(Enum):
    COMPUTE = 0
    DB = 1
    STORAGE = 2
    INTERNET = 3


class HighLevelItem:
    def __init__(self, _id: str, bindings: {str: "HighLevelItem"} = None):
        if bindings is None:
            bindings = {}
        self.id: str = _id
        self.bindings: {str: "HighLevelItem"} = bindings

    def needs_internet(self) -> bool:
        for _, item in self.bindings:
            if item.gettype == HighLevelItemType.INTERNET:
                return True
        return False

    def linked_compute(self, input_map: {str: LowLevelAWSItem}) -> [LowLevelComputeItem]:
        return map(
            lambda x: input_map[x.id],
            filter(
                lambda x: x.gettype == HighLevelItemType.COMPUTE and x.id in list(input_map),
                list(self.bindings.values()),
            ),
        )

    @abstractmethod
    def gettype(self) -> HighLevelItemType:
        raise NotImplementedError()


class HighLevelCompute(HighLevelItem):
    def gettype(self) -> HighLevelItemType:
        return HighLevelItemType.COMPUTE


class HighLevelDB(HighLevelItem):
    def gettype(self) -> HighLevelItemType:
        return HighLevelItemType.DB


class HighLevelStorage(HighLevelItem):
    def gettype(self) -> HighLevelItemType:
        return HighLevelItemType.STORAGE


class HighLevelInternet(HighLevelItem):
    def gettype(self) -> HighLevelItemType:
        return HighLevelItemType.INTERNET
