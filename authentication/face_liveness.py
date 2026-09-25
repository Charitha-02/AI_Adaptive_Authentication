import random

def check_liveness():

    score = random.randint(80, 100)

    if score >= 90:
        return True, score
    else:
        return False, score