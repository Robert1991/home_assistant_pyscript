from ..modules.testtools.function_decorators import pyscript_compile
from ..modules.testtools.function_decorators import service
from ..modules.testtools.context_tools import load_file_to_global_context_without_imports
from unittest.mock import MagicMock
from unittest.mock import call
import pytest
import re


def pytest_namespace():
    return {'current_call': 0}


@pytest.fixture(autouse=True)
def host_server_update_setup():
    pytest.current_call = 0
    load_file_to_global_context_without_imports(
        "../scripts/server_maintenance/host_server_update.py", globals(),
        ["log", "task", "notify", "pyscript", "run_remote_apt_command"])
    pyscript.config = {
        "global": {
            "host_server": {
                "ssh_login": "foo@server",
                "ssh_key": ".ssh/id_rsa",
                "ssh_sudo": "sudo!"
            }}}


def test_update_host_machine_apt_command_invocation():
    task.executor = MagicMock(return_value=[
        "1 upgraded, 2 newly installed, 3 to remove and 4 not upgraded.", None])

    update_host_machine("/log/file/path")

    executor_calls = [call(run_remote_apt_command,  'update',
                           'foo@server', '.ssh/id_rsa', 'sudo!', "/log/file/path"),
                      call(run_remote_apt_command,  'upgrade',
                           'foo@server', '.ssh/id_rsa', 'sudo!', "/log/file/path"),
                      call(run_remote_apt_command, 'dist-upgrade',
                           'foo@server', '.ssh/id_rsa', 'sudo!', "/log/file/path")]
    task.executor.assert_has_calls(executor_calls)

    log_calls = [call("Running host server update"),
                 call("Host server update successfully completed")]
    log.info.assert_has_calls(log_calls)
    notify.persistent_notification.assert_called_once_with(
        title='Host Server Update successful',
        message='packages updated: 2\npackages newly installed: 4\npackages to remove: 6\npackages not upgraded: 8\n')


def test_update_host_machine_apt_command_invocation_with_error_upgrade_and_dist_upgrade():
    def side_effect_function(*args):
        try:
            if pytest.current_call == 0:
                return ["this is the update", None]
            else:
                return [None, "error"]
        finally:
            pytest.current_call = pytest.current_call + 1

    task.executor = MagicMock(side_effect=side_effect_function)

    update_host_machine("/log/file/path")

    executor_calls = [call(run_remote_apt_command,  'update',
                           'foo@server', '.ssh/id_rsa', 'sudo!', "/log/file/path"),
                      call(run_remote_apt_command,  'upgrade',
                           'foo@server', '.ssh/id_rsa', 'sudo!', "/log/file/path")]
    task.executor.assert_has_calls(executor_calls)
    log.info.assert_called_once_with("Running host server update")

    error_log = [
        call("error during excution of apt command 'upgrade': error"),
        call("error during excution of apt command 'dist-upgrade': error"),
        call('Host server update resulted in error')]
    log.error.assert_has_calls(error_log)
    notify.persistent_notification.assert_called_once_with(
        title="Host Server Update failed", message="Errors occured during apt update on host server.")


def test_update_host_machine_apt_command_invocation_with_error_update():
    task.executor = MagicMock(return_value=[None, "error"])

    update_host_machine("/log/file/path")

    task.executor.assert_called_once_with(run_remote_apt_command,  'update',
                                          'foo@server', '.ssh/id_rsa', 'sudo!', "/log/file/path")
    log.info.assert_called_once_with("Running host server update")

    error_log = [
        call("error during excution of apt command 'update': error"),
        call("Host server update resulted in error")]
    log.error.assert_has_calls(error_log)
    notify.persistent_notification.assert_called_once_with(
        title="Host Server Update failed", message="Errors occured during apt update on host server.")


def test_update_host_machine_apt_command_invocation_with_error_dist_upgrade():
    def side_effect_function(*args):
        try:
            if pytest.current_call == 0:
                return ["this is the update", None]
            elif pytest.current_call == 1:
                return ["1 upgraded, 2 newly installed, 3 to remove and 4 not upgraded.", None]
            return [None, "error"]
        finally:
            pytest.current_call = pytest.current_call + 1
    task.executor = MagicMock(side_effect=side_effect_function)

    update_host_machine("/log/file/path")

    executor_calls = [call(run_remote_apt_command,  'update',
                           'foo@server', '.ssh/id_rsa', 'sudo!', "/log/file/path"),
                      call(run_remote_apt_command,  'upgrade',
                           'foo@server', '.ssh/id_rsa', 'sudo!', "/log/file/path"),
                      call(run_remote_apt_command,  'dist-upgrade',
                           'foo@server', '.ssh/id_rsa', 'sudo!', "/log/file/path")]
    task.executor.assert_has_calls(executor_calls)
    log.info.assert_called_once_with("Running host server update")

    error_log = [
        call("error during excution of apt command 'dist-upgrade': error"),
        call("Host server update resulted in error")]
    log.error.assert_has_calls(error_log)
    notify.persistent_notification.assert_called_once_with(
        title="Host Server Update failed", message="Errors occured during apt update on host server.")


def test_update_host_machine_when_parsing_error_occurs_on_update():
    def side_effect_function(*args):
        try:
            if pytest.current_call == 0:
                return ["this is the update", None]
            elif pytest.current_call == 1:
                return ["1 upgraded, 2 newly instaled, 3 to rffemove and 4 not upgraded.", None]
            return ["1 upgraded, 2 newly installed, 3 to remove and 4 not upgraded.", None]
        finally:
            pytest.current_call = pytest.current_call + 1
    task.executor = MagicMock(side_effect=side_effect_function)

    update_host_machine("/log/file/path")

    executor_calls = [call(run_remote_apt_command,  'update',
                           'foo@server', '.ssh/id_rsa', 'sudo!', "/log/file/path"),
                      call(run_remote_apt_command,  'upgrade',
                           'foo@server', '.ssh/id_rsa', 'sudo!', "/log/file/path"),
                      call(run_remote_apt_command,  'dist-upgrade',
                           'foo@server', '.ssh/id_rsa', 'sudo!', "/log/file/path")]
    task.executor.assert_has_calls(executor_calls)
    log.info.assert_called_once_with("Running host server update")

    error_log = [
        call("Upgrade statistics could not be calculated. Check logs for pattern changes"),
        call("Host server update resulted in error")]
    log.error.assert_has_calls(error_log)
    notify.persistent_notification.assert_called_once_with(
        title="Host Server Update failed", message="Errors occured during apt update on host server.")


def test_update_host_machine_when_parsing_error_occurs_on_upgrade():
    def side_effect_function(*args):
        try:
            if pytest.current_call == 0:
                return ["this is the update", None]
            elif pytest.current_call == 1:
                return ["1 upgraded, 2 newly installed, 3 to remove and 4 not upgraded.", None]
            return ["1 upgraded, 2 newly instaled, 3 to rffemove and 4 not upgraded.", None]
        finally:
            pytest.current_call = pytest.current_call + 1
    task.executor = MagicMock(side_effect=side_effect_function)

    update_host_machine("/log/file/path")

    executor_calls = [call(run_remote_apt_command,  'update',
                           'foo@server', '.ssh/id_rsa', 'sudo!', "/log/file/path"),
                      call(run_remote_apt_command,  'upgrade',
                           'foo@server', '.ssh/id_rsa', 'sudo!', "/log/file/path"),
                      call(run_remote_apt_command,  'dist-upgrade',
                           'foo@server', '.ssh/id_rsa', 'sudo!', "/log/file/path")]
    task.executor.assert_has_calls(executor_calls)
    log.info.assert_called_once_with("Running host server update")

    error_log = [
        call("Upgrade statistics could not be calculated. Check logs for pattern changes"),
        call("Host server update resulted in error")]
    log.error.assert_has_calls(error_log)
    notify.persistent_notification.assert_called_once_with(
        title="Host Server Update failed", message="Errors occured during apt update on host server.")
