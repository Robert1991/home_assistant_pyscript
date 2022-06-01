from tools.dict import replace_key_in_dict

registered_battery_observer_triggers = {}
registered_battery_observers = {}


def build_battery_observer_function(battery_observer, threshold_input_number):
    state_trigger_expression = "float(" + threshold_input_number + ") > " + \
        "float(" + battery_observer["entity"] + ")"

    @task_unique("battery_tracker_" + battery_observer["entity"])
    @state_trigger(state_trigger_expression)
    def battery_observer_function(**kwargs):
        while True:
            persistent_notification.create(title="Battery Low", message="Battery low on " +
                                           battery_observer["entity"] + " (" + state.get(battery_observer["entity"]) + "%)")
            reminder = task.wait_until(
                state_trigger="not (" + state_trigger_expression + " )",
                timeout=pyscript.app_config["reminder_timeout"] * 60)
            if reminder["trigger_type"] != "timeout":
                log.info("Battery alert resolved for " +
                         battery_observer["entity"])
                return

    return battery_observer_function


def build_setup_battery_observer_function(battery_observer, default_threshold_entity):
    if "threshold_entity" in battery_observer.keys():
        threshold_input_number = battery_observer["threshold_entity"]
    else:
        threshold_input_number = default_threshold_entity

    @task_unique("change_tracker_" + battery_observer["entity"])
    @time_trigger
    @state_trigger(threshold_input_number)
    def setup_battery_observer_trigger():
        log.info("Setting up battery observer trigger for: " +
                 threshold_input_number)
        battery_observer_function = build_battery_observer_function(
            battery_observer, threshold_input_number)
        replace_key_in_dict(
            registered_battery_observers, battery_observer["entity"], battery_observer_function)
    return setup_battery_observer_trigger


@time_trigger
def setup_battery_observers():
    global registered_battery_observer_triggers
    global registered_battery_observers

    log.info("Setting up battery observers")
    for observed_entity in pyscript.app_config["observed_entities"]:
        log.info("Setting up battery observer for: " +
                 observed_entity["entity"])
        setup_battery_observer_function = build_setup_battery_observer_function(
            observed_entity, pyscript.app_config["default_threshold_entity"])
        replace_key_in_dict(
            registered_battery_observer_triggers, observed_entity["entity"], setup_battery_observer_function)
