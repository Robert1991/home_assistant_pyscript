from tools.entity import call_service_within_entity_domain
from tools.state import is_off
from tools.dict import replace_key_in_dict
from tools.scene import toggle_selected_scene

registered_button_controllers = {}


def setup_button_controller(config_name, configuration_dict):
    controlled_entity = configuration_dict["entity"]
    switch_sensor = configuration_dict["switch_sensor"]
    scene_input_select = configuration_dict["scene_input_select"]
    scene_prefix = configuration_dict["scene_prefix"]

    @task_unique(config_name + "_ikea_button_toggle_listener")
    @state_trigger(switch_sensor + " == 'toggle'")
    def toggle_entity(**kwargs):
        if is_off(controlled_entity):
            toggle_selected_scene(scene_input_select, scene_prefix)
        else:
            call_service_within_entity_domain(
                controlled_entity, "turn_off", entity_id=controlled_entity)

    @task_unique(config_name + "_ikea_button_arrow_right_listener")
    @state_trigger(switch_sensor + " == 'arrow_right_click'")
    def select_next_scene(**kwargs):
        call_service_within_entity_domain(
            scene_input_select, "select_next", entity_id=scene_input_select)
        task.sleep(0.5)
        toggle_selected_scene(scene_input_select, scene_prefix)

    @task_unique(config_name + "_ikea_button_arrow_left_listener")
    @state_trigger(switch_sensor + " == 'arrow_left_click'")
    def select_previous_scene(**kwargs):
        call_service_within_entity_domain(
            scene_input_select, "select_previous", entity_id=scene_input_select)
        task.sleep(0.5)
        toggle_selected_scene(scene_input_select, scene_prefix)

    return [toggle_entity, select_next_scene, select_previous_scene]


@ time_trigger
@ task_unique("ikea_button_controller_app")
def setup_button_controller_app():
    global registered_state_observer_triggers

    log.info("Setting up ikea button controller app")
    for app_config_part in pyscript.app_config:
        button_controller_config_name = list(app_config_part.keys())[0]
        button_controller_configuration_dict = app_config_part[button_controller_config_name]

        button_controller = setup_button_controller(
            button_controller_config_name, button_controller_configuration_dict)

        replace_key_in_dict(
            registered_button_controllers, button_controller_config_name, button_controller)
