from typing import Tuple, Optional
from pathlib import Path
import json
import datetime

import requests
import werkzeug
from flask import abort

from config import *
from util import Device, get_devices


class ColorTemperatureHelper:
    def __init__(self) -> None:
        self.color_previous = 6500

    def change_light_colors(self):
        color_next = self.__calculate_light_temp()
        if self.color_previous == color_next:
            return

        self.color_previous = color_next

        for room_name in ROOMS:
            light_id = get_devices()["SmartLight"][room_name]
            Device.get(light_id, f"/color_temperature/{color_next}")


    def __get_sun_times(self, lat: str = "49.2099", long: str = "16.5989") -> Tuple[datetime.datetime, datetime.datetime]:
        """
        Replacing this with a call to library would be much shorter, but not as educative for API handling. 
        """

        day = datetime.date.today()
        url = f"https://api.sunrise-sunset.org/json?lat={lat}&lng={long}&date={day}"

        sunfile_basic = f"sun_{lat}_{long}_{day}.json"
        sunfile_safe = werkzeug.utils.secure_filename(sunfile_basic)

        if Path(sunfile_safe).is_file():
            with open(sunfile_safe) as f:
                data = json.load(f)
        else:
            with open(sunfile_safe, "w") as f:
                resp = requests.get(url)
                if resp.status_code != 200:
                    abort(400)

                data = resp.json()
                json.dump(data, f)

        sunrise = datetime.datetime.combine(day, self.__extract_time_from_sun_text(data["results"]["sunrise"]))
        sunset = datetime.datetime.combine(day, self.__extract_time_from_sun_text(data["results"]["sunset"]))
        return sunrise, sunset


    def __extract_time_from_sun_text(self, text: str) -> datetime.time:
        hour, minute, second = text.split(" ")[0].split(":")
        return datetime.time(int(hour), int(minute), int(second))


    def __calculate_normalized_offset(self, start: datetime.datetime, change_interval: datetime.timedelta) -> float:
        current_time = datetime.datetime.now()
        percentage = (current_time - start)/change_interval
        return max(min(1, percentage), 0)  # return from range <0, 1>


    def __calculate_light_temp(self, current_time: Optional[datetime.datetime] = None) -> int:
        CHANGE_INTERVAL = datetime.timedelta(hours=1, minutes=30)
        NIGHT_TEMP = 2300
        DAY_TEMP = 6500  

        sunrise, sunset = self.__get_sun_times()
        if current_time is None:
            current_time = datetime.datetime.now()

        start_sunrise = sunrise - CHANGE_INTERVAL
        end_sunset = sunset + CHANGE_INTERVAL

        if current_time < start_sunrise or current_time > end_sunset:
            return NIGHT_TEMP

        if sunrise < current_time < sunset:
            return DAY_TEMP

        offset1 = self.__calculate_normalized_offset(start_sunrise, CHANGE_INTERVAL)
        offset2 = self.__calculate_normalized_offset(sunset, CHANGE_INTERVAL)
        offset = max(offset1, offset2) # <0, 1>

        return int(NIGHT_TEMP + (DAY_TEMP - NIGHT_TEMP) * offset)
