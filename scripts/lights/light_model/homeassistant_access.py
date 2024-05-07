import subprocess


def reload_homeassistant_config():
    subprocess.run(
        ["hass-cli", "service", "call", "homeassistant.reload_all"], check=True
    )
