from typing import Union, Tuple, List, Dict

import cli


def handle(version: str, action: str, data: Dict) -> Tuple[Union[str, List[str]], int]:
    if version == "1.0":
        if action == "validate":
            valid, results = cli._validate(data, verbose=True)

            if not valid:
                return results, 422
        elif action == "build":
            results = [line for line in cli._build(data).split("\n")]

        elif action == "search":
            search_results = cli._search(data.get("keyword"), data.get("cloud"), data.get("tags"))
            if data.get("keys_only"):
                results = [resource.key for resource in search_results]
            else:
                results = [result.to_json() for result in search_results]

        else:
            return f"Command {action} not recognised", 404

    else:
        return f"Unrecognised command version {version}", 403

    return results, 200
