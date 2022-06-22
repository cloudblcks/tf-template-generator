from typing import Dict

from models.schemas import MAP_SCHEMA
from schema import SchemaError


def validate(data: Dict) -> bool:
    try:
        MAP_SCHEMA.validate(data)
    except SchemaError as e:
        print(e)
        return False
    return True
