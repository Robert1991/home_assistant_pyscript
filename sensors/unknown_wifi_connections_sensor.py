#!/usr/local/bin/python
# coding: utf8

import yaml
import json


def read_yaml_file(file_path):
    with open(file_path) as file_handle:
        try:
            return yaml.safe_load(file_handle)
        except yaml.YAMLError as exc:
            return None


known_devices_file = read_yaml_file('/config/known_devices.yaml')
connected_devices_file = read_yaml_file(
    '/config/tmp/connected_wifi_clients.yaml')

if known_devices_file and connected_devices_file:
    unknown_devices = []

    for connected_device in connected_devices_file["connected"]:
        is_known = False
        for device in known_devices_file:
            known_device_info = known_devices_file[device]
            if known_device_info["mac"] == connected_device["mac_address"]:
                is_known = True
        if not is_known:
            unknown_devices.append(connected_device)

    if len(unknown_devices) > 0:
        print(json.dumps(
            {'unknown_present': 'on', 'devices': unknown_devices}))
    else:
        print(json.dumps({'unknown_present': 'off', 'devices': []}))
    exit(0)
else:
    print("unavailabe")
    exit(1)
