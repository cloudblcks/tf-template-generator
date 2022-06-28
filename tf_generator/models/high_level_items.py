from enum import auto
from typing import List, Union, Dict

from strenum import LowercaseStrEnum

from models.low_level_items_aws import LowLevelAWSItem, LowLevelComputeItem, CloudblocksValidationException

HIGH_LEVEL_ITEM_TYPES = ["compute", "db", "storage", "internet"]


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
        raise CloudblocksValidationException("Unsupported binding direction")


HIGH_LEVEL_BINDING_DIRECTIONS = [x for x in HighLevelBindingDirection]


class HighLevelItem:
    def __init__(self, uid: str, bindings: List["HighLevelBinding"] = None):
        if bindings is None:
            bindings = []
        self.uid: str = uid
        self.bindings = bindings

    def needs_internet(self) -> bool:
        for item in self.bindings:
            if isinstance(item.item, HighLevelInternet):
                return True
        return False

    def linked_compute(self, input_map: Dict[str, LowLevelAWSItem]) -> List[LowLevelComputeItem]:
        out = []
        for x in self.bindings:
            if isinstance(x.item, HighLevelCompute) and x.item.uid in list(input_map):
                item = input_map[x.item.uid]
                assert isinstance(item, LowLevelComputeItem)
                out.append(item)
        return out


class HighLevelCompute(HighLevelItem):
    pass


class HighLevelDB(HighLevelItem):
    pass


class HighLevelStorage(HighLevelItem):
    pass


class HighLevelInternet(HighLevelItem):
    pass


HighLevelItemTypes = Union[HighLevelStorage, HighLevelCompute, HighLevelDB, HighLevelInternet]


class HighLevelBinding:
    def __init__(self, item: HighLevelItemTypes, direction: HighLevelBindingDirection):
        self.item = item
        self.direction = direction
