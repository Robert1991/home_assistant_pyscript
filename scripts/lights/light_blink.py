from tools.state import is_entity_in_state


@service
def light_blink(entity=None, state_entity=None, target_state="on", blink_timeout=1):
    former_state = state.get(entity)
    while is_entity_in_state(state_entity, target_state):
        light.turn_on(entity_id=entity)
        task.sleep(blink_timeout)
        light.turn_off(entity_id=entity)
        task.sleep(blink_timeout)
    log.info("finished blinking, returning to former state: " + former_state)
    if former_state == "on":
        light.turn_on(entity_id=entity)
        return
    light.turn_off(entity_id=entity)
