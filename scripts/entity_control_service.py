@service
def toggle_entity_with_state_ensurance(entity="light.test", target_state="off", retry_timeout=3, retry_count=3):
    toggle_command = entity + ".turn_" + target_state + "()"
    log.info("Toggling '" + entity + "' with command line: " + toggle_command)
    eval(toggle_command)

    current_try = 1
    while True:
        task.sleep(retry_timeout)
        if is_entity_in_state(entity, target_state):
            log.info("Sucessesfully toggled '" + entity +
                     "' to target state '" + target_state + "'")
            break
        if current_try == retry_count:
            log.error("Failed to toggle entity '" + entity + "' to target_state '" +
                      target_state + "' within given retry configuration")
            break
        eval(toggle_command)
        log.info("Failed to toggle entity '" + entity + "' to target_state '" +
                 target_state + "' retrying in " + str(retry_count) + " Seconds...")
        current_try = current_try + 1


def is_entity_in_state(entity, target_state):
    return state.get(entity) == target_state
