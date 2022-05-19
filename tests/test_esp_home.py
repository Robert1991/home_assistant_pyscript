from ..modules.testtools.function_decorators import service
from ..modules.testtools.context_tools import load_file_to_global_context_without_imports
import pytest
from unittest.mock import MagicMock
from unittest.mock import call


@pytest.fixture(autouse=True)
def host_server_update_setup():
    load_file_to_global_context_without_imports(
        "../scripts/server_maintenance/esp_home.py", globals(),
        ["log", "task", "notify", "pyscript", "state", "run_remote_shell_command"])
    pyscript.config = {
        "global": {
            "esp_home_automations": {
                "esp_home_base_path": "/path/on/host/to/esphome"
            },
            "host_server": {
                "ssh_login": "foo@server",
                "ssh_key": ".ssh/id_rsa",
            }}}


def test_update_all_esp_home_devices():
    state.getattr.return_value = {"options": [
        "test_device_1", "test_device_2"]}

    update_all_esp_home_devices()

    state.getattr.assert_called_once_with("input_select.esp_home_devices")
    pyscript.run_esp_home_device_update.assert_has_calls(
        [call(esp_home_device_config="test_device_1.yaml"),
         call(esp_home_device_config="test_device_2.yaml")])
    log.info.assert_has_calls(
        [call("Invoking esp home update for: test_device_1.yaml"),
         call("Invoking esp home update for: test_device_2.yaml")])


def test_run_esp_home_device_update():
    command_result = MagicMock()
    command_result.returncode = 0
    task.executor.return_value = command_result

    run_esp_home_device_update("test_device.yaml")

    expected_command_line = create_expected_command_line("test_device.yaml")
    task.executor.assert_called_once_with(
        run_remote_shell_command,
        expected_command_line,
        "foo@server",
        ".ssh/id_rsa")
    log_calls = [
        call("Running esp-home update for: 'test_device.yaml' with command line: " +
             expected_command_line),
        call("esp home device update for test_device.yaml was successful")]
    log.info.assert_has_calls(log_calls)


def test_run_esp_home_device_update_with_failure():
    command_result = MagicMock()
    command_result.returncode = 1
    command_result.stderr = "error!"
    task.executor.return_value = command_result

    run_esp_home_device_update("test_device.yaml")

    expected_command_line = create_expected_command_line("test_device.yaml")
    task.executor.assert_called_once_with(
        run_remote_shell_command,
        expected_command_line,
        "foo@server",
        ".ssh/id_rsa")
    log.info.assert_called_once_with(
        "Running esp-home update for: 'test_device.yaml' with command line: " + expected_command_line)
    log.error.assert_called_once_with(
        "Running esp home update for test_device.yaml failed:\\nerror!")
    notify.persistent_notification.assert_called_once_with(
        title="ESP Home Device Update Failed", message="Device update for test_device.yaml failed. Check logs for more information.")


def create_expected_command_line(device_name):
    return "docker run --rm -v /path/on/host/to/esphome:/config esphome/esphome " + device_name + " run --no-logs"
