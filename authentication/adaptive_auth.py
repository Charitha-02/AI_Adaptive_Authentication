def check_risk(
    face_verified,
    liveness_verified,
    keystroke_verified,
    typing_deviation=0,
    previous_anomalies=0
):

    risk_score = 0
    reasons = []

    if not face_verified:
        risk_score += 35
        reasons.append("Face verification failed")

    if not liveness_verified:
        risk_score += 25
        reasons.append("Liveness verification failed")

    if not keystroke_verified:
        risk_score += 25
        reasons.append("Typing verification failed")

    if typing_deviation <= 20:

        pass

    elif typing_deviation <= 40:

        risk_score += 10
        reasons.append("Minor typing deviation")

    elif typing_deviation <= 60:

        risk_score += 30
        reasons.append("Significant typing deviation")

    else:

        risk_score += 50
        reasons.append("Major typing anomaly")

    risk_score += min(
        previous_anomalies * 5,
        15
    )

    risk_score = min(
        risk_score,
        100
    )

    if risk_score <= 20:

        level = "LOW"

    elif risk_score <= 50:

        level = "MEDIUM"

    else:

        level = "HIGH"

    if not reasons:

        reasons.append(
            "All authentication signals are normal"
        )

    return risk_score, level, reasons