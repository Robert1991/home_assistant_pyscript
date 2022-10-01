entity_observers = []


def setup_entity_observer(entity_id, notification_timeout, message):
    @task_unique("entity_observer_" + entity_id)
    @state_trigger(entity_id + " == 'unavailable'")
    def notify_unavailable_state(**kwargs):
        while True:
            # notification comes here
            log.info("observed entity: " + entity_id +
                     " changed to unavailable state")
            trig_info = task.wait_until(
                state_trigger=entity_id + " != 'unavailable'",
                timeout=notification_timeout * 60)
            if trig_info["trigger_type"] != "timeout":
                log.info("observed entity: " + entity_id +
                         " is available again")
                break

    return notify_unavailable_state


@time_trigger
def setup_entity_unavailable_notification_service():
    global entity_observers
    entity_observers = []
    for entity_configuration in pyscript.app_config:
        log.info("Setting up entity unavailable service for " +
                 entity_configuration["entity"])
        entity_observers.append(
            setup_entity_observer(entity_configuration["entity"], entity_configuration["notify_every"], entity_configuration["message"]))
