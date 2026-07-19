from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from .models import UserProfile
from .services.youtube_service import YouTubeService
import json
from unittest.mock import patch

class RecommendationSystemTests(TestCase):
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(username="testuser", password="testpassword123")
        self.client = Client()
        self.client.login(username="testuser", password="testpassword123")

    def test_save_profile_requires_login(self):
        # Test saved profile endpoint works when logged in
        payload = {
            "name": "Jane Doe",
            "age": 28,
            "weight": 65.5,
            "height": 168.0,
            "gender": "Female",
            "goal": "Fat Loss",
            "experience": "intermediate",
            "workout_place": "home"
        }
        response = self.client.post(
            reverse("api_save_profile"),
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("profile_id", data)

        # Check in DB
        profile = UserProfile.objects.get(id=data["profile_id"])
        self.assertEqual(profile.name, "Jane Doe")
        self.assertEqual(profile.goal, "Fat Loss")

    def test_choose_workout_page_renders(self):
        profile = UserProfile.objects.create(
            user=self.user,
            name="John Fit",
            age=25,
            weight=75,
            height=175,
            gender="Male",
            goal="weight gain",
            experience="beginner",
            workout_place="Gym"
        )
        response = self.client.get(reverse("choose_workout"), {"profile_id": profile.id})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Choose Your Workout Type")

    @override_settings(GROQ_API_KEY="", YOUTUBE_API_KEY="")
    def test_api_generate_plan_mock(self):
        profile = UserProfile.objects.create(
            user=self.user,
            name="John Fit",
            age=25,
            weight=75,
            height=175,
            gender="Male",
            goal="weight gain",
            experience="beginner",
            workout_place="Gym"
        )
        # Test requesting Weight Training and Cardio (no Yoga)
        payload = {
            "profile_id": profile.id,
            "categories": ["weight_training", "cardio"]
        }
        response = self.client.post(
            reverse("api_generate_plan"),
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Weight training and cardio must be present
        self.assertIn("weight_training", data)
        self.assertIn("cardio", data)
        # Yoga must NOT be present (Requirement 6)
        self.assertNotIn("yoga", data)
        self.assertIn("diet_plan", data)

        # Ensure YouTube details are merged (Requirement 8)
        wt_day1_exercises = data["weight_training"]["day1"]
        self.assertTrue(len(wt_day1_exercises) > 0)
        first_ex = wt_day1_exercises[0]
        self.assertIn("video", first_ex)
        self.assertIn("embed_url", first_ex["video"])
        self.assertIn("video_id", first_ex["video"])

    @override_settings(YOUTUBE_API_KEY="")
    def test_fallback_video_ids_do_not_use_known_stale_ids(self):
        stale_ids = {
            "SCVCLChPQEY",
            "roCP_too8fE",
            "CAwf7n6Tuhs",
            "lU4yKMNSzMQ",
            "LkJFBGqGGS4",
            "52FRpHMoFuM",
            "3E06kHDQSyk",
            "4z2_dVlFrM8",
            "H0r8HX8jFlQ",
            "ayVIHOYBXKM",
            "2MJGcgRYNew",
            "gej6yWSUINQ",
            "C_VtOa4KXGM",
            "nULQNDKNSmU",
            "o2JK-O1oZFc",
            "1LVUGS4BJOQ",
        }
        exercises = [
            "Bench Press",
            "Dumbbell Rows",
            "Lat Pulldown",
            "Brisk Walking",
            "Stationary Cycling",
            "Box Jumps",
            "Stair Climbing",
            "Swimming",
            "Rowing",
            "Downward Dog",
            "Child's Pose",
            "Warrior Pose",
            "Sun Salutation",
            "Bridge Pose",
            "Seated Forward Bend",
            "Pigeon Pose",
        ]

        for exercise in exercises:
            video = YouTubeService._get_mock_video(exercise)
            self.assertNotIn(video["video_id"], stale_ids)
            self.assertEqual(
                video["embed_url"],
                f"https://www.youtube.com/embed/{video['video_id']}?rel=0&modestbranding=1",
            )

    @override_settings(YOUTUBE_API_KEY="test-key")
    @patch("gymapp.services.youtube_service.requests.get")
    def test_youtube_api_result_must_be_public_and_embeddable(self, mock_get):
        class FakeResponse:
            def __init__(self, payload):
                self.payload = payload

            def raise_for_status(self):
                return None

            def json(self):
                return self.payload

        def fake_get(url, params=None, timeout=None):
            if url == YouTubeService.SEARCH_URL:
                return FakeResponse({
                    "items": [
                        {"id": {"videoId": "badvideo001"}, "snippet": {"title": "Bad"}},
                        {"id": {"videoId": "goodvideo01"}, "snippet": {"title": "Good"}},
                    ]
                })
            if url == YouTubeService.VIDEOS_URL:
                return FakeResponse({
                    "items": [
                        {
                            "id": "badvideo001",
                            "status": {"privacyStatus": "public", "embeddable": False},
                            "snippet": {"title": "Bad"},
                        },
                        {
                            "id": "goodvideo01",
                            "status": {"privacyStatus": "public", "embeddable": True},
                            "snippet": {
                                "title": "Good tutorial",
                                "thumbnails": {"medium": {"url": "https://example.com/thumb.jpg"}},
                            },
                        },
                    ]
                })
            raise AssertionError(f"Unexpected URL: {url}")

        mock_get.side_effect = fake_get

        videos = YouTubeService.get_exercise_videos(["Push-Ups"])

        self.assertEqual(videos["push-ups"]["video_id"], "goodvideo01")
        self.assertEqual(videos["push-ups"]["title"], "Good tutorial")

    @override_settings(GROQ_API_KEY="", YOUTUBE_API_KEY="")
    def test_saved_plan_lifecycle_and_views(self):
        from .models import GeneratedPlan
        
        # 1. Initially, no plan exists for the user
        self.assertFalse(GeneratedPlan.objects.filter(user=self.user).exists())
        
        # Check that register member and home views render with plan_exists = False
        response_home = self.client.get(reverse("home"))
        self.assertEqual(response_home.status_code, 200)
        self.assertFalse(response_home.context.get("plan_exists", True))
        
        response_reg = self.client.get(reverse("register_member"))
        self.assertEqual(response_reg.status_code, 200)
        self.assertFalse(response_reg.context.get("plan_exists", True))
        self.assertContains(response_reg, "Rs 0")
        
        # 2. Setup user profile
        profile = UserProfile.objects.create(
            user=self.user,
            name="John Fit",
            age=25,
            weight=75,
            height=175,
            gender="Male",
            goal="weight gain",
            experience="beginner",
            workout_place="Gym"
        )
        
        # 3. Generate plan via API
        payload = {
            "profile_id": profile.id,
            "categories": ["weight_training"]
        }
        response_gen = self.client.post(
            reverse("api_generate_plan"),
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(response_gen.status_code, 200)
        
        # 4. Verify GeneratedPlan object is created in the database
        self.assertTrue(GeneratedPlan.objects.filter(user=self.user).exists())
        saved_plan = GeneratedPlan.objects.get(user=self.user)
        self.assertEqual(saved_plan.profile, profile)
        
        # 5. Check that templates now receive plan_exists = True
        response_home = self.client.get(reverse("home"))
        self.assertEqual(response_home.status_code, 200)
        self.assertTrue(response_home.context.get("plan_exists"))
        
        response_reg = self.client.get(reverse("register_member"))
        self.assertEqual(response_reg.status_code, 200)
        self.assertTrue(response_reg.context.get("plan_exists"))
        # The Rs 0 plan card should display "You have accessed this plan"
        self.assertContains(response_reg, "You have accessed this plan")
        self.assertContains(response_reg, "Go to your plan")
        
        # 6. Check that My Plans page renders successfully
        response_my_plans = self.client.get(reverse("my_plans"))
        self.assertEqual(response_my_plans.status_code, 200)
        self.assertContains(response_my_plans, "My Personal Fitness Blueprint")
        self.assertTrue(response_my_plans.context.get("plan_exists"))
        
        # Show diet only
        response_diet = self.client.get(reverse("my_plans"), {"show": "diet"})
        self.assertEqual(response_diet.status_code, 200)
        self.assertEqual(response_diet.context.get("show"), "diet")
        
        # Show workouts only
        response_workouts = self.client.get(reverse("my_plans"), {"show": "workouts"})
        self.assertEqual(response_workouts.status_code, 200)
        self.assertEqual(response_workouts.context.get("show"), "workouts")

