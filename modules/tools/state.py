
def is_entity_in_state(entity, target_state):
    return state.get(entity) == target_state


def is_on(entity):
    return is_entity_in_state(entity, "on")


def is_off(entity):
    return is_entity_in_state(entity, "off")


def get_state_as_date_time(input_datetime_entity, format='%H:%M:%S'):
    return datetime.strptime(
        state.get(input_datetime_entity), format)


def get_seconds_from_input_number(input_number_entity):
    unit_of_measurement = state.getattr(input_number_entity)[
        "unit_of_measurement"]

    current_state = int(float(state.get(input_number_entity)))
    if unit_of_measurement == "h":
        return current_state*60*60
    if unit_of_measurement == "min":
        return current_state*60
    return current_state
