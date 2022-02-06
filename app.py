from typing import Tuple, Optional
import datetime
import os

from flask import abort, render_template, Flask, redirect, request, jsonify, url_for
from werkzeug import Response
from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity, jwt_required, set_access_cookies, unset_jwt_cookies
from dotenv import load_dotenv

from config import USERS, ROOMS_PRIVATE
from utils_sun import ColorTemperatureHelper
from util import *

g_cron_last_start = datetime.datetime.min
color_temperature_helper = ColorTemperatureHelper()

app = Flask(__name__)


# Security: The secret key should NEVER be part of the code itself, but part of some secret config that will never be shared.
#           I'll show how to do it on another variable bellow (JWT_SECRET_KEY).
app.secret_key = "The ships hung in the sky in much the same way that bricks don't."

# --- EXAMPLE OF LOGIN USING JSON WEB TOKENS (JWT) ---

# First you have to manually copy file .env.dist to file .env.
# Then modify it with random secret. 
load_dotenv()
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
assert app.config["JWT_SECRET_KEY"], "You've probably forgot to copy the .env.dist file to .env and modify it."

app.config["JWT_TOKEN_LOCATION"] = ["cookies"] # Beware that when cookies are used you might be vulnerable to Cross Site Request forgery. 
# app.config["JWT_COOKIE_SECURE"] = True  # This would make sure that the cookie is only transmitted via HTTPS.
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = datetime.timedelta(days=1)
jwt = JWTManager(app)


@app.route("/login", methods=["POST"])
def login_post():
    username = request.form.get("username", None)
    password = request.form.get("password", None)
    if username is None or password is None:
        return {"msg": "Username or password missing."}, 401
    if USERS.get(username, None) is None or USERS[username] != password:
        return {"msg": "Bad username or password"}, 401

    access_token = create_access_token(identity=username)
    response = redirect(url_for("map_get"))
    set_access_cookies(response, access_token)
    return response


@app.route("/login", methods=["GET"])
def login_get():
    return render_template("login.html")


@app.route("/logout", methods=["GET"])
def logout():
    response = redirect(url_for("map_get"))
    unset_jwt_cookies(response)
    return response


@app.route("/device/<string:device_id>/<path:command>")
@jwt_required()
def relay_command(device_id: str, command: str):
    username = get_jwt_identity()
    if not can_user_control_device(username, device_id):
        abort(401)
    Device.get(device_id, command)
    return redirect(url_for("map_get"))

# --- END OF JWT EXAMPLE ---


@app.route("/cron")
def cron():
    global g_cron_last_start
    """
        Note that using global like this only works correctly for one thread.
        If you run the server multiple times concurently each instance might have the it's own global.

        A better way would be to use a rate limiter, but that usually requires some external database/cache/storage.
        https://flask-limiter.readthedocs.io/en/stable/
    """

    current_time = datetime.datetime.now()
    if g_cron_last_start + datetime.timedelta(minutes=1) > current_time:
        return "Cron already called in the current minute"

    g_cron_last_start = current_time

    color_temperature_helper.change_light_colors()
    return "Cron finished"


# Try to avoid argument name "id". There is built-in Python function called id.
@app.route("/device/<string:device_id>")
@jwt_required(optional=True)
def device_info(device_id: str) -> str:
    username = get_jwt_identity()
    if not can_user_control_device(username, device_id):
        abort(401)
    resp_txt = Device.get(device_id)
    return json.loads(resp_txt)


@app.route("/map")
@jwt_required(optional=True)
def map_get():
    room_status = {}
    for room_name in get_devices()["SmartLight"]:
        light_info = Device.get(get_devices()["SmartLight"][room_name], "")
        light_info_json = json.loads(light_info)
        room_status[room_name] = f'{room_name} <br> {light_info_json["color_temperature"]} <br> {light_info_json["current_state"]}'

    return render_template("flat_map.html", room_status=room_status, username=get_jwt_identity())


@app.route("/bill")
@jwt_required(optional=True)
def bill():
    usage = {}

    for room_name in get_devices()["SmartLight"]:
        if room_name in ROOMS_PUBLIC:
            continue

        device_id = get_devices()["SmartLight"][room_name] 
        usage[room_name] = int(json.loads(Device.get(device_id))["power_usage"])
    
    total_usage = sum(usage.values())
    for room_name in ROOMS_PRIVATE:
        usage[room_name] = round(usage[room_name] / total_usage * 100, 2)
        # note that rounding might cause sum() != 100%

    return render_template("bill.html", usage=usage, username=get_jwt_identity())


@app.route("/")
@jwt_required(optional=True)
def root():
    return render_template("base.html", username=get_jwt_identity())


@app.route("/device_list")
@jwt_required()
def device_list():
    username = get_jwt_identity()

    lights = {}
    other_devices = {}

    for device_type in get_devices():
        for room_name in get_devices()[device_type]:
            if can_user_control_room(username, room_name):
                url = f'/device/{get_devices()[device_type][room_name]}'
                if device_type == "SmartLight":
                    lights[room_name] = url
                else:
                    other_devices[f"{room_name} - {device_type}"] = url

    return render_template("device_list.html", devices=other_devices, lights=lights, username=username)


if __name__ == "__main__":
    app.run(debug=True)
