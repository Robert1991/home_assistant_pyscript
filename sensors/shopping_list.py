#!/usr/local/bin/python
# coding: utf8
import json

with open('/config/.shopping_list.json') as data_file:
    shopping_list_data = json.load(data_file)

open_entries = []
for entry in shopping_list_data:
    if not entry['complete']:
        open_entries.append(entry['name'])

print(",".join(open_entries))