from tools.ssh_shell import run_remote_shell_command


@service
def renew_certificates(url, email, token, path_to_certificates, path_to_lets_encrypt_volume):
    command = "docker run --rm -p 80:80 --name certbot " + \
        "-v \"" + path_to_certificates + ":/etc/letsencrypt\" " + \
        "-v \"" + path_to_lets_encrypt_volume + ":/var/lib/letsencrypt\" " + \
        "-e URL=" + url + " " + \
        "-e EMAIL=" + email + " " + \
        "-e VALIDATION=http" + " " + \
        "-e DUCKDNSTOKEN=" + token + " " + \
        "certbot/certbot certonly --standalone -d " + \
        url + " --preferred-challenges http-01 -v --force-renewal"

    command_result = task.executor(
        run_remote_shell_command,
        command,
        pyscript.config["global"]["host_server"]["ssh_login"],
        pyscript.config["global"]["host_server"]["ssh_key"])
    if command_result.returncode != 0:
        log.error("Running certificate renewal for " + url +
                  " failed:\\n" + str(command_result.stderr))
        notify.persistent_notification(title="Certificate Renewal Failed", message="Certificate renewal for " +
                                       url + " failed. Check logs for more information.")
    else:
        log.info("Running certificate renewal for " + url +
                 " was successful:\\n" + str(command_result.stdout))
        notify.persistent_notification(title="Certificate Renewal Successful", message="Certificate renewal for " +
                                       url + " was successful.")
