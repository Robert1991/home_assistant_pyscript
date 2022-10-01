import requests
import json
from datetime import datetime


@pyscript_compile
def send_post_request(url, data):
    return requests.post(url, json.dumps(data), headers={"Content-Type": "application/json"})


@service
def send_heart_beat(heart_beat_receiver="foo.duckdns.org", webhook_id="some_id", retry_count=3):
    heart_beat_receiver_webhook_url = "https://" + \
        heart_beat_receiver + "/api/webhook/" + webhook_id
    heart_beat_data = {"time_stamp": str(datetime.now()),
                       "ip_address": state.get("sensor.fritz_box_7590_external_ip")}

    current_try = 0
    while current_try < retry_count:
        heart_beat_response = task.executor(
            send_post_request, heart_beat_receiver_webhook_url, heart_beat_data)
        try:
            if heart_beat_response.status_code != 200:
                log.error(
                    "Unable to send heart beat to: " + heart_beat_receiver +
                    ": status code: " + str(heart_beat_response.status_code)
                    + ", text: " + str(heart_beat_response.text))
                current_try = current_try + 1
            else:
                return
        except:
            log.error(
                "Unable to send heart beat to: " + heart_beat_receiver + "; connectivity exception received")
            current_try = current_try + 1
    log.error("Unable to send heart beat to  " + heart_beat_receiver + " in " +
              str(retry_count) + " attempts")
