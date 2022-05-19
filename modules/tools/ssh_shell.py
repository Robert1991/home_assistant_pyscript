import subprocess


@pyscript_compile
def run_remote_shell_command(command, ssh_login, ssh_key_path, sudo_password=None):
    command_array = command.split(" ")
    if sudo_password:
        command_array = ['ssh', '-i', ssh_key_path, ssh_login,
                         'echo', sudo_password, "|"] + command_array
    else:
        command_array = ['ssh', '-i', ssh_key_path,
                         ssh_login] + command_array
    return subprocess.run(command_array, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


@pyscript_compile
def run_remote_apt_command(command_name, login, ssh_key_path, password, log_file_path="tmp/home_server_update_log.log"):
    apt_command = "sudo -S apt-get -y " + command_name

    with open(log_file_path, "ab") as log_file:
        command_result = run_remote_shell_command(
            apt_command, login, ssh_key_path, password)
        log_file.write(command_result.stdout)
        if command_result.returncode != 0:
            log_file.write(
                "error occured during execution of apt '" + command_name + "': ")
            log_file.write(command_result.stderr)
            return None, command_result.stderr
    return command_result.stdout, None
