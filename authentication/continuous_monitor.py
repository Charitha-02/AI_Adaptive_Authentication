import json
import os


PROFILE_FOLDER = "storage/typing_profiles"


def get_profile(email):

    path = f"{PROFILE_FOLDER}/{email}.json"

    if not os.path.exists(path):
        return None

    with open(path, "r") as file:
        return json.load(file)


def calculate_typing_speed(text, duration):

    if duration <= 0:
        duration = 0.1

    characters = len(text.strip())

    return characters / duration


def analyze_typing(email, text, duration):

    profile = get_profile(email)

    if not profile:
        return {
            "anomaly": True,
            "status": "PROFILE_NOT_FOUND",
            "risk": "HIGH",
            "deviation": 100,
            "current_speed": 0,
            "baseline_speed": 0
        }

    baseline_speed = profile.get("speed", 0)

    if baseline_speed <= 0:

        old_duration = profile.get("duration", 1)
        old_length = profile.get("length", 1)

        baseline_speed = old_length / max(old_duration, 0.1)

    current_speed = calculate_typing_speed(text, duration)

    deviation = abs(
        current_speed - baseline_speed
    ) / baseline_speed * 100

    # More than 40% difference = suspicious
    if deviation <= 40:

        return {
            "anomaly": False,
            "status": "NORMAL",
            "risk": "LOW",
            "deviation": round(deviation, 2),
            "current_speed": round(current_speed, 2),
            "baseline_speed": round(baseline_speed, 2)
        }

    elif deviation <= 60:

        return {
            "anomaly": True,
            "status": "SUSPICIOUS",
            "risk": "MEDIUM",
            "deviation": round(deviation, 2),
            "current_speed": round(current_speed, 2),
            "baseline_speed": round(baseline_speed, 2)
        }

    else:

        return {
            "anomaly": True,
            "status": "ANOMALY",
            "risk": "HIGH",
            "deviation": round(deviation, 2),
            "current_speed": round(current_speed, 2),
            "baseline_speed": round(baseline_speed, 2)
        }