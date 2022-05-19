from tools.ssh_shell import run_remote_shell_command


@service
def run_home_assistant_docker_pull_container_command(container=""):
    docker_compose_path = pyscript.config["global"]["host_server"]["home_assistant_docker_compose"]

    log.info("Pulling container: " + container)
    command_result = execute_docker_compose_command(
        "pull " + container, docker_compose_path)
    if command_result.returncode == 0:
        log.info("Stopping container: " + container)
        command_result = execute_docker_compose_command(
            "stop " + container, docker_compose_path)
        if command_result.returncode == 0:
            log.info("Removing old container: " + container)
            command_result = execute_docker_compose_command(
                "rm " + container, docker_compose_path)
            if command_result.returncode == 0:
                log.info("Starting freshly pulled container: " + container)
                command_result = execute_docker_compose_command(
                    "up -d " + container, docker_compose_path)
                notify.persistent_notification(title="Executing Docker Pull Command",
                                               message="Executing docker pull command for " + container + " was successful.")
                log.info("Executing docker pull command for " +
                         container + " was successful.")
                return
    log.error("Pulling new container for: " + container +
              " failed:\\n" + str(command_result.stderr))
    notify.persistent_notification(title="Executing Docker Pull Command Failed", message="Pulling fresh container for " +
                                   container + " failed. Check logs for more information.")


@service
def run_home_assistant_docker_compose_command(command=""):
    docker_compose_path = pyscript.config["global"]["host_server"]["home_assistant_docker_compose"]
    pyscript.run_docker_compose_command(
        command=command, docker_compose_path=docker_compose_path)


@service
def run_server_monitoring_docker_compose_command(command=""):
    docker_compose_path = pyscript.config["global"]["host_server"]["server_monitoring_docker_compose"]
    pyscript.run_docker_compose_command(
        command=command, docker_compose_path=docker_compose_path)


@service
def run_docker_compose_command(command="", docker_compose_path=""):
    docker_compose_command = "docker-compose -f " + \
        docker_compose_path + " " + command
    log.info("Running docker compose command: " + docker_compose_command)
    command_result = execute_docker_compose_command(
        command, docker_compose_path)
    if command_result.returncode != 0:
        log.error("Docker compose command: " +
                  docker_compose_command + " failed:\\n" + str(command_result.stderr))
        notify.persistent_notification(title="Executing Docker Compose Command Failed", message="Executing " +
                                       docker_compose_command + " failed. Check logs for more information.")
    else:
        notify.persistent_notification(title="Executing Docker Compose Command", message="Executing " +
                                       docker_compose_command + " was successful.")
        log.info("Docker compose command " +
                 docker_compose_command + " was successful")


def execute_docker_compose_command(command, docker_compose_path):
    docker_compose_command = "docker-compose -f " + \
        docker_compose_path + " " + command
    log.info("Running docker compose command: " + docker_compose_command)
    return task.executor(
        run_remote_shell_command,
        docker_compose_command,
        pyscript.config["global"]["host_server"]["ssh_login"],
        pyscript.config["global"]["host_server"]["ssh_key"])
