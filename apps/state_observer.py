registered_state_observer_triggers = {}
registered_state_observer_change_triggers = {}


def execute_service_call(service_call):
    domain, name = service_call["service"].split('.')
    service_call["arguments"]
    service.call(domain, name, **service_call["arguments"])


def get_from_state_observer_config(config_key, argument):
    return pyscript.app_config[config_key][argument]


def calculate_timeout(time_out_entity):
    unit = state.getattr(time_out_entity)["unit_of_measurement"]
    timeout = int(
        float(state.get("input_number.kitchen_frigde_door_open_alarm_timeout")))

    if unit and unit != "s":
        if unit == "min":
            return timeout * 60
        if unit == "h":
            return timeout * 60 * 60
    return timeout


def build_trigger_state_expression(state_observer_key):
    return get_from_state_observer_config(state_observer_key, "observed_entity") \
        + " == '" + get_from_state_observer_config(state_observer_key, "observed_state") \
        + "'"


def build_resolved_state_expression(state_observer_key):
    return get_from_state_observer_config(state_observer_key, "observed_entity") \
        + " != '" + get_from_state_observer_config(state_observer_key, "observed_state") \
        + "'"


def build_state_observer_trigger_function(state_observer_key):
    if "timeout_input_number" in pyscript.app_config[state_observer_key]:
        state_hold_time_out = calculate_timeout(
            get_from_state_observer_config(state_observer_key, "timeout_input_number"))
    else:
        state_hold_time_out = 0

    trigger_state_expression = build_trigger_state_expression(
        state_observer_key)
    resolved_state_expression = build_resolved_state_expression(
        state_observer_key)

    @task_unique("state_tracker_" + state_observer_key)
    @state_trigger(trigger_state_expression, state_hold=state_hold_time_out)
    def state_observer_trigger(**kwargs):
        for action in get_from_state_observer_config(state_observer_key, "actions"):
            execute_service_call(action)
        task.wait_until(state_trigger=resolved_state_expression)

        for action in get_from_state_observer_config(state_observer_key, "state_resolved_actions"):
            execute_service_call(action)
    return state_observer_trigger


def build_setup_state_observer_function_with_timeout_observation(state_observer_key, timeout_input_number):
    @task_unique("change_tracker_" + state_observer_key)
    @time_trigger
    @state_trigger(timeout_input_number)
    def setup_observer_trigger():
        log.info("Setting state observer trigger for: " + state_observer_key)
        state_observer_function = build_state_observer_trigger_function(
            state_observer_key)
        replace_key_in_dict(
            registered_state_observer_triggers, state_observer_key, state_observer_function)
    return setup_observer_trigger


def build_setup_state_observer_function(state_observer_key):
    @task_unique("change_tracker_" + state_observer_key)
    @time_trigger
    def setup_observer_trigger():
        log.info("Setting state observer trigger for: " + state_observer_key)
        state_observer_function = build_state_observer_trigger_function(
            state_observer_key)
        replace_key_in_dict(
            registered_state_observer_triggers, state_observer_key, state_observer_function)
    return setup_observer_trigger


def replace_key_in_dict(dict, key, replace_object):
    if key in dict.keys():
        del dict[key]
    dict[key] = replace_object


@time_trigger
def setup_state_observers():
    global registered_state_observer_change_triggers
    global registered_state_observer_triggers
    log.info("Setting up state observers")

    for state_observer_key in pyscript.app_config.keys():
        state_observer = pyscript.app_config[state_observer_key]
        log.info("Setting up: " + state_observer_key)

        if "timeout_input_number" in state_observer.keys():
            setup_observer_function = build_setup_state_observer_function_with_timeout_observation(
                state_observer_key, state_observer["timeout_input_number"])
        else:
            setup_observer_function = build_setup_state_observer_function(
                state_observer_key)
        replace_key_in_dict(
            registered_state_observer_change_triggers, state_observer_key, setup_observer_function)
