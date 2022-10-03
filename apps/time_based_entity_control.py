from tools.dict import get_logged_app_parameter_if_exists
from tools.dict import replace_key_in_dict
from tools.entity import call_service_within_entity_domain
from tools.state import is_off, is_entity_in_state, get_state_as_date_time
import datetime

time_triggers = {}
state_triggers = {}


def time_in_range(start, end, x):
    if start <= end:
        return start <= x <= end
    else:
        return start <= x or x <= end


def get_time_of_day(datetime_object):
    return datetime.time(datetime_object.hour, datetime_object.minute, 0)


def toggle_entity_to_state_if_necessary(entity_control_config_name, toggled_entity, target_state):
    if not is_entity_in_state(toggled_entity, target_state):
        if target_state == "on":
            log.info(entity_control_config_name +
                     ": initializing, turning on " + toggled_entity)
            call_service_within_entity_domain(
                toggled_entity, "turn_on", entity_id=toggled_entity)
            return
        log.info(entity_control_config_name +
                 ": initializing, turning off " + toggled_entity)
        call_service_within_entity_domain(
            toggled_entity, "turn_off", entity_id=toggled_entity)
        return
    log.info(entity_control_config_name + " no initialization needed")


def initialize_entity_state(entity_control_config_name, interval_start_datetime, interval_end_datetime, toggled_entity, target_state):
    interval_start_time = get_time_of_day(
        get_state_as_date_time(interval_start_datetime))
    interval_end_time = get_time_of_day(
        get_state_as_date_time(interval_end_datetime))
    now_time = get_time_of_day(datetime.datetime.now())

    if time_in_range(interval_start_time, interval_end_time, now_time):
        toggle_entity_to_state_if_necessary(entity_control_config_name,
                                            toggled_entity, target_state)
    else:
        opposite_state = "off"
        if target_state == "off":
            opposite_state = "on"
        toggle_entity_to_state_if_necessary(entity_control_config_name,
                                            toggled_entity, opposite_state)


def create_cron_time_trigger_function(entity, datetime_entity, automation_enabled_entity, toggle_entity_function):
    entity_turn_toggle_time = get_state_as_date_time(datetime_entity)
    hour = entity_turn_toggle_time.hour
    minute = entity_turn_toggle_time.minute

    time_trigger = "cron(" + str(minute) + " " + str(hour) + " * * *)"
    time_trigger_id = datetime_entity + "_time_trigger"

    log.info("Registering " + time_trigger_id +
             " with cron " + time_trigger + " for " + entity)

    @task_unique(time_trigger_id)
    @time_trigger(time_trigger)
    def on_cron_triggered():
        if is_off(automation_enabled_entity):
            log.info("skipping automation on " + entity + " as " +
                     automation_enabled_entity + " set to off")
            return
        toggle_entity_function()
    return time_trigger_id, on_cron_triggered


def register_time_based_entity_control(configuration):
    entity_control_config_name = list(configuration.keys())[0]

    refresh_cron_time_trigger_task_id = "refresh_cron_time_trigger_" + \
        entity_control_config_name
    configuration_dict = configuration[entity_control_config_name]

    toggled_entity = get_logged_app_parameter_if_exists(
        configuration_dict, "entity")
    interval_start_datetime = get_logged_app_parameter_if_exists(
        configuration_dict, "interval_start")
    interval_end_datetime = get_logged_app_parameter_if_exists(
        configuration_dict, "interval_end")
    automation_enabled_entity = get_logged_app_parameter_if_exists(
        configuration_dict, "automation_enabled_entity")
    target_state = get_logged_app_parameter_if_exists(
        configuration_dict, "target_state")

    @task_unique(refresh_cron_time_trigger_task_id)
    @state_trigger(interval_start_datetime)
    @state_trigger(interval_end_datetime)
    @state_trigger(automation_enabled_entity)
    @time_trigger
    def refresh_cron_time_trigger(**kwargs):
        def turn_on_entity():
            log.info(entity_control_config_name +
                     ": turning on " + toggled_entity)
            call_service_within_entity_domain(
                toggled_entity, "turn_on", entity_id=toggled_entity)

        def turn_off_entity():
            call_service_within_entity_domain(
                toggled_entity, "turn_off", entity_id=toggled_entity)

        if target_state == "on":
            interval_start_function = turn_on_entity
            interval_end_function = turn_off_entity
        else:
            interval_start_function = turn_off_entity
            interval_end_function = turn_on_entity

        interval_start_trigger_function_id, interval_start_trigger_function = create_cron_time_trigger_function(
            toggled_entity, interval_start_datetime, automation_enabled_entity, interval_start_function)
        replace_key_in_dict(time_triggers, interval_start_trigger_function_id,
                            interval_start_trigger_function)
        interval_end_trigger_function_id, interval_end_trigger_function = create_cron_time_trigger_function(
            toggled_entity, interval_end_datetime, automation_enabled_entity, interval_end_function)
        replace_key_in_dict(time_triggers, interval_end_trigger_function_id,
                            interval_end_trigger_function)
        initialize_entity_state(entity_control_config_name, interval_start_datetime,
                                interval_end_datetime, toggled_entity, target_state)
    replace_key_in_dict(
        state_triggers, refresh_cron_time_trigger_task_id, refresh_cron_time_trigger)


@time_trigger
def setup_time_based_entity_control():
    log.info("Setting up time based entity control")
    for app_config_part in pyscript.app_config:
        if isinstance(app_config_part, list):
            for config in app_config_part:
                register_time_based_entity_control(config)
        else:
            register_time_based_entity_control(app_config_part)
