from tools.ssh_shell import run_remote_shell_command


@service
def update_all_esp_home_devices():
    for esp_home_device in state.getattr("input_select.esp_home_devices")["options"]:
        device_file = esp_home_device + ".yaml"
        log.info("Invoking esp home update for: " + device_file)
        pyscript.run_esp_home_device_update(esp_home_device_config=device_file)


@service
def run_esp_home_device_update(esp_home_device_config):
    esp_home_base_path = pyscript.config["global"]["esp_home_automations"]["esp_home_base_path"]

    esp_home_device_docker_run_command = "docker run --rm -v " + esp_home_base_path + ":/config esphome/esphome " \
        + esp_home_device_config + " run --no-logs"
    log.info("Running esp-home update for: '" + esp_home_device_config +
             "' with command line: " + esp_home_device_docker_run_command)
    command_result = task.executor(
        run_remote_shell_command,
        esp_home_device_docker_run_command,
        pyscript.config["global"]["host_server"]["ssh_login"],
        pyscript.config["global"]["host_server"]["ssh_key"])
    if command_result.returncode != 0:
        log.error("Running esp home update for " +
                  esp_home_device_config + " failed:\\n" + str(command_result.stderr))
        notify.persistent_notification(title="ESP Home Device Update Failed", message="Device update for " +
                                       esp_home_device_config + " failed. Check logs for more information.")
    else:
        log.info("esp home device update for " +
                 esp_home_device_config + " was successful")
        notify.persistent_notification(title="ESP Home Device Update Successfull", message="Device update for " +
                                       esp_home_device_config + " was successful.")
