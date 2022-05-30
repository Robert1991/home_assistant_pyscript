from homeassistant.const import EVENT_CALL_SERVICE
from datetime import datetime
from enum import auto

state_trackers = {}
time_triggers = {}
motion_triggers = {}


def replace_key_in_dict(dict, key, replace_object):
    if key in dict.keys():
        del dict[key]
    dict[key] = replace_object


def get_scene_toggle_time(time_switch_configuration):
    input_datetime_entity, _ = time_switch_configuration.split("/")
    return "input_datetime." + input_datetime_entity


def get_scene_input_select(time_switch_configuration):
    _, input_select_entity = time_switch_configuration.split("/")
    return "input_select." + input_select_entity


def get_state_as_date_time(input_datetime_entity):
    return datetime.strptime(
        state.get(input_datetime_entity), '%H:%M:%S')


def normalize_scene_name(scene_group_prefix, scene_name):
    return "scene." + scene_group_prefix + "_" + scene_name.lower().replace(" ", "_")


def toggle_light_scene(scene_toggle_input_select, current_light_scene, light_group_entity,
                       scene_group_prefix):
    log.info("toggling " + scene_toggle_input_select +
             " to " + current_light_scene)
    input_select.select_option(
        entity_id=scene_toggle_input_select, option=current_light_scene)
    if state.get(light_group_entity) == "on":
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
        if state.get(automation_enabled_entity) == "off":
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
        if state.get(automation_enabled_entity) == "off":
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


def create_motion_triggered_light_control(light_group_entity, motion_sensor_entity, motion_triggered_light_enabled_entity, turn_off_timer_entity,
                                          turn_off_timeout_entity, light_intensity_control, current_scene_input_select, scene_group_prefix):
    motion_light_control_id = "motion_light_control_" + light_group_entity

    @task_unique(motion_light_control_id + "_motion_trigger")
    @state_trigger(motion_sensor_entity + " == 'on'")
    def on_motion_detected():
        automation_enabled = state.get(motion_triggered_light_enabled_entity)
        if automation_enabled == "off":
            log.info("skipping automation on " + light_group_entity + " as " +
                     motion_triggered_light_enabled_entity + " set to off")
            return

        if state.get(light_group_entity) == "on":
            if state.get(turn_off_timer_entity) == "active":
                log.info("stopping timer " + turn_off_timer_entity +
                         " because movement was detected by " + motion_sensor_entity)
                timer.cancel(entity_id=turn_off_timer_entity)
        else:
            if light_intensity_control and is_light_intensity_sufficient(light_intensity_control):
                log.info("skip turning on " + light_group_entity +
                         " as light was determined to be sufficient")
                return

            current_light_scene = state.get(current_scene_input_select)
            current_scene_entity_id = normalize_scene_name(
                scene_group_prefix, current_light_scene)
            log.info("turning on scene " + current_scene_entity_id +
                     " because movement was detected by " + motion_sensor_entity)
            scene.turn_on(entity_id=current_scene_entity_id)

    @task_unique(motion_light_control_id + "_motion_trigger")
    @state_trigger(motion_sensor_entity + " == 'off'")
    def on_motion_cleared():
        turn_off_timeout = state.get(turn_off_timeout_entity)
        log.info("starting turn off timer with turn off timeout { "
                 + turn_off_timeout_entity + ": " + turn_off_timeout +
                 " } because no movement was detected by " + motion_sensor_entity)
        timer.start(entity_id=turn_off_timer_entity, duration=turn_off_timeout)

    @task_unique(motion_light_control_id + "_light_manual_off_trigger")
    @state_trigger(light_group_entity + " == 'off'")
    def kill_timer_after_light_was_turned_off_manually():
        if state.get(turn_off_timer_entity) == "active":
            log.info("stopping " + turn_off_timer_entity + " as light " +
                     light_group_entity + " was turned off manually.")
            timer.cancel(entity_id=turn_off_timer_entity)

    @task_unique(motion_light_control_id + "_timer_trigger")
    @event_trigger("timer.finished", "entity_id == '" + turn_off_timer_entity + "'")
    def turn_off_light_after_timer_finish(**kwargs):
        log.info(f"got timer.finished from " + turn_off_timer_entity +
                 ". turning off: " + light_group_entity)
        light.turn_off(entity_id=light_group_entity)

    return motion_light_control_id, {on_motion_detected, on_motion_cleared, turn_off_light_after_timer_finish, kill_timer_after_light_was_turned_off_manually}


def setup_light_control(light_control_config):
    global state_trackers
    global time_triggers
    global motion_triggers

    light_group_entity = light_control_config["light_group_entity"]
    motion_sensor_entity = light_control_config["motion_sensor_entity"]
    motion_triggered_light_enabled_entity = light_control_config[
        "motion_triggered_light_enabled_entity"]
    turn_off_timeout_entity = light_control_config["turn_off_timeout_entity"]
    scene_toggle_input_select = light_control_config["scene_toggle_entity"]
    scene_group_prefix = light_control_config["scene_group_prefix"]
    turn_off_timer_entity = light_control_config["turn_off_timer_entity"]

    time_based_scene_switch_config = light_control_config["time_based_scene_switch"]
    scene_switch_configuration = time_based_scene_switch_config[
        "scene_switch_configuration_entity"]
    time_to_scene_selects = state.getattr(
        scene_switch_configuration)["options"]
    scene_switch_automation_enabled_entity = time_based_scene_switch_config[
        "automation_enabled_entity"]

    light_intensity_control = None
    if "light_intensity_control" in light_control_config:
        light_intensity_control = light_control_config["light_intensity_control"]

    log.info(" light_group_entity: " + light_group_entity)
    log.info(" motion_sensor_entity: " + motion_sensor_entity)
    log.info(" motion_triggered_light_enabled_entity: " +
             motion_triggered_light_enabled_entity)
    log.info(" turn_off_timeout_entity: " + turn_off_timeout_entity)
    log.info(" turn_off_timer_entity: " + turn_off_timer_entity)
    log.info(" scene_toggle_input_select: " + scene_toggle_input_select)
    log.info(" scene_group_prefix: " + scene_group_prefix)
    log.info(" scene_switch_configuration: " + scene_switch_configuration)
    log.info(" automation_enabled_entity: " + scene_switch_configuration)
    log.info(" light_intensity_control: " + str(light_intensity_control))

    for time_switch_configuration in time_to_scene_selects:
        motion_trigger_id, motion_trigger_function = create_motion_triggered_light_control(light_group_entity,
                                                                                           motion_sensor_entity,
                                                                                           motion_triggered_light_enabled_entity,
                                                                                           turn_off_timer_entity,
                                                                                           turn_off_timeout_entity,
                                                                                           light_intensity_control,
                                                                                           scene_toggle_input_select,
                                                                                           scene_group_prefix)
        replace_key_in_dict(motion_triggers, motion_trigger_id,
                            motion_trigger_function)
        state_tracker_id, refresh_time_trigger_function = create_refresh_time_trigger_function(time_switch_configuration,
                                                                                               light_group_entity,
                                                                                               scene_toggle_input_select,
                                                                                               time_to_scene_selects,
                                                                                               scene_group_prefix,
                                                                                               scene_switch_automation_enabled_entity)
        replace_key_in_dict(state_trackers, state_tracker_id,
                            refresh_time_trigger_function)

        time_trigger_id, time_trigger_execution = create_time_trigger_execution_function(time_switch_configuration,
                                                                                         light_group_entity,
                                                                                         scene_toggle_input_select,
                                                                                         scene_group_prefix,
                                                                                         scene_switch_automation_enabled_entity)
        replace_key_in_dict(time_triggers, time_trigger_id,
                            time_trigger_execution)


@time_trigger
def setup_time_based_scene_switches():
    log.info("Setting up light control")

    for light_control_config_name in pyscript.app_config.keys():
        light_control_config = pyscript.app_config[light_control_config_name]

        log.info("Setting up: " + light_control_config_name)
        setup_light_control(light_control_config)
