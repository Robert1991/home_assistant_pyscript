from tools.ssh_shell import run_remote_apt_command
import re


@service
def update_host_machine(apt_log_file_path):
    log.info("Running host server update")
    if run_update_command("update", apt_log_file_path):
        upgrade_result = run_upgrade_command("upgrade", apt_log_file_path)
        dist_upgrade_result = run_upgrade_command(
            "dist-upgrade", apt_log_file_path)

        if upgrade_result and dist_upgrade_result:
            upgrade_result.add(dist_upgrade_result)
            notify.persistent_notification(
                title="Host Server Update successful", message=upgrade_result.report_update())
            log.info("Host server update successfully completed")
            return
    log.error("Host server update resulted in error")
    notify.persistent_notification(
        title="Host Server Update failed", message="Errors occured during apt update on host server.")


def run_upgrade_command(command, log_file_path):
    command_result = run_update_command(command, log_file_path)
    if not command_result:
        return None
    update_statistics = UpdateResult.parse_update_result(command_result)
    if not update_statistics:
        log.error(
            "Upgrade statistics could not be calculated. Check logs for pattern changes")
    return update_statistics


def run_update_command(command, log_file_path):
    std_out, std_err = task.executor(run_remote_apt_command, command,
                                     pyscript.config["global"]["host_server"]["ssh_login"],
                                     pyscript.config["global"]["host_server"]["ssh_key"],
                                     pyscript.config["global"]["host_server"]["ssh_sudo"],
                                     log_file_path)
    if std_err:
        log.error("error during excution of apt command '" +
                  command + "': " + str(std_err))
        return None
    return std_out


class UpdateResult:
    def parse_update_result(update_result):
        update_groups = re.split("([0-9]+) upgraded, ([0-9]+) newly installed, ([0-9]+) to remove and ([0-9]+) not upgraded.",
                                 str(update_result).splitlines()[-1])
        if len(update_groups) == 6:
            return UpdateResult(update_groups[1], update_groups[2], update_groups[3], update_groups[4])
        return None

    def __init__(self, upgraded_packages, newly_installed_packages, packages_to_remove, packages_not_upgraded):
        self.upgraded_packages = int(upgraded_packages)
        self.newly_installed_packages = int(newly_installed_packages)
        self.packages_to_remove = int(packages_to_remove)
        self.packages_not_upgraded = int(packages_not_upgraded)

    def add(self, updateResult):
        self.upgraded_packages = self.upgraded_packages + updateResult.upgraded_packages
        self.newly_installed_packages = self.newly_installed_packages + \
            updateResult.newly_installed_packages
        self.packages_to_remove = self.packages_to_remove + updateResult.packages_to_remove
        self.packages_not_upgraded = self.packages_not_upgraded + \
            updateResult.packages_not_upgraded

    def report_update(self):
        return "packages updated: " + str(self.upgraded_packages) + "\n" + \
               "packages newly installed: " + str(self.newly_installed_packages) + "\n" + \
               "packages to remove: " + str(self.packages_to_remove) + "\n" + \
               "packages not upgraded: " + \
            str(self.packages_not_upgraded) + "\n"
