
def is_entity_in_state(entity, target_state):
    return state.get(entity) == target_state


def is_on(entity):
    return is_entity_in_state(entity, "on")


def is_off(entity):
    return is_entity_in_state(entity, "off")
