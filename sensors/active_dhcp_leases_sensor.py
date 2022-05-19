#!/usr/local/bin/python
# coding: utf8
import yaml
import json
from os.path import exists

if exists('/config/tmp/active_dhcp_leases.yaml'):
    with open('/config/tmp/active_dhcp_leases.yaml') as data_file:
        active_dhcp_leases = yaml.safe_load(data_file)
        lease_count = len(active_dhcp_leases["leases"])
        leases = []
        for lease in active_dhcp_leases["leases"]:
            leases.append(lease)

        print(json.dumps({"count": lease_count,
                          "leases": leases}))
        exit()
print("unavailable")
