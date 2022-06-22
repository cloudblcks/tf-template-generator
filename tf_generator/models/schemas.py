from typing import Dict

from schema import Schema, And, Use, Optional, Or

from models.high_level_items import HIGH_LEVEL_ITEM_TYPES

MAP_SCHEMA = Schema(
    {
        "cloudblocks_data": [
            {
                "clbksType": And(Use(str), lambda s: s in HIGH_LEVEL_ITEM_TYPES),
                "clbksId": Use(str),
                Optional("bindings"): [
                    Optional(
                        {
                            "id": Use(str),
                            "direction": And(Use(str), lambda s: s in ("to", "from")),
                        }
                    )
                ],
                Optional("params"): Or({str: object}, {}),
            }
        ]
    }
)
