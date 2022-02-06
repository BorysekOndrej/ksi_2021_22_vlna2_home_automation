import requests
from config import DEVICES_BASE_URL, ROOMS_PUBLIC, DEVICE_FILE
from flask import abort
from typing import Optional, Dict
import json


class Device:
    @staticmethod
    def get(device_id: str, command: Optional[str] = None) -> str:
        url = f"{DEVICES_BASE_URL}device/{device_id}"
        if command:
            url += f"/{command}"

        resp = requests.get(url)
        if resp.status_code != 200:
            abort(500)
        return resp.text


def can_user_control_room(username: str, room: str) -> bool:
    return room in ROOMS_PUBLIC or username == room


def can_user_control_device(username: str, device_id: str) -> bool:
    devices = get_devices()

    for device_type in devices:
        for room_name in devices[device_type]:
            if devices[device_type][room_name] == device_id:
                return can_user_control_room(username, room_name)

    return False


class FileLoadingCache:
    """
        This cache presumes that the path is unique.
        It does not correctly handle cache clear for relative vs absolute path.

        Also, the cache is not shared across threads.
    """

    def __init__(self) -> None:
        self.__cache: Dict[str, str] = {}

    def load(self, path: str, reload: bool = False) -> str:
        if reload:
            del self.__cache[path]

        if self.__cache.get(path, None) is None:
            with open(path) as f:
                self.__cache[path] = f.read()

        return self.__cache[path]

    def clear_whole_cache(self):
        self.__cache = {}


def get_devices(reload: bool = False) -> Dict[str, Dict[str, str]]:
    return json.loads(file_cache.load(DEVICE_FILE, reload))


file_cache = FileLoadingCache()
