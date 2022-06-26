from abc import abstractmethod
from enum import Enum, auto

from strenum import LowercaseStrEnum

from models.low_level_items_aws import LowLevelAWSItem, LowLevelComputeItem


class HighLevelItemType(LowercaseStrEnum):
    COMPUTE = auto()
    DB = auto()
    STORAGE = auto()
    INTERNET = auto()


HIGH_LEVEL_ITEM_TYPES = [x for x in HighLevelItemType]


class HighLevelBindingDirection(LowercaseStrEnum):
    TO = auto()
    FROM = auto()
    BOTH = auto()

    @staticmethod
    def match_string(string: str) -> "HighLevelBindingDirection":
        if string == "to":
            return HighLevelBindingDirection.TO
        elif string == "from":
            return HighLevelBindingDirection.FROM
        elif string == "both":
            return HighLevelBindingDirection.BOTH


HIGH_LEVEL_BINDING_DIRECTIONS = [x for x in HighLevelBindingDirection]


class HighLevelItem:
    def __init__(self, _id: str, bindings: ["HighLevelBinding"] = None):
        if bindings is None:
            bindings = []
        self._id: str = _id
        self.bindings: ["HighLevelItem"] = bindings

    def needs_internet(self) -> bool:
        for _, item in self.bindings:
            if item.gettype == HighLevelItemType.INTERNET:
                return True
        return False

    def linked_compute(self, input_map: {str: LowLevelAWSItem}) -> [LowLevelComputeItem]:
        out = []

        for x in self.bindings.values():
            if x.gettype == HighLevelItemType.COMPUTE and x._id in list(input_map):
                out.append(input_map[x._id])
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
