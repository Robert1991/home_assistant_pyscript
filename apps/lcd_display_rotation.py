registered_lcd_display_rotation_trigger = None


def get_next_for_display_name(next_for_display):
    if "name_entity" in next_for_display:
        return state.get(next_for_display["name_entity"])
    return next_for_display["name"]


def format_message(next_for_display):
    display_message = get_next_for_display_name(next_for_display) + \
        ":\n" + state.get(next_for_display["entity"])
    if next_for_display["unit"]:
        unit = next_for_display["unit"].replace("\\\\", "\\")
        display_message = display_message + " " + unit
    return display_message


def rotate_display(lcd_display_mqtt_topic, enabled_state_entity, displayed_entities, lcd_rotation_timeout):
    displayed_entity_index = 0
    while state.get(enabled_state_entity) == "on":
        next_for_display = displayed_entities[displayed_entity_index]
        mqtt.publish(topic=lcd_display_mqtt_topic,
                     payload=format_message(next_for_display))

        displayed_entity_index = displayed_entity_index + 1
        if displayed_entity_index == len(displayed_entities):
            displayed_entity_index = 0
        task.sleep(int(float(lcd_rotation_timeout)))


@time_trigger
@task_unique("lcd_display_rotation_setup")
@state_trigger("" + pyscript.app_config["rotation_enabled_entity"] + " == 'on'")
@state_trigger(pyscript.app_config["rotate_timeout_entity"])
def setup_lcd_display_rotation():
    global registered_lcd_display_rotation_trigger

    @task_unique("lcd_display_rotation")
    @time_trigger
    def lcd_display_rotation():
        rotation_timeout_entity = pyscript.app_config["rotate_timeout_entity"]
        displayed_entities = pyscript.app_config["displayed_entities"]
        lcd_display_mqtt_topic = pyscript.app_config["display_topic"]
        enabled_state_entity = pyscript.app_config["rotation_enabled_entity"]
        log.info("setting up lcd display rotation for mqtt topic: " +
                 str(lcd_display_mqtt_topic) + "(rotation_timeout_entity: " + rotation_timeout_entity + ")")
        rotate_display(lcd_display_mqtt_topic,
                       enabled_state_entity, displayed_entities, state.get(rotation_timeout_entity))
    registered_lcd_display_rotation_trigger = lcd_display_rotation
