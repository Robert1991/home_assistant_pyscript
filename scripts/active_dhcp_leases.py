from yaml import dump
from tools.ssh_shell import run_remote_shell_command


@pyscript_compile
def write_connected_clients(file_path, connected_clients):
    with open(file_path, "w") as connected_clients_file:
        connected_clients_file.write(dump(connected_clients))


@service
def export_active_dhcp_leases(file_path):
    command_result = task.executor(
        run_remote_shell_command,
        "cat /tmp/dhcp.leases",
        "root@RPNRouter",
        pyscript.config["global"]["host_server"]["ssh_key"])
    if command_result.returncode == 0:
        active_dhcp_leases = {"leases": []}

        for line in command_result.stdout.decode().split("\n"):
            if len(line) > 0:
                line_parts = line.split(" ")
                if len(line_parts) == 5:
                    active_dhcp_leases["leases"].append(
                        {"ip": line_parts[2], "hostname": line_parts[3], "mac_address": line_parts[1]})
                else:
                    log.error("entry not interpretable: " + line)
            write_connected_clients(file_path, active_dhcp_leases)
    else:
        log.error("Unable to list available client")
