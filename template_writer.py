def write(path: str, template: str):
    with open(path, "w") as f:
        f.write(template)
