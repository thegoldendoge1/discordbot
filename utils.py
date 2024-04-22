import datetime


def log(message):
    current_time = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    print(f"{current_time} {message}")
    return f"{current_time} {message}"


def format_duration(duration_seconds):
    minutes = duration_seconds // 60
    seconds = duration_seconds % 60
    return f"{minutes}:{seconds:02d}"
