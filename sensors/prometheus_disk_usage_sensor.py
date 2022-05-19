#!/usr/local/bin/python
# coding: utf8
import json
import requests


def execute_query(prometheus_query):
    server_query_result = json.loads(requests.get(
        "http://rpn-home-server:9090/api/v1/query?query=" + prometheus_query).text)
    if server_query_result["status"] == "success" and server_query_result["data"]["resultType"] == "vector":
        return server_query_result["data"]["result"]
    return None


rpn_home_server_node = "job=\"rpn-home-server\""

available_bytes_query = "node_filesystem_avail_bytes{mountpoint=\"/\",fstype!=\"rootfs\", " + \
    rpn_home_server_node + "}"
available_bytes_query_result = execute_query(available_bytes_query)

file_system_bytes_query = "node_filesystem_size_bytes{mountpoint=\"/\",fstype!=\"rootfs\", " + \
    rpn_home_server_node + "}"
file_system_bytes_query_result = execute_query(file_system_bytes_query)

if available_bytes_query_result and file_system_bytes_query_result \
        and len(available_bytes_query_result) == 1 and len(file_system_bytes_query_result) == 1:
    available_bytes = int(available_bytes_query_result[0]["value"][1])
    file_system_bytes = int(file_system_bytes_query_result[0]["value"][1])
    disk_usage = 100 - ((available_bytes * 100) / file_system_bytes)

    print(json.dumps({"available_space": round(available_bytes/2**30, 2),
                      "filesystem_size": round(file_system_bytes/2**30, 2), "disk_usage": round(disk_usage, 2)}))
    exit(0)
print("unavailable")
exit(1)
