import logging
import os
import re
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class YouTubeService:
    SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
    VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"

    @staticmethod
    def get_exercise_videos(exercises_list):
        """
        Return a map of lowercase exercise name to YouTube video details.
        Live API results are verified with videos.list before an embed URL is used.
        """
        api_key = getattr(settings, "YOUTUBE_API_KEY", "") or os.environ.get("YOUTUBE_API_KEY")

        results = {}
        if not api_key:
            logger.warning("YOUTUBE_API_KEY is not defined. Using fallback video map.")
            for exercise in exercises_list:
                if exercise:
                    results[exercise.lower()] = YouTubeService._get_mock_video(exercise)
            return results

        for exercise in exercises_list:
            if not exercise:
                continue

            exercise_key = exercise.lower()
            if exercise_key in results:
                continue

            params = {
                "key": api_key,
                "q": f"{exercise} workout tutorial",
                "part": "snippet",
                "type": "video",
                "videoEmbeddable": "true",
                "videoDefinition": "high",
                "relevanceLanguage": "en",
                "safeSearch": "strict",
                "maxResults": 5,
            }

            try:
                response = requests.get(YouTubeService.SEARCH_URL, params=params, timeout=10)
                response.raise_for_status()
                video = YouTubeService._pick_embeddable_video(
                    api_key,
                    exercise,
                    response.json().get("items", []),
                )
                results[exercise_key] = video or YouTubeService._get_mock_video(exercise)
            except Exception as exc:
                logger.error(f"Error fetching YouTube video for '{exercise}': {exc}")
                results[exercise_key] = YouTubeService._get_mock_video(exercise)

        return results

    @staticmethod
    def _pick_embeddable_video(api_key, exercise_name, search_items):
        video_ids = []
        search_snippets = {}

        for item in search_items:
            video_id = item.get("id", {}).get("videoId")
            if not video_id:
                continue
            video_ids.append(video_id)
            search_snippets[video_id] = item.get("snippet", {})

        if not video_ids:
            return None

        try:
            response = requests.get(
                YouTubeService.VIDEOS_URL,
                params={
                    "key": api_key,
                    "id": ",".join(video_ids),
                    "part": "snippet,status,contentDetails",  # ← Add contentDetails
                },
                timeout=10,
            )
            response.raise_for_status()
        except Exception as exc:
            logger.warning(f"Unable to verify YouTube embed status for '{exercise_name}': {exc}")
            return None

        verified_items = {
            item.get("id"): item
            for item in response.json().get("items", [])
            if item.get("id")
        }

        for video_id in video_ids:
            item = verified_items.get(video_id)
            if not item:
                continue

            status = item.get("status", {})
            if status.get("privacyStatus") != "public" or not status.get("embeddable"):
                continue

            content_details = item.get("contentDetails") or {}
            iso_duration = content_details.get("duration", "PT5M")
            parsed_duration = YouTubeService._parse_iso_duration(iso_duration)

            snippet = item.get("snippet") or search_snippets.get(video_id, {})
            return YouTubeService._build_video_details(exercise_name, video_id, snippet, parsed_duration)

        return None

    @staticmethod
    def _build_video_details(exercise_name, video_id, snippet=None, duration="5 mins"):
        snippet = snippet or {}
        thumbnail = (
            snippet.get("thumbnails", {})
            .get("medium", {})
            .get("url", f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg")
        )

        return {
            "exercise": exercise_name,
            "video_id": video_id,
            "title": snippet.get("title") or f"{exercise_name} - Proper Form & Technique",
            "thumbnail": thumbnail,
            "duration": duration,
            "embed_url": f"https://www.youtube.com/embed/{video_id}?rel=0&modestbranding=1",
        }

    @staticmethod
    def _parse_iso_duration(iso_duration):
        """
        Parses PT1H2M10S to a readable format (e.g. '1 hr 2 mins 10 secs')
        """
        pattern = re.compile(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?')
        match = re.match(pattern, iso_duration)
        if not match:
            return "5 mins"

        hours, minutes, seconds = match.groups()
        parts = []
        if hours:
            parts.append(f"{hours} hr" + ("s" if int(hours) > 1 else ""))
        if minutes:
            parts.append(f"{minutes} min" + ("s" if int(minutes) > 1 else ""))
        if seconds:
            parts.append(f"{seconds} sec" + ("s" if int(seconds) > 1 else ""))

        return " ".join(parts) if parts else "5 mins"

    @staticmethod
    def _get_mock_video(exercise_name):
        """
        Fallback lookup table with public, embeddable YouTube video IDs.
        """
        lookup = {
            # Weight training
            "push-ups": ("IODxDxX7oi4", "3 mins 38 secs"),
            "push ups": ("IODxDxX7oi4", "3 mins 38 secs"),
            "push-up": ("IODxDxX7oi4", "3 mins 38 secs"),
            "pull-ups": ("eGo4IYlbE5g", "4 mins 32 secs"),
            "pull ups": ("eGo4IYlbE5g", "4 mins 32 secs"),
            "pull-up": ("eGo4IYlbE5g", "4 mins 32 secs"),
            "squats": ("aclHkVaku9U", "1 min 52 secs"),
            "bodyweight squats": ("aclHkVaku9U", "1 min 52 secs"),
            "dumbbell squats": ("aclHkVaku9U", "1 min 52 secs"),
            "bench press": ("hWbUlkb5Ms4", "51 secs"),
            "dumbbell chest press": ("hWbUlkb5Ms4", "51 secs"),
            "chest press": ("hWbUlkb5Ms4", "51 secs"),
            "deadlift": ("op9kVnSso6Q", "58 secs"),
            "romanian deadlift": ("op9kVnSso6Q", "58 secs"),
            "plank": ("ASdvN_XEl_c", "3 mins 26 secs"),
            "lunges": ("3XDriUn0udo", "4 mins 20 secs"),
            "dumbbell lunges": ("3XDriUn0udo", "4 mins 20 secs"),
            "shoulder press": ("qEwKCR5JCog", "2 mins 24 secs"),
            "overhead press": ("qEwKCR5JCog", "2 mins 24 secs"),
            "bicep curls": ("ykJmrZ5v0Oo", "1 min 49 secs"),
            "dumbbell curls": ("ykJmrZ5v0Oo", "1 min 49 secs"),
            "tricep dips": ("6kALZikXxLc", "1 min 28 secs"),
            "dips": ("6kALZikXxLc", "1 min 28 secs"),
            "lat pulldown": ("bNmvKpJSWKM", "13 secs"),
            "bent over rows": ("WkFX6_GxAs8", "9 secs"),
            "dumbbell rows": ("WkFX6_GxAs8", "9 secs"),
            "calf raises": ("gwLzBJYoWlI", "2 mins 20 secs"),
            "burpees": ("auBLPXO8Fww", "52 secs"),
            "mountain climbers": ("nmwgirgXLYM", "1 min 23 secs"),
            "bicycle crunches": ("9FGilxCbdz8", "1 min 25 secs"),
            "crunches": ("Xyd_fa5zoEU", "1 min 27 secs"),
            # Cardio
            "brisk walking": ("enYITYwvPAQ", "31 mins 31 secs"),
            "walking": ("enYITYwvPAQ", "31 mins 31 secs"),
            "jogging": ("kVnyY17VS9Y", "6 mins 30 secs"),
            "running": ("kVnyY17VS9Y", "6 mins 30 secs"),
            "treadmill run": ("kVnyY17VS9Y", "6 mins 30 secs"),
            "treadmill jogging": ("kVnyY17VS9Y", "6 mins 30 secs"),
            "jumping jacks": ("iSSAk4XCsRA", "45 secs"),
            "jump rope": ("u3zgHI8QnqE", "2 mins 44 secs"),
            "skipping": ("u3zgHI8QnqE", "2 mins 44 secs"),
            "stationary cycling": ("dieOsJlsvpM", "20 secs"),
            "cycling": ("dieOsJlsvpM", "20 secs"),
            "high knees": ("OAJ_J3EZkdY", "2 mins 17 secs"),
            "box jumps": ("bXgFx93CGow", "20 secs"),
            "stair climbing": ("6mYp_BNYD5Y", "12 secs"),
            "swimming": ("GlcG6LtytyQ", "15 secs"),
            "rowing": ("uqs9A0B6s9U", "15 mins 48 secs"),
            # Yoga
            "downward dog pose": ("UsTTTYbBdQg", "55 secs"),
            "downward dog": ("UsTTTYbBdQg", "55 secs"),
            "child's pose": ("eqVMAPM00DM", "6 mins 14 secs"),
            "childs pose": ("eqVMAPM00DM", "6 mins 14 secs"),
            "warrior pose": ("56hnUF1scTE", "15 secs"),
            "warrior i": ("56hnUF1scTE", "15 secs"),
            "warrior ii": ("56hnUF1scTE", "15 secs"),
            "sun salutation": ("IPuN-b71HgQ", "42 secs"),
            "tree pose": ("2KuBgfDoFyM", "16 secs"),
            "cobra pose": ("luTSRGXPEMs", "6 mins 51 secs"),
            "cat cow pose": ("kqnua4rHVVA", "1 min 44 secs"),
            "bridge pose": ("H2oJdqGikTY", "10 secs"),
            "seated forward bend": ("wVdOp3h1nog", "15 secs"),
            "pigeon pose": ("F4rC8C-GbVk", "14 secs"),
        }

        exercise_key = exercise_name.lower().strip()
        pair = lookup.get(exercise_key)

        video_id = None
        duration = "5 mins"

        if pair:
            video_id, duration = pair

        if not video_id:
            for key, value in lookup.items():
                if key in exercise_key or exercise_key in key:
                    video_id, duration = value
                    break

        if not video_id:
            video_id = "aclHkVaku9U"
            duration = "5 mins"

        return YouTubeService._build_video_details(exercise_name, video_id, duration=duration)
