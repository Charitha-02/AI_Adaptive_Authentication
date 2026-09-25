import random

def check_risk():

    score = random.randint(1, 100)

    if score <= 30:
        return score, "LOW"

    elif score <= 70:
        return score, "MEDIUM"

    else:
        return score, "HIGH"