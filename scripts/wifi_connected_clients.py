from yaml import dump
from tools.ssh_shell import run_remote_shell_command


@pyscript_compile
def write_connected_clients(file_path, connected_clients):
    with open(file_path, "w") as connected_clients_file:
        connected_clients_file.write(dump(connected_clients))


@service
def export_connected_clients(file_path):
    command_result = task.executor(
        run_remote_shell_command,
        "/etc/show_wifi_clients.sh",
        "root@RPNRouter",
        pyscript.config["global"]["host_server"]["ssh_key"])
    if not command_result.returncode:
        wifi_connected_clients = {"connected": []}
        for line in command_result.stdout.decode().split("\n"):
            if not line.startswith("#"):
                line_parts = line.split("\t")
                if len(line_parts) == 3:
                    wifi_connected_clients["connected"].append(
                        {"ip": line_parts[0], "hostname": line_parts[1], "mac_address": line_parts[2]})
        write_connected_clients(file_path, wifi_connected_clients)
    else:
        log.error("Unable to list available client")
