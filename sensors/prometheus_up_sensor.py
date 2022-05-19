#!/usr/local/bin/python
# coding: utf8
import json
import requests

server_up_request = json.loads(requests.get(
    "http://rpn-home-server:9090/api/v1/query?query=up").text)

if server_up_request["status"] == "success" and server_up_request["data"]["resultType"] == "vector":
    server_up_request_result = []
    for result in server_up_request["data"]["result"]:
        server_up_request_result.append(
            {"name": result["metric"]["job"], "up": result["value"][1]})
    print(json.dumps(server_up_request_result))
else:
    print("unavailable")
