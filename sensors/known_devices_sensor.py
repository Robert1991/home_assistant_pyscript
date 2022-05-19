#!/usr/local/bin/python
# coding: utf8
import yaml
import json
from os.path import exists

if exists('/config/known_devices.yaml'):
    with open('/config/known_devices.yaml') as data_file:
        known_devices = yaml.safe_load(data_file)
        device_count = len(known_devices.keys())
        devices = []
        for key in known_devices.keys():
            devices.append(known_devices[key])
        print(json.dumps({"count": device_count,
                          "devices": devices}))
        exit()
print("unavailable")
