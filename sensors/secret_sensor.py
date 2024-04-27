#!/usr/local/bin/python
# coding: utf8

import sys
import yaml

def read_secret(key):
    with open('/config/secrets.yaml', 'r') as file:
        secrets = yaml.safe_load(file)
        print(secrets.get(key, 'Secret not found'))

if len(sys.argv) != 2:
    print("Usage: python read_secret.py <key>")
    sys.exit(1)
read_secret(sys.argv[1])