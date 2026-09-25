import random

def check_liveness():
    """
    Simulates face liveness detection.
    Replace this with a real liveness model in the future.
    """
    score = random.randint(80, 100)

    if score >= 90:
        return True, score
    else:
        return False, score