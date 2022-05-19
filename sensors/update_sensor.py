#!/usr/local/bin/python
# coding: utf8

import subprocess
import json

process = subprocess.Popen(['ssh', '-i', '.ssh/id_rsa', 'robert@rpn-home-server', '/usr/lib/update-notifier/apt-check', '2>&1'],
                           stdout=subprocess.PIPE,
                           universal_newlines=True)

while True:
    output = process.stdout.readline()
    if output:
        update_state = output.strip()
    return_code = process.poll()
    if return_code is not None:
        break

if update_state and return_code == 0:
    update_count, security_update_count = update_state.split(";")
    print(json.dumps({"total_updates": update_count, "security_updates": security_update_count}))
else:
    print("unavailable")
