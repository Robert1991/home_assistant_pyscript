from ruamel.yaml import YAML
from os import path
from collections import OrderedDict

yaml = YAML()
yaml.preserve_quotes = True
yaml.indent(mapping=2, sequence=4, offset=2)


def write_yaml(file_path, yaml_dict):
    with open(file_path, "w") as file:
        yaml.dump(yaml_dict, file)


def read_yaml(file_path):
    if path.isfile(file_path):
        with open(file_path) as yaml_file:
            return yaml.load(yaml_file)
    return None


def write_yaml_ordered(file_path, yaml_dict):
    yaml_dict_ordered = OrderedDict(sorted(yaml_dict.items()))
    with open(file_path, "w") as file:
        for key, value in yaml_dict_ordered.items():
            yaml.dump({key: value}, file)
