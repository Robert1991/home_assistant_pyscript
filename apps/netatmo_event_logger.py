import time
import datetime
import urllib.request as url_request
import os
from pathlib import Path
from shutil import copyfile

event_logger_instance = None


@pyscript_compile
def clean_up_folder(folder_path, max_number_of_items):
    files = os.listdir(folder_path)
    if len(files) <= max_number_of_items:
        return

    sorted_by_creation = sorted(
        files, key=lambda fileName: os.path.getctime(folder_path + fileName))
    deleted_item_count = len(files) - max_number_of_items
    for file_to_be_deleted in sorted_by_creation[:deleted_item_count]:
        os.remove(folder_path + file_to_be_deleted)


@pyscript_compile
def log_netatmo_event_to_file(event, event_time, event_file_path):
    with open(event_file_path, "a") as event_log:
        time_stamp = datetime.datetime.fromtimestamp(
            event_time).strftime('%Y-%m-%d %H:%M:%S')
        event_log.write(time_stamp + ": " + str(event) + "\n")


@pyscript_executor
def download_snapshot(snapshot_url, folder_path, time_stamp, max_snapshots):
    Path(folder_path).mkdir(parents=True, exist_ok=True)
    file_time_stamp = datetime.datetime.fromtimestamp(
        time_stamp).strftime('%Y%m%d-%H%M%S')
    url_request.urlretrieve(snapshot_url,
                            folder_path + "/" + file_time_stamp + ".jpg")
    clean_up_folder(folder_path, max_snapshots)


def log_netatmo_event(event_data, event_time, cameras, event_log_path, max_snapshots):
    if "camera_id" in event_data and event_data["event_type"] in ["human", "animal", "vehicle", "movement"]:
        for camera in cameras:
            if event_data["camera_id"] == camera["id"]:
                event_type = event_data["event_type"]
                picture_folder_path = "/config/tmp/" + \
                    camera["name"] + "/" + event_type + "/"
                if "snapshot_url" in event_data:
                    download_snapshot(
                        event_data["snapshot_url"], picture_folder_path, event_time, max_snapshots)
                else:
                    log.info("No downloadable snapshot")
    log_netatmo_event_to_file(event_data, event_time, event_log_path)


@time_trigger
def setup_netatmo_event_logger():
    global event_logger_instance

    log.info("Setting up netatmo event logger, logging to: " +
             pyscript.app_config["event_log"])

    @task_unique("netatmo_event_logger")
    @event_trigger("netatmo_event")
    def netatmo_event_logger(**kwargs):
        log.info("Received netatmo event: " + str(kwargs))
        if "data" in kwargs:
            event_time = time.time()
            event_data = kwargs["data"]
            cameras = pyscript.app_config["cameras"]
            event_log_path = pyscript.app_config["event_log"]
            max_snapshots = pyscript.app_config["max_snapshots"]
            log_netatmo_event(event_data, event_time, cameras,
                              event_log_path, max_snapshots)
    event_logger_instance = netatmo_event_logger
