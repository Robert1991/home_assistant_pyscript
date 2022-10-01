#!/usr/local/bin/python
# coding: utf8
import yaml
import json
import datetime
from os.path import exists


harvest_data_file = "/config/tmp/harvest.yaml"

if exists(harvest_data_file):
    with open(harvest_data_file) as data_file:
        all_harvest_data = yaml.safe_load(data_file)

        overall_harvest = 0.0
        latest_harvest = None
        last_plant = None
        last_amount = None
        for harvest_data in all_harvest_data["harvest"]:
            harvest_time_stamp = datetime.datetime.strptime(
                harvest_data["date"], "%Y-%m-%d")

            if latest_harvest is None or harvest_time_stamp >= latest_harvest:
                latest_harvest = harvest_time_stamp
                last_harvest = harvest_data

            overall_harvest = overall_harvest + \
                float(harvest_data["amount"])
        print(json.dumps(({"overall": round(overall_harvest),
                           "harvested_count": len(all_harvest_data["harvest"]),
                           "last": last_harvest, "harvests": all_harvest_data["harvest"]})))
        exit(0)
print("unavailable")
exit(0)
