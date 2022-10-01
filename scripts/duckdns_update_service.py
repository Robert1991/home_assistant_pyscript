import requests


@pyscript_compile
def send_get_request(url):
    return requests.get(url)


@service
def update_duckdns_ipaddress(duckdns_domain="homeofkarlfriedrich", duckdns_token="dbe685ca-1320-4e8b-9fec-7123ac7aba9d"):
    current_ip_address = state.get("sensor.fritz_box_7590_external_ip")

    duckdns_ip_address_update_url = "https://www.duckdns.org/update?domains=" + \
        duckdns_domain + "&token=" + duckdns_token + "&ip=" + current_ip_address

    update_response = task.executor(
        send_get_request, duckdns_ip_address_update_url)
    if update_response.status_code != 200:
        log.error(
            "Unable to update duckdns ip: status_code: " + update_response.status_code + ", text: " + update_response.text)
    else:
        log.info("successfully updated ip address for duckdns domain")
