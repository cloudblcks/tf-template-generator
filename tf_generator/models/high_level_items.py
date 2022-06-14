from abc import abstractmethod
from enum import Enum

from low_level_items_aws import LowLevelAWSItem, LowLevelComputeItem


class HighLevelItemType(Enum):
    COMPUTE = 0
    DB = 1
    STORAGE = 2
    INTERNET = 3


class HighLevelBindingDirection(Enum):
    TO = 0
    FROM = 1
    BOTH = 2

    @staticmethod
    def match_string(string: str) -> "HighLevelBindingDirection":
        match string:
            case "to":
                return HighLevelBindingDirection.TO
            case "from":
                return HighLevelBindingDirection.FROM
            case "both":
                return HighLevelBindingDirection.BOTH


class HighLevelItem:
    def __init__(self, _id: str, bindings: ["HighLevelBinding"] = None):
        if bindings is None:
            bindings = []
        self.id: str = _id
        self.bindings: ["HighLevelItem"] = bindings

    def needs_internet(self) -> bool:
        for _, item in self.bindings:
            if item.gettype == HighLevelItemType.INTERNET:
                return True
        return False

    def linked_compute(self, input_map: {str: LowLevelAWSItem}) -> [LowLevelComputeItem]:
        out = []

        for x in self.bindings.values():
            if x.gettype == HighLevelItemType.COMPUTE and x.id in list(input_map):
                out.append(input_map[x.id])
        return out

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


class HighLevelBinding:
    def __init__(self, item: HighLevelItem, direction: HighLevelBindingDirection):
        self.item = item
        self.direction = direction
