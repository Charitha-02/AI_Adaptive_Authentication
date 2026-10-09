import json
import os
import statistics

PROFILE_FOLDER = "storage/typing_profiles"


def get_profile(email):
    path = os.path.join(PROFILE_FOLDER, f"{email}.json")
    if not os.path.exists(path):
        return None

    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return None


def calculate_typing_speed(text, duration):
    if duration <= 0:
        duration = 0.1

    characters = len(text.strip())
    return characters / duration


def _get_speed_stats(profile):
    """Get the user's personalized speed baseline and variability."""
    samples = profile.get("samples", [])
    speeds = []

    for sample in samples:
        try:
            value = float(sample.get("speed", 0))
            if value > 0:
                speeds.append(value)
        except (TypeError, ValueError):
            pass

    baseline = float(
        profile.get(
            "average_speed",
            profile.get("speed", 0)
        ) or 0
    )

    if baseline <= 0 and speeds:
        baseline = statistics.mean(speeds)

    if len(speeds) >= 2:
        std = statistics.stdev(speeds)
    else:
        std = float(profile.get("speed_std", 0) or 0)

    minimum = float(profile.get("min_speed", min(speeds) if speeds else 0) or 0)
    maximum = float(profile.get("max_speed", max(speeds) if speeds else 0) or 0)

    return baseline, std, minimum, maximum


def analyze_typing(email, text, duration):
    """
    Personalized continuous behavioral authentication.

    Existing behavior is preserved:
      - current typing speed
      - baseline speed
      - percentage deviation
      - NORMAL / SUSPICIOUS / ANOMALY

    New behavior:
      - personalized speed variability (standard deviation)
      - z-score against the user's own typing profile
      - behavioral confidence score
      - speed consistency score

    This is intentionally a lightweight statistical extension.
    It does NOT claim to capture key-down/key-up dwell or flight time,
    because the current Streamlit input does not expose those raw events.
    """

    profile = get_profile(email)

    if not profile:
        return {
            "anomaly": True,
            "status": "PROFILE_NOT_FOUND",
            "risk": "HIGH",
            "deviation": 100,
            "current_speed": 0,
            "baseline_speed": 0,
            "speed_std": 0,
            "z_score": 999,
            "behavioral_score": 0,
            "speed_consistency": 0,
        }

    baseline_speed, speed_std, min_speed, max_speed = _get_speed_stats(profile)

    if baseline_speed <= 0:
        return {
            "anomaly": True,
            "status": "INVALID_PROFILE",
            "risk": "HIGH",
            "deviation": 100,
            "current_speed": 0,
            "baseline_speed": 0,
            "speed_std": speed_std,
            "z_score": 999,
            "behavioral_score": 0,
            "speed_consistency": 0,
        }

    current_speed = calculate_typing_speed(text, duration)

    deviation = (
        abs(current_speed - baseline_speed)
        / baseline_speed
        * 100
    )

    # Personalized variability:
    # z-score is useful when the user naturally types at different speeds.
    if speed_std > 0.01:
        z_score = abs(current_speed - baseline_speed) / speed_std
    else:
        z_score = deviation / 10.0

    # A lightweight confidence score combining deviation and
    # how unusual the speed is for this specific user.
    deviation_component = max(0.0, 100.0 - min(deviation, 100.0))
    z_component = max(0.0, 100.0 - min(z_score * 25.0, 100.0))
    behavioral_score = (deviation_component * 0.6) + (z_component * 0.4)

    # Small bonus when the current speed remains inside the registered range.
    if min_speed > 0 and max_speed > 0 and min_speed <= current_speed <= max_speed:
        behavioral_score = min(100.0, behavioral_score + 8.0)

    behavioral_score = round(max(0.0, min(100.0, behavioral_score)), 2)

    # Consistency of the registered profile itself.
    if baseline_speed > 0:
        speed_consistency = max(
            0.0,
            min(100.0, 100.0 - ((speed_std / baseline_speed) * 100.0))
        )
    else:
        speed_consistency = 0.0

    speed_consistency = round(speed_consistency, 2)
    z_score = round(z_score, 2)

    # Preserve the existing 25% normal boundary, but also use
    # the personalized z-score to detect unusual behavior.
    if deviation <= 25 and z_score <= 2.5:
        return {
            "anomaly": False,
            "status": "NORMAL",
            "risk": "LOW",
            "deviation": round(deviation, 2),
            "current_speed": round(current_speed, 2),
            "baseline_speed": round(baseline_speed, 2),
            "speed_std": round(speed_std, 2),
            "z_score": z_score,
            "behavioral_score": behavioral_score,
            "speed_consistency": speed_consistency,
        }

    if deviation <= 40 and z_score <= 3.5:
        return {
            "anomaly": True,
            "status": "SUSPICIOUS",
            "risk": "MEDIUM",
            "deviation": round(deviation, 2),
            "current_speed": round(current_speed, 2),
            "baseline_speed": round(baseline_speed, 2),
            "speed_std": round(speed_std, 2),
            "z_score": z_score,
            "behavioral_score": behavioral_score,
            "speed_consistency": speed_consistency,
        }

    return {
        "anomaly": True,
        "status": "ANOMALY",
        "risk": "HIGH",
        "deviation": round(deviation, 2),
        "current_speed": round(current_speed, 2),
        "baseline_speed": round(baseline_speed, 2),
        "speed_std": round(speed_std, 2),
        "z_score": z_score,
        "behavioral_score": behavioral_score,
        "speed_consistency": speed_consistency,
    }
