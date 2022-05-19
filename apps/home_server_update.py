registered_triggers = []


@time_trigger
def setup_update_trigger():
    global registered_triggers

    @state_trigger("binary_sensor.home_server_updates_available == 'on'")
    def trigger_home_server_update(**kwargs):
        notify.persistent_notification(
            title="Host Server Update triggered", message="Check log files for further infomation")
        pyscript.update_host_machine(
            apt_log_file_path=pyscript.app_config["update_log"])

    registered_triggers.append([trigger_home_server_update])
    log.info("registered host server update")
