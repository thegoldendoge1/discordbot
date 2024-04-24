import datetime
import json


def log(message):
    current_time = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    print(f"{current_time} {message}")
    return f"{current_time} {message}"


def format_duration(duration_seconds):
    minutes = duration_seconds // 60
    seconds = duration_seconds % 60
    return f"{minutes}:{seconds:02d}"


def add_xp(*, user, server_id, xp: int) -> None:
    user_id = user.id
    is_bot = user.bot
    user_id = str(user_id)
    filename = f"./ranks/{server_id}.json"
    try:
        file = open(filename, 'r+')
    except IOError:
        file = open(filename, 'w+')
    with open(filename, "r+", encoding="utf-8") as file:
        try:
            user_data = json.load(file)
        except:
            user_data = {}
    if user_id in user_data and not is_bot:
        user_data[user_id] += xp
        log(f"XP user {user_id} + {xp}")
    elif user_id not in user_data and not is_bot:
        log(f"New user {user_id} added!")
        user_data[user_id] = 0

    with open(filename, "w+", encoding="utf-8") as file:
        json.dump(user_data, file, indent=4)
