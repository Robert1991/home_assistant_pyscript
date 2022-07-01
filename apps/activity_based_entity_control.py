from tools.state import is_off, is_entity_in_state
from datetime import datetime
from tools.dict import get_logged_app_parameter_if_exists
from tools.dict import replace_key_in_dict

state_trackers = {}
time_triggers = {}
motion_triggers = {}


def call_service_within_entity_domain(entity, service_name, **service_args):
    entity_domain = entity.split(".")[0]
    service.call(entity_domain, service_name, **service_args)


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


def create_motion_entity_control(entity, motion_sensor_entity, automation_enabled_entity, turn_off_timeout_entity, timer_entity,
                                 turn_on_function, turn_off_function, turn_on_condition=None):
    motion_entity_control_id = "motion_entity_control_" + entity

    @task_unique(motion_entity_control_id + "_motion_trigger")
    @state_trigger(motion_sensor_entity + " == 'on'")
    def on_motion_detected():
        if automation_enabled_entity:
            if is_off(automation_enabled_entity):
                log.info("skipping automation on " + entity + " as " +
                         automation_enabled_entity + " set to off")
                return
        if not is_off(entity):
            if is_entity_in_state(timer_entity, "active"):
                log.info("stopping timer " + timer_entity +
                         " because movement was detected by " + motion_sensor_entity)
                timer.cancel(entity_id=timer_entity)
            return
        if turn_on_condition is not None and not turn_on_condition():
            log.info("skip turning on " + entity +
                     " as turn on condition was not met")
            return
        if turn_on_function is not None:
            turn_on_function()

    @task_unique(motion_entity_control_id + "_motion_trigger")
    @state_trigger(motion_sensor_entity + " == 'off'")
    def on_motion_cleared():
        if not is_off(entity):
            turn_off_timeout = get_seconds_from_input_number(
                turn_off_timeout_entity)
            log.info("starting turn off timer with turn off timeout { "
                     + turn_off_timeout_entity + ": " + str(turn_off_timeout) +
                     "s } because no movement was detected by " + motion_sensor_entity)
            timer.start(entity_id=timer_entity,
                        duration=turn_off_timeout)

    @task_unique(motion_entity_control_id + "_entity_manual_off_trigger")
    @state_trigger(entity + " == 'off'")
    def kill_timer_after_entity_was_turned_off_manually():
        if is_entity_in_state(timer_entity, "active"):
            log.info("stopping " + timer_entity + " as entity " +
                     entity + " was turned off manually.")
            timer.cancel(entity_id=timer_entity)

    @task_unique(motion_entity_control_id + "_timer_trigger")
    @event_trigger("timer.finished", "entity_id == '" + timer_entity + "'")
    def turn_off_entity_after_timer_finish(**kwargs):
        log.info(f"got timer.finished from " + timer_entity +
                 ". executing turn off: " + entity)
        if turn_off_function is not None:
            turn_off_function()

    return motion_entity_control_id, {on_motion_detected, on_motion_cleared, kill_timer_after_entity_was_turned_off_manually, turn_off_entity_after_timer_finish}


def get_scene_toggle_time(time_switch_configuration):
    input_datetime_entity, _ = time_switch_configuration.split("/")
    return "input_datetime." + input_datetime_entity


def get_scene_input_select(time_switch_configuration):
    _, input_select_entity = time_switch_configuration.split("/")
    return "input_select." + input_select_entity


def normalize_scene_name(scene_group_prefix, scene_name):
    return "scene." + scene_group_prefix + "_" + scene_name.lower().replace(" ", "_")


def toggle_scene(scene_toggle_input_select, current_scene, controlled_entity,
                 scene_group_prefix):
    log.info("toggling " + scene_toggle_input_select +
             " to " + current_scene)
    input_select.select_option(
        entity_id=scene_toggle_input_select, option=current_scene)
    if not is_off(controlled_entity):
        current_scene_entity_id = normalize_scene_name(
            scene_group_prefix, current_scene)
        log.info("turning on scene " + current_scene_entity_id)
        scene.turn_on(entity_id=current_scene_entity_id)


def determine_closest_beginning_scene(time_to_scene_selects):
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


def determine_latest_beginning_scene(time_to_scene_selects):
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


def create_time_trigger_execution_function(time_switch_configuration, controlled_entity, scene_toggle_input_select,
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
        current_scene = state.get(input_select_entity)
        toggle_scene(scene_toggle_input_select,
                     current_scene,
                     controlled_entity,
                     scene_group_prefix)
    return time_trigger_id, execute_on_time_trigger


def create_refresh_time_trigger_function(time_switch_configuration, controlled_entity, scene_toggle_input_select,
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
                                                                                         controlled_entity,
                                                                                         scene_toggle_input_select,
                                                                                         scene_group_prefix,
                                                                                         automation_enabled_entity)
        replace_key_in_dict(time_triggers, time_trigger_id,
                            time_trigger_execution)
        if is_off(automation_enabled_entity):
            log.info("Skip setting as automation is disabled for " +
                     input_datetime_entity)
            return
        current_scene = determine_closest_beginning_scene(
            time_to_scene_selects)
        if not current_scene:
            current_scene = determine_latest_beginning_scene(
                time_to_scene_selects)
        toggle_scene(scene_toggle_input_select,
                     current_scene,
                     controlled_entity,
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


class ActivityBasedEntityControlConfig:
    def __init__(self, config_name, entity_control_config):
        self.config_name = config_name
        self.controlled_entity = get_logged_app_parameter_if_exists(
            entity_control_config, "entity")
        self.motion_sensor_entity = get_logged_app_parameter_if_exists(
            entity_control_config, "motion_sensor_entity")
        self.activity_based_entity_control_enabled_entity = get_logged_app_parameter_if_exists(
            entity_control_config, "automation_enabled_entity")
        self.turn_off_timeout_entity = get_logged_app_parameter_if_exists(
            entity_control_config, "turn_off_timeout_entity")
        self.turn_off_timer_entity = get_logged_app_parameter_if_exists(
            entity_control_config, "turn_off_timer_entity")

        skip_turn_on = get_logged_app_parameter_if_exists(
            entity_control_config, "skip_turn_on")
        if not skip_turn_on:
            self.skip_turn_on = False
        else:
            self.skip_turn_on = True

        self.light_intensity_control = get_logged_app_parameter_if_exists(
            entity_control_config, "light_intensity_control")

        self.scene_toggle_input_select = get_logged_app_parameter_if_exists(
            entity_control_config, "scene_toggle_entity")
        self.scene_group_prefix = get_logged_app_parameter_if_exists(
            entity_control_config, "scene_group_prefix")

        time_based_scene_switch_config = get_logged_app_parameter_if_exists(
            entity_control_config, "time_based_scene_switch")

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
                                                                                                       self.controlled_entity,
                                                                                                       self.scene_toggle_input_select,
                                                                                                       time_to_scene_selects,
                                                                                                       self.scene_group_prefix,
                                                                                                       self.scene_switch_automation_enabled_entity)
                replace_key_in_dict(state_trackers, state_tracker_id,
                                    refresh_time_trigger_function)

                time_trigger_id, time_trigger_execution = create_time_trigger_execution_function(time_switch_configuration,
                                                                                                 self.controlled_entity,
                                                                                                 self.scene_toggle_input_select,
                                                                                                 self.scene_group_prefix,
                                                                                                 self.scene_switch_automation_enabled_entity)
                replace_key_in_dict(time_triggers, time_trigger_id,
                                    time_trigger_execution)

    def create_motion_trigger_function(self):
        if not self.scene_switch_configuration:
            return self.create_activity_based_entity_control()

        return self.create_activity_based_scene_based_entity_control()

    def create_activity_based_entity_control(self):
        def turn_on_entity():
            log.info(self.config_name + ": turning on " + self.controlled_entity +
                     " because movement was detected by " + self.motion_sensor_entity)
            call_service_within_entity_domain(
                self.controlled_entity, "turn_on", entity_id=self.controlled_entity)

        def turn_off_entity():
            call_service_within_entity_domain(
                self.controlled_entity, "turn_off", entity_id=self.controlled_entity)

        turn_on_entity_function = None
        if not self.skip_turn_on:
            turn_on_entity_function = turn_on_entity

        return create_motion_entity_control(self.controlled_entity,
                                            self.motion_sensor_entity,
                                            self.activity_based_entity_control_enabled_entity,
                                            self.turn_off_timeout_entity,
                                            self.turn_off_timer_entity,
                                            turn_on_entity_function,
                                            turn_off_entity)

    def create_activity_based_scene_based_entity_control(self):
        def turn_on_entity_scene_based():
            current_scene = state.get(self.scene_toggle_input_select)
            current_scene_entity_id = normalize_scene_name(
                self.scene_group_prefix, current_scene)
            log.info(self.config_name + ": turning on scene " + current_scene_entity_id +
                     " because movement was detected by " + self.motion_sensor_entity)
            scene.turn_on(entity_id=current_scene_entity_id)

        def light_intensity_turn_on_condition():
            if self.light_intensity_control is not None and is_light_intensity_sufficient(self.light_intensity_control):
                log.info(self.config_name + ": skip turning on " + self.controlled_entity +
                         " as light was determined to be sufficient")
                return False
            return True

        def turn_off_function():
            call_service_within_entity_domain(
                self.controlled_entity, "turn_off", entity_id=self.controlled_entity)

        log.info("light_control   " + str(self.light_intensity_control))

        return create_motion_entity_control(self.controlled_entity,
                                            self.motion_sensor_entity,
                                            self.activity_based_entity_control_enabled_entity,
                                            self.turn_off_timeout_entity,
                                            self.turn_off_timer_entity,
                                            turn_on_entity_scene_based,
                                            turn_off_function,
                                            light_intensity_turn_on_condition)


def register_entity_control_config(entity_control_config):
    global state_trackers
    global time_triggers
    global motion_triggers

    entity_control_config_name = list(entity_control_config.keys())[0]
    log.info("Setting up: " + entity_control_config_name)
    entity_control_config = ActivityBasedEntityControlConfig(
        entity_control_config_name, entity_control_config[entity_control_config_name])
    entity_control_config.register(
        motion_triggers, state_trackers, time_triggers)


@time_trigger
def setup_activity_based_entity_control():
    log.info("Setting up activity based entity control")
    for app_config_part in pyscript.app_config:
        if isinstance(app_config_part, list):
            for entity_control_config in app_config_part:
                register_entity_control_config(entity_control_config)
        else:
            register_entity_control_config(app_config_part)
