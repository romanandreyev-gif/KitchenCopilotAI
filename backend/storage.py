import json
import os

PROFILE_FILE = "family_profile.json"


def save_profile(user_id, profile_text):
    data = {
        "user_id": user_id,
        "profile": profile_text
    }

    with open(PROFILE_FILE, "w") as file:
        json.dump(data, file, indent=4)


def load_profile():
    if not os.path.exists(PROFILE_FILE):
        return None

    with open(PROFILE_FILE, "r") as file:
        data = json.load(file)

    return data.get("profile")