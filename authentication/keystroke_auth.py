import json
import os

def verify_typing(email, typed_text):

    path = f"storage/typing_profiles/{email}.json"

    if not os.path.exists(path):
        return False

    with open(path, "r") as file:
        profile = json.load(file)

    return typed_text.strip() == profile["text"].strip()