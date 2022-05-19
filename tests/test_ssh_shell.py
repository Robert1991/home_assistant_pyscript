from ..modules.testtools.function_decorators import pyscript_compile
from ..modules.testtools.context_tools import load_file_to_global_context_without_imports
from unittest.mock import patch
import pytest
import subprocess
from unittest.mock import MagicMock
from unittest.mock import call
from unittest.mock import patch, mock_open


@pytest.fixture(autouse=True)
def run_remote_shell_command_test():
    load_file_to_global_context_without_imports(
        "../modules/tools/ssh_shell.py", globals())


def test_run_remote_shell_command():
    with patch('subprocess.run'):
        run_remote_shell_command("echo 'Hello World!'",
                                 "foo@some_remote", ".ssh/id_rsa")
        assert_subprocess_called_with('ssh', '-i', '.ssh/id_rsa', 'foo@some_remote',
                                      'echo', "'Hello", "World!'")


def assert_subprocess_called_with(*args):
    subprocess.run.assert_called_with(
        list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def test_run_sudo_shell_command():
    with patch('subprocess.run'):
        run_remote_shell_command("echo 'Hello World!'",
                                 "foo@some_remote", ".ssh/id_rsa", "sudo_password")
        assert_subprocess_called_with('ssh', '-i', '.ssh/id_rsa', 'foo@some_remote',
                                      'echo', "sudo_password", "|", 'echo', "'Hello", "World!'")


def test_run_remote_apt_command():
    with patch('subprocess.run') as subprocess_mock:
        command_result = MagicMock()
        command_result.returncode = 0
        command_result.stdout = "stdout"
        subprocess_mock.return_value = command_result
        with patch("builtins.open", mock_open(read_data="data")) as mock_file:
            std_out, std_err = run_remote_apt_command("update",
                                                      "foo@some_remote", ".ssh/id_rsa", "sudo_password")
            assert std_out == "stdout"
            assert std_err == None
            assert_subprocess_called_with(
                'ssh', '-i', '.ssh/id_rsa', 'foo@some_remote',
                'echo', "sudo_password", "|", 'sudo', "-S", "apt-get", "-y", "update")

            mock_file.assert_called_once_with(
                'tmp/home_server_update_log.log', 'ab')
            mock_file.return_value.__enter__().write.assert_called_once_with('stdout')


def test_run_remote_apt_command_when_error_occuors():
    with patch('subprocess.run') as subprocess_mock:
        command_result = MagicMock()
        command_result.returncode = 1
        command_result.stdout = "stdout"
        command_result.stderr = "error!"
        subprocess_mock.return_value = command_result
        with patch("builtins.open", mock_open(read_data="data")) as mock_file:
            std_out, std_err = run_remote_apt_command("update",
                                                      "foo@some_remote", ".ssh/id_rsa", "sudo_password")
            assert std_out == None
            assert std_err == "error!"

            assert_subprocess_called_with('ssh', '-i', '.ssh/id_rsa', 'foo@some_remote',
                                          'echo', "sudo_password", "|", 'sudo', "-S", "apt-get", "-y", "update")

            mock_file.assert_called_once_with(
                'tmp/home_server_update_log.log', 'ab')
            log_calls = [call("stdout"),
                         call("error occured during execution of apt 'update': "),
                         call("error!")]
            mock_file.return_value.__enter__().write.assert_has_calls(log_calls)
