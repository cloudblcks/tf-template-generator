from typing import Dict, Tuple

from schema import SchemaError

from models.schemas import MAP_SCHEMA


def validate(data: Dict) -> Tuple[bool, str]:
    try:
        MAP_SCHEMA.validate(data)
    except SchemaError as e:
        return False, e.code
    return True, ""
