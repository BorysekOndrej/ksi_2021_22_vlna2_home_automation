import json
from urllib.parse import urljoin, quote_plus

import requests

from config import DEVICES_BASE_URL, DEVICES_TYPES, ROOMS, ROOMS_PUBLIC, DEVICE_FILE

# Inspired by solution of Marek Haba
DEVICES = {key: {} for key in DEVICES_TYPES}


def create_device(device_type: str, room: str) -> str:
    response = requests.get(urljoin(DEVICES_BASE_URL, "new"+device_type))
    data = json.loads(response.text)
    device_id = data["id"]
    
    # Add a note, for example about the room
    notes = {"room": room}
    requests.post(urljoin(DEVICES_BASE_URL, f"device/{data['id']}/notes"), data=json.dumps(notes))
    return device_id


def save_devices() -> None:
    with open(DEVICE_FILE, "w") as file:
        json.dump(DEVICES, file, indent=4)


def link_motion_sensor(motionsensor_id: str, light_id: str) -> None:
    """Sets up motion sensor to turn the light on when it is triggered."""
    collector_url = quote_plus(urljoin(DEVICES_BASE_URL, f"device/{light_id}/state/ON"))
    requests.get(urljoin(DEVICES_BASE_URL, f"device/{motionsensor_id}/report_url?url={collector_url}"))


def link_smart_switch(switchsensor_id: str, light_id: str) -> None:
    """Sets up switch to toggle the light when it is triggerd."""
    collector_url = quote_plus(urljoin(DEVICES_BASE_URL, f"device/{light_id}/toggle"))
    requests.get(urljoin(DEVICES_BASE_URL, f"device/{switchsensor_id}/report_url?url={collector_url}"))


def main():
    for device_type in DEVICES_TYPES:
        for room_name in ROOMS:
            if room_name not in ROOMS_PUBLIC and device_type == "MotionSensor":
                continue  # Let's have motion sensors only in shared rooms 

            DEVICES[device_type][room_name] = create_device(device_type, room_name)

    for room_name in ROOMS:
        link_smart_switch(
            DEVICES["SwitchSensor"][room_name],
            DEVICES["SmartLight"][room_name]
        )
        
        if DEVICES["MotionSensor"].get(room_name, None):
            link_motion_sensor(
                DEVICES["MotionSensor"][room_name],
                DEVICES["SmartLight"][room_name]
            )

    save_devices()


if __name__ == "__main__":
    main()
