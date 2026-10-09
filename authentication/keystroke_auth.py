import json
import os


def verify_typing(email, typed_text):

    path = f"storage/typing_profiles/{email}.json"

    if not os.path.exists(path):
        return False

    with open(path, "r") as file:
        profile = json.load(file)

    # Normalize typed input
    typed = " ".join(typed_text.strip().split()).lower()

    # New profile format
    if "sentence" in profile:

        registered = " ".join(
            profile["sentence"].strip().split()
        ).lower()

        return typed == registered

    # Multiple typing samples
    if "samples" in profile:

        for sample in profile["samples"]:

            sample_text = sample.get("text", "")

            registered = " ".join(
                sample_text.strip().split()
            ).lower()

            if typed == registered:
                return True

    # Old profile format
    if "text" in profile:

        registered = " ".join(
            profile["text"].strip().split()
        ).lower()

        return typed == registered

    return False