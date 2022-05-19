from ..modules.testtools.context_tools import load_file_to_global_context_without_imports
from ..modules.testtools.function_decorators import service
import pytest
from unittest.mock import MagicMock
from unittest.mock import call


def pytest_namespace():
    return {'current_call': 0}


@pytest.fixture(autouse=True)
def light_blink_setup():
    pytest.current_call = 0
    load_file_to_global_context_without_imports(
        "../scripts/lights/light_blink.py", globals(),
        ["state", "task", "light", "log"])


def test_light_blink_when_light_should_blink_twice_and_is_turned_on_before():
    def get_state_mocked(entity):
        try:
            if entity == "light.some_light":
                return "on"
            if entity == "input_boolean.state_entity":
                if pytest.current_call < 3:
                    return "on"
                return "off"
        finally:
            pytest.current_call = pytest.current_call + 1
    state.get.side_effect = get_state_mocked

    light_blink("light.some_light", "input_boolean.state_entity")

    called_light = call(entity_id='light.some_light')
    light.turn_on.assert_has_calls([called_light, called_light, called_light])
    light.turn_off.assert_has_calls([called_light, called_light])
    task.sleep.assert_has_calls([call(1), call(1)])
    log.info.assert_called_once_with(
        "finished blinking, returning to former state: on")


def test_light_blink_when_light_should_blink_trice_and_is_turned_off_before():
    def get_state_mocked(entity):
        try:
            if entity == "light.some_light":
                return "off"
            if entity == "input_boolean.state_entity":
                if pytest.current_call < 4:
                    return "on"
                return "off"
        finally:
            pytest.current_call = pytest.current_call + 1
    state.get.side_effect = get_state_mocked

    light_blink("light.some_light", "input_boolean.state_entity")

    called_light = call(entity_id='light.some_light')
    light.turn_on.assert_has_calls([called_light, called_light, called_light])
    light.turn_off.assert_has_calls(
        [called_light, called_light, called_light, called_light])
    task.sleep.assert_has_calls([call(1), call(1), call(1)])
    log.info.assert_called_once_with(
        "finished blinking, returning to former state: off")


def test_light_blink_when_light_should_blink_trice_and_is_turned_on_before_with_target_state_off_and_other_timeout():
    def get_state_mocked(entity):
        try:
            if entity == "light.some_light":
                return "on"
            if entity == "input_boolean.state_entity":
                if pytest.current_call < 4:
                    return "off"
                return "on"
        finally:
            pytest.current_call = pytest.current_call + 1
    state.get.side_effect = get_state_mocked

    light_blink("light.some_light", "input_boolean.state_entity",
                target_state="off", blink_timeout=10)

    called_light = call(entity_id='light.some_light')
    light.turn_on.assert_has_calls(
        [called_light, called_light, called_light, called_light])
    light.turn_off.assert_has_calls(
        [called_light, called_light, called_light])
    task.sleep.assert_has_calls([call(10), call(10), call(10)])
    log.info.assert_called_once_with(
        "finished blinking, returning to former state: on")
