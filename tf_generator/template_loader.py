from jinja2 import Template


def load_template(path: str) -> Template:
    with open(path, "r") as f:
        data = f.read()
        return Template(data)
