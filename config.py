DEVICES_BASE_URL = "https://home_automation.iamroot.eu/"
DEVICES_TYPES = ("SmartLight", "MotionSensor", "SwitchSensor")
DAYTEMP = 6500
NIGHTTEMP = 2300

DEVICE_FILE = "devices.json"

USERS = {
    'Karlik': '1234',
    'SobKarsob': '1234',
    'LosKarlos': '1234',
    'ZelvickaJulie': '1234'
}

ROOMS_PRIVATE = [x for x in USERS]
ROOMS_PUBLIC = ['Kuchyň', 'Obyvák', 'Koupelna']
ROOMS = ROOMS_PUBLIC + ROOMS_PRIVATE
