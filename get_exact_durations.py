import os
import django
import requests
import json
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gymproject.settings')
django.setup()

from django.conf import settings
from gymapp.services.youtube_service import YouTubeService

# Get the list of all video IDs in mock database
lookup = {
    "push-ups": "IODxDxX7oi4",
    "pull-ups": "eGo4IYlbE5g",
    "squats": "aclHkVaku9U",
    "bench press": "hWbUlkb5Ms4",
    "deadlift": "op9kVnSso6Q",
    "plank": "ASdvN_XEl_c",
    "lunges": "3XDriUn0udo",
    "shoulder press": "qEwKCR5JCog",
    "bicep curls": "ykJmrZ5v0Oo",
    "tricep dips": "6kALZikXxLc",
    "lat pulldown": "bNmvKpJSWKM",
    "bent over rows": "WkFX6_GxAs8",
    "calf raises": "gwLzBJYoWlI",
    "burpees": "auBLPXO8Fww",
    "mountain climbers": "nmwgirgXLYM",
    "bicycle crunches": "9FGilxCbdz8",
    "crunches": "Xyd_fa5zoEU",
    "brisk walking": "enYITYwvPAQ",
    "jogging": "kVnyY17VS9Y",
    "stationary cycling": "dieOsJlsvpM",
    "high knees": "OAJ_J3EZkdY",
    "box jumps": "bXgFx93CGow",
    "stair climbing": "6mYp_BNYD5Y",
    "swimming": "GlcG6LtytyQ",
    "rowing": "uqs9A0B6s9U",
    "downward dog pose": "UsTTTYbBdQg",
    "child's pose": "eqVMAPM00DM",
    "warrior pose": "56hnUF1scTE",
    "sun salutation": "IPuN-b71HgQ",
    "tree pose": "2KuBgfDoFyM",
    "cobra pose": "luTSRGXPEMs",
    "cat cow pose": "kqnua4rHVVA",
    "bridge pose": "H2oJdqGikTY",
    "seated forward bend": "wVdOp3h1nog",
    "pigeon pose": "F4rC8C-GbVk",
}

api_key = settings.YOUTUBE_API_KEY
video_ids = list(lookup.values())

response = requests.get(
    "https://www.googleapis.com/youtube/v3/videos",
    params={
        "key": api_key,
        "id": ",".join(video_ids),
        "part": "contentDetails,snippet"
    }
)
items = response.json().get("items", [])

details = {}
for item in items:
    vid = item["id"]
    title = item["snippet"]["title"]
    duration = item["contentDetails"]["duration"]
    parsed = YouTubeService._parse_iso_duration(duration)
    details[vid] = (parsed, title)

for name, vid in lookup.items():
    info = details.get(vid, ("5 mins", "Unknown"))
    print(f'"{name}": ("{vid}", "{info[0]}"), # {info[1]}')
