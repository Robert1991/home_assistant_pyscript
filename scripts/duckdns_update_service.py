import requests


@pyscript_compile
def send_get_request(url):
    return requests.get(url)


@service
def update_duckdns_ipaddress(duckdns_domain="duckdns_domain", external_ip_provider="sensor.some_sensor", duckdns_token="some duckdns token"):
    current_ip_address = state.get(external_ip_provider)
    duckdns_ip_address_update_url = "https://www.duckdns.org/update?domains=" + \
        duckdns_domain + "&token=" + duckdns_token + "&ip=" + current_ip_address

    update_response = task.executor(
        send_get_request, duckdns_ip_address_update_url)
    if update_response.status_code != 200:
        log.error(
            "Unable to update duckdns ip: status_code: " + update_response.status_code + ", text: " + update_response.text)
    else:
        log.info("successfully updated ip address for duckdns domain")
