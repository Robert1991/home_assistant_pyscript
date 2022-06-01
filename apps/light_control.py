from datetime import datetime
from automations.motion_entity_control import create_motion_entity_control
from tools.dict import get_logged_app_parameter_if_exists
from tools.dict import replace_key_in_dict
from tools.state import is_on, is_off

state_trackers = {}
time_triggers = {}
motion_triggers = {}


def get_state_as_date_time(input_datetime_entity, format='%H:%M:%S'):
    return datetime.strptime(
        state.get(input_datetime_entity), format)


def get_scene_toggle_time(time_switch_configuration):
    input_datetime_entity, _ = time_switch_configuration.split("/")
    return "input_datetime." + input_datetime_entity


def get_scene_input_select(time_switch_configuration):
    _, input_select_entity = time_switch_configuration.split("/")
    return "input_select." + input_select_entity


def normalize_scene_name(scene_group_prefix, scene_name):
    return "scene." + scene_group_prefix + "_" + scene_name.lower().replace(" ", "_")


def toggle_light_scene(scene_toggle_input_select, current_light_scene, light_group_entity,
                       scene_group_prefix):
    log.info("toggling " + scene_toggle_input_select +
             " to " + current_light_scene)
    input_select.select_option(
        entity_id=scene_toggle_input_select, option=current_light_scene)
    if is_on(light_group_entity):
        current_scene_entity_id = normalize_scene_name(
            scene_group_prefix, current_light_scene)
        log.info("turning on scene " + current_scene_entity_id)
        scene.turn_on(entity_id=current_scene_entity_id)


def determine_closest_beginning_light_scene(time_to_scene_selects):
    current_time_stamp = datetime.now()
    current_latest_time_scene_time = None
    current_latest_time_scene = None
    for time_to_scene_select in time_to_scene_selects:
        input_datetime_entity = get_scene_toggle_time(time_to_scene_select)
        scene_start_time = get_state_as_date_time(input_datetime_entity)

        if scene_start_time.time() < current_time_stamp.time():
            if not current_latest_time_scene or (scene_start_time > current_latest_time_scene_time):
                input_select_entity = get_scene_input_select(
                    time_to_scene_select)
                current_latest_time_scene = state.get(input_select_entity)
                current_latest_time_scene_time = scene_start_time
    return current_latest_time_scene


def determine_latest_beginning_light_scene(time_to_scene_selects):
    current_latest_time = None
    current_latest_time_scene = None
    for time_to_scene_select in time_to_scene_selects:
        input_datetime_entity = get_scene_toggle_time(time_to_scene_select)
        scene_start_time = get_state_as_date_time(input_datetime_entity)

        if not current_latest_time or current_latest_time < scene_start_time:
            current_latest_time = scene_start_time
            input_select_entity = get_scene_input_select(
                time_to_scene_select)
            current_latest_time_scene = state.get(input_select_entity)
    return current_latest_time_scene


def create_time_trigger_execution_function(time_switch_configuration, light_group_entity, scene_toggle_input_select,
                                           scene_group_prefix, automation_enabled_entity):
    input_datetime_entity = get_scene_toggle_time(time_switch_configuration)
    time_trigger_id = "time_trigger_" + input_datetime_entity

    @task_unique(time_trigger_id)
    @time_trigger("once(" + state.get(input_datetime_entity) + ")")
    def execute_on_time_trigger(**kwargs):
        input_datetime_entity = get_scene_toggle_time(
            time_switch_configuration)
        log.info("executing time trigger for " + input_datetime_entity)
        if is_off(automation_enabled_entity):
            log.info("Skip setting as automation is disabled for " +
                     input_datetime_entity)
            return

        input_select_entity = get_scene_input_select(time_switch_configuration)
        current_light_scene = state.get(input_select_entity)
        toggle_light_scene(scene_toggle_input_select,
                           current_light_scene,
                           light_group_entity,
                           scene_group_prefix)
    return time_trigger_id, execute_on_time_trigger


def create_refresh_time_trigger_function(time_switch_configuration, light_group_entity, scene_toggle_input_select,
                                         time_to_scene_selects, scene_group_prefix, automation_enabled_entity):
    input_datetime_entity = get_scene_toggle_time(time_switch_configuration)
    input_select_entity = get_scene_input_select(time_switch_configuration)
    state_tracker_id = "state_tracker_" + input_datetime_entity
    log.info("setting up state tracker: " + state_tracker_id)

    @task_unique(state_tracker_id)
    @state_trigger(input_datetime_entity)
    @state_trigger(input_select_entity)
    @state_trigger(automation_enabled_entity)
    @time_trigger
    def refresh_time_trigger(**kwargs):
        input_datetime_entity = get_scene_toggle_time(
            time_switch_configuration)
        log.info("Refreshing time trigger for " + input_datetime_entity)
        time_trigger_id, time_trigger_execution = create_time_trigger_execution_function(time_switch_configuration,
                                                                                         light_group_entity,
                                                                                         scene_toggle_input_select,
                                                                                         scene_group_prefix,
                                                                                         automation_enabled_entity)
        replace_key_in_dict(time_triggers, time_trigger_id,
                            time_trigger_execution)
        if is_off(automation_enabled_entity):
            log.info("Skip setting as automation is disabled for " +
                     input_datetime_entity)
            return
        current_light_scene = determine_closest_beginning_light_scene(
            time_to_scene_selects)
        if not current_light_scene:
            current_light_scene = determine_latest_beginning_light_scene(
                time_to_scene_selects)
        toggle_light_scene(scene_toggle_input_select,
                           current_light_scene,
                           light_group_entity,
                           scene_group_prefix)

    return state_tracker_id, refresh_time_trigger


def is_light_intensity_sufficient(light_intensity_control):
    light_sensor_entity = light_intensity_control["light_sensor_entity"]
    threshold_entity = light_intensity_control["threshold_entity"]
    current_light_sensor_value = float(state.get(light_sensor_entity))
    current_threshold_value = float(state.get(threshold_entity))
    if current_light_sensor_value > current_threshold_value:
        log.info("light intensity sufficient: " +
                 "{ " + light_sensor_entity +
                 ": " + str(current_light_sensor_value) +
                 " } higher than threshold { " + threshold_entity +
                 ": " + str(current_threshold_value) + " }")
        return True
    log.info("light intensity insufficient: " +
             "{ " + light_sensor_entity +
             ": " + str(current_light_sensor_value) +
             " } lower than threshold { " + threshold_entity +
             ":" + str(current_threshold_value) + " }")
    return False


def create_motion_triggered_scene_based_light_control(light_group_entity, motion_sensor_entity, motion_triggered_light_enabled_entity, turn_off_timer_entity,
                                                      turn_off_timeout_entity, light_intensity_control, current_scene_input_select, scene_group_prefix):
    def turn_on_light_scene_based():
        current_light_scene = state.get(current_scene_input_select)
        current_scene_entity_id = normalize_scene_name(
            scene_group_prefix, current_light_scene)
        log.info("turning on scene " + current_scene_entity_id +
                 " because movement was detected by " + motion_sensor_entity)
        scene.turn_on(entity_id=current_scene_entity_id)

    def light_intensity_turn_on_condition():
        if is_light_intensity_sufficient(light_intensity_control):
            log.info("skip turning on " + light_group_entity +
                     " as light was determined to be sufficient")
            return False
        return True

    def turn_off_function():
        light.turn_off(entity_id=light_group_entity)

    return create_motion_entity_control(light_group_entity,
                                        motion_sensor_entity,
                                        motion_triggered_light_enabled_entity,
                                        turn_off_timeout_entity,
                                        turn_off_timer_entity,
                                        turn_on_light_scene_based,
                                        turn_off_function,
                                        light_intensity_turn_on_condition)


def create_motion_triggered_light_control(light_group_entity, motion_sensor_entity, motion_triggered_light_enabled_entity, turn_off_timer_entity,
                                          turn_off_timeout_entity):
    def turn_on_light():
        log.info("turning on " + light_group_entity +
                 " because movement was detected by " + motion_sensor_entity)
        light.turn_on(light_group_entity)

    def turn_off_light():
        light.turn_off(entity_id=light_group_entity)

    return create_motion_entity_control(light_group_entity,
                                        motion_sensor_entity,
                                        motion_triggered_light_enabled_entity,
                                        turn_off_timeout_entity,
                                        turn_off_timer_entity,
                                        turn_on_light,
                                        turn_off_light,
                                        None)


class LightControlConfig:
    def __init__(self, config_name, light_control_config):
        self.config_name = config_name
        self.light_group_entity = get_logged_app_parameter_if_exists(
            light_control_config, "light_group_entity")
        self.motion_sensor_entity = get_logged_app_parameter_if_exists(
            light_control_config, "motion_sensor_entity")
        self.motion_triggered_light_enabled_entity = get_logged_app_parameter_if_exists(
            light_control_config, "motion_triggered_light_enabled_entity")
        self.turn_off_timeout_entity = get_logged_app_parameter_if_exists(
            light_control_config, "turn_off_timeout_entity")
        self.turn_off_timer_entity = get_logged_app_parameter_if_exists(
            light_control_config, "turn_off_timer_entity")

        self.light_intensity_control = get_logged_app_parameter_if_exists(
            light_control_config, "light_intensity_control")

        self.scene_toggle_input_select = get_logged_app_parameter_if_exists(
            light_control_config, "scene_toggle_entity")
        self.scene_group_prefix = get_logged_app_parameter_if_exists(
            light_control_config, "scene_group_prefix")

        time_based_scene_switch_config = get_logged_app_parameter_if_exists(
            light_control_config, "time_based_scene_switch")

        self.scene_switch_configuration = None
        if time_based_scene_switch_config:
            self.scene_switch_configuration = get_logged_app_parameter_if_exists(
                time_based_scene_switch_config, "scene_switch_configuration_entity")
            self.scene_switch_automation_enabled_entity = get_logged_app_parameter_if_exists(
                time_based_scene_switch_config, "automation_enabled_entity")

    def register(self, motion_triggers, state_trackers, time_triggers):
        motion_trigger_id, motion_trigger_function = self.create_motion_trigger_function()
        replace_key_in_dict(
            motion_triggers, motion_trigger_id, motion_trigger_function)
        if self.scene_switch_configuration:
            time_to_scene_selects = state.getattr(
                self.scene_switch_configuration)["options"]
            for time_switch_configuration in time_to_scene_selects:
                state_tracker_id, refresh_time_trigger_function = create_refresh_time_trigger_function(time_switch_configuration,
                                                                                                       self.light_group_entity,
                                                                                                       self.scene_toggle_input_select,
                                                                                                       time_to_scene_selects,
                                                                                                       self.scene_group_prefix,
                                                                                                       self.scene_switch_automation_enabled_entity)
                replace_key_in_dict(state_trackers, state_tracker_id,
                                    refresh_time_trigger_function)

                time_trigger_id, time_trigger_execution = create_time_trigger_execution_function(time_switch_configuration,
                                                                                                 self.light_group_entity,
                                                                                                 self.scene_toggle_input_select,
                                                                                                 self.scene_group_prefix,
                                                                                                 self.scene_switch_automation_enabled_entity)
                replace_key_in_dict(time_triggers, time_trigger_id,
                                    time_trigger_execution)

    def create_motion_trigger_function(self):
        if not self.scene_switch_configuration:
            return create_motion_triggered_light_control(self.light_group_entity,
                                                         self.motion_sensor_entity,
                                                         self.motion_triggered_light_enabled_entity,
                                                         self.turn_off_timer_entity,
                                                         self.turn_off_timeout_entity)

        return create_motion_triggered_scene_based_light_control(self.light_group_entity,
                                                                 self.motion_sensor_entity,
                                                                 self.motion_triggered_light_enabled_entity,
                                                                 self.turn_off_timer_entity,
                                                                 self.turn_off_timeout_entity,
                                                                 self.light_intensity_control,
                                                                 self.scene_toggle_input_select,
                                                                 self.scene_group_prefix)


@time_trigger
def setup_time_based_scene_switches():
    global state_trackers
    global time_triggers
    global motion_triggers

    log.info("Setting up light control")

    for light_control_config_name in pyscript.app_config.keys():
        light_control_config = pyscript.app_config[light_control_config_name]

        log.info("Setting up: " + light_control_config_name)
        light_control_config = LightControlConfig(
            light_control_config_name, light_control_config)
        light_control_config.register(
            motion_triggers, state_trackers, time_triggers)
