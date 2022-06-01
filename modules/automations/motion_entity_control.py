
def create_motion_entity_control(entity, motion_sensor_entity, automation_enabled_entity, turn_off_timeout_entity, timer_entity,
                                 turn_on_function, turn_off_function, turn_on_condition=None):
    motion_entity_control_id = "motion_entity_control_" + entity

    @task_unique(motion_entity_control_id + "_motion_trigger")
    @state_trigger(motion_sensor_entity + " == 'on'")
    def on_motion_detected():
        if automation_enabled_entity:
            automation_enabled = state.get(automation_enabled_entity)
            if automation_enabled == "off":
                log.info("skipping automation on " + entity + " as " +
                         automation_enabled_entity + " set to off")
                return
        if state.get(entity) == "on":
            if state.get(timer_entity) == "active":
                log.info("stopping timer " + timer_entity +
                         " because movement was detected by " + motion_sensor_entity)
                timer.cancel(entity_id=timer_entity)
            return
        if turn_on_condition and not turn_on_condition():
            log.info("skip turning on " + entity +
                     " as turn on condition was not met")
            return
        turn_on_function()

    @task_unique(motion_entity_control_id + "_motion_trigger")
    @state_trigger(motion_sensor_entity + " == 'off'")
    def on_motion_cleared():
        if state.get(entity) == "on":
            turn_off_timeout = state.get(turn_off_timeout_entity)
            log.info("starting turn off timer with turn off timeout { "
                     + turn_off_timeout_entity + ": " + turn_off_timeout +
                     " } because no movement was detected by " + motion_sensor_entity)
            timer.start(entity_id=timer_entity,
                        duration=turn_off_timeout)

    @task_unique(motion_entity_control_id + "_entity_manual_off_trigger")
    @state_trigger(entity + " == 'off'")
    def kill_timer_after_entity_was_turned_off_manually():
        if state.get(timer_entity) == "active":
            log.info("stopping " + timer_entity + " as entity " +
                     entity + " was turned off manually.")
            timer.cancel(entity_id=timer_entity)

    @task_unique(motion_entity_control_id + "_timer_trigger")
    @event_trigger("timer.finished", "entity_id == '" + timer_entity + "'")
    def turn_off_entity_after_timer_finish(**kwargs):
        log.info(f"got timer.finished from " + timer_entity +
                 ". executing turn off: " + entity)
        turn_off_function()

    return motion_entity_control_id, {on_motion_detected, on_motion_cleared, kill_timer_after_entity_was_turned_off_manually, turn_off_entity_after_timer_finish}
