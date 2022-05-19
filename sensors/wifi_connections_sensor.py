#!/usr/local/bin/python
# coding: utf8
import yaml
import json
from os.path import exists

if exists('/config/tmp/connected_wifi_clients.yaml'):
    with open('/config/tmp/connected_wifi_clients.yaml') as data_file:
        connected_wifi_client_data = yaml.safe_load(data_file)
        connection_count = len(connected_wifi_client_data["connected"])
        print(json.dumps({"connection_count": connection_count,
                          "connections": connected_wifi_client_data["connected"]}))
        exit()
print("unavailable")
