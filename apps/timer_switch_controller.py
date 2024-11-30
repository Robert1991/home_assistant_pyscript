switch_controller_toggles = []
switch_controllers_timer_toggles = []


def read_state(switch_entity, timer_entity, timeout_entity):
    switch_state = state.get(switch_entity)
    timer_state = state.get(timer_entity)
    timeout = int(float(state.get(timeout_entity)))*60
    return switch_state, timer_state, timeout

def setup_button_sensor(switch_entity, button_sensor, timer_entity, timeout_entity):
    @task_unique("switch_controller_observer_" + button_sensor)
    @state_trigger(button_sensor + " == 'press'")
    def toggle_switch(**kwargs):
        switch_state, timer_state, timeout = read_state(
            switch_entity, timer_entity, timeout_entity)

        if switch_state == "off" and timer_state == "idle":
            switch.turn_on(entity_id=switch_entity)
        elif switch_state == "on" and timer_state == "idle":
            switch.turn_off(entity_id=switch_entity)
            timer.start(duration=timeout, entity_id=timer_entity)
        elif switch_state == "off" and timer_state == "active":
            switch.turn_on(entity_id=switch_entity)
            timer.cancel(entity_id=timer_entity)

    return toggle_switch

def setup_switch_controller(switch_entity, timer_entity, timeout_entity):
    @task_unique("switch_controller_observer_" + switch_entity)
    @state_trigger(switch_entity)
    def toggle_timer(**kwargs):
        switch_state, timer_state, timeout = read_state(
            switch_entity, timer_entity, timeout_entity)
        
        log.info(f"Switch '{switch_entity}' changed state: {switch_state}")
        if switch_state == "on" and timer_state == "active":
            log.info(f"Cancelling timer: {timer_entity}")
            timer.cancel(entity_id=timer_entity)
        elif switch_state == "off" and timer_state == "idle":
            log.info(f"Starting timer '{timer_entity}' with timeout: {timeout}")
            timer.start(duration=timeout, entity_id=timer_entity)

    @task_unique("switch_controller_" + switch_entity + "_timer_event_handler")
    @event_trigger("timer.finished", "entity_id == '" + timer_entity + "'")
    def toggle_switch_on_timer_finish(**kwargs):
        log.info(f"Timer {timer_entity} elapsed, turning swtich entity back on: {switch_entity}")
        switch.turn_on(entity_id=switch_entity)

    return toggle_timer, toggle_switch_on_timer_finish


@time_trigger
def setup_switch_controllers():
    global switch_controller_toggles
    global switch_controllers_timer_toggles

    for switch_controller in pyscript.app_config:
        log.info(f"Setting up switch controller for: {switch_controller}")
        
        if "button_sensor" in switch_controller:
            log.info(f"Starting button observation for button sensor: {switch_controller["button_sensor"]}")
            button_controller_toggle_func = setup_button_sensor(
                switch_controller["switch_entity"], switch_controller["button_sensor"], switch_controller["timer_entity"], switch_controller["timeout_entity"])
            switch_controller_toggles.append(button_controller_toggle_func)

        log.info(f"Starting switch observation for switch: {switch_controller["switch_entity"]}")
        switch_controller_toggle_func, switch_controller_timer_toggle_func = setup_switch_controller(
            switch_controller["switch_entity"], switch_controller["timer_entity"], switch_controller["timeout_entity"])
        switch_controller_toggles.append(switch_controller_toggle_func)
        switch_controllers_timer_toggles.append(switch_controller_timer_toggle_func)
