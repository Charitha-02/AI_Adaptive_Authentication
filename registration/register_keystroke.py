import os
import json

os.makedirs("storage/typing_profiles", exist_ok=True)

email = input("Enter Email: ")

print("\nType the following sentence exactly as shown:")
print("Artificial Intelligence improves cybersecurity")

input("\nPress Enter when you are ready...")

text = input("Type here: ")

profile = {
    "email": email,
    "text": text,
    "length": len(text)
}

with open(f"storage/typing_profiles/{email}.json", "w") as file:
    json.dump(profile, file, indent=4)

print("Typing profile registered successfully.")