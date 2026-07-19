import os
import json
import logging
from groq import Groq
from django.conf import settings

logger = logging.getLogger(__name__)

# Llama models available on Groq free tier (in priority order)
GROQ_MODELS = [
    "llama-3.3-70b-versatile",   # Most capable, 32K context
    "llama-3.1-8b-instant",      # Fastest, 128K context
    "mixtral-8x7b-32768",        # Good quality, 32K context
]


class GeminiService:
    """
    Fitness plan generation service — now powered by Groq Llama models.
    The class name is kept as GeminiService for backwards compatibility.
    """

    @staticmethod
    def generate_fitness_plan(user_profile, categories):
        """
        Calls Groq API with Llama models to generate a workout and diet plan
        based on the user's physical profile and chosen workout categories.
        """
        api_key = getattr(settings, "GROQ_API_KEY", "") or os.environ.get("GROQ_API_KEY")
        if not api_key:
            logger.warning("GROQ_API_KEY is not set. Using mock data.")
            return GeminiService._generate_mock_plan(user_profile, categories)

        prompt = GeminiService._build_prompt(user_profile, categories)
        client = Groq(api_key=api_key)

        last_error = None
        for model in GROQ_MODELS:
            logger.info(f"Attempting plan generation with Groq model: {model}")
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are an expert fitness coach and nutritionist. "
                                "You ONLY respond with valid JSON. No markdown, no explanation, no code blocks."
                            )
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.7,
                    max_tokens=4096,
                )

                raw_text = response.choices[0].message.content.strip()

                # Strip accidental markdown code block wrappers if any
                if raw_text.startswith("```"):
                    raw_text = raw_text.split("```")[1]
                    if raw_text.startswith("json"):
                        raw_text = raw_text[4:]
                raw_text = raw_text.strip()

                parsed = json.loads(raw_text)
                logger.info(f"Successfully generated fitness plan using model: {model}")
                return parsed

            except json.JSONDecodeError as e:
                logger.error(f"JSON parse error from model '{model}': {e}. Raw: {raw_text[:200]}")
                last_error = str(e)
            except Exception as e:
                error_msg = str(e)
                if "rate_limit" in error_msg.lower() or "429" in error_msg:
                    logger.warning(f"Rate limit hit on model '{model}'. Trying next model...")
                else:
                    logger.error(f"Error calling Groq model '{model}': {e}")
                last_error = error_msg
                continue

        logger.error(f"All Groq model attempts failed. Last error: {last_error}. Using mock data.")
        return GeminiService._generate_mock_plan(user_profile, categories)

    @staticmethod
    def _build_prompt(user_profile, categories):
        formatted_categories = ", ".join(categories)
        goal_lower = user_profile.goal.lower()
        
        # Build strict goal instructions for the LLM
        if "loss" in goal_lower or "cut" in goal_lower:
            diet_instruction = (
                "For Fat Loss: prescribe an Indian diet in calorie deficit (1400-1800 kcal) using budget-friendly, "
                "easily available Indian ingredients with high protein/low carb. E.g. paneer, eggs, sprouts, dals, curd, roti. "
                "Do NOT suggest fancy or expensive ingredients like salmon, avocado, quinoa, berries, asparagus, or chia seeds."
            )
        elif "gain" in goal_lower or "bulk" in goal_lower:
            diet_instruction = (
                "For Weight Gain (Bulking): prescribe a high-calorie surplus Indian diet (2700-3400 kcal) focused on "
                "budget-friendly Indian ingredients. E.g. peanut butter, bananas, whole eggs, oats, milk, rajma, paneer, kala chana, rice, ghee. "
                "Do NOT suggest fancy or expensive ingredients like salmon, avocado, berries, asparagus, quinoa, or chia seeds."
            )
        else:
            diet_instruction = (
                "For Weight Maintenance: prescribe a balanced Indian diet (2000-2400 kcal) with budget-friendly Indian carbs "
                "(rice, wheat chapati), dals, vegetables, dahi, and paneer/chana/lentils/eggs. "
                "Do NOT suggest fancy or costly ingredients like salmon, avocado, asparagus, or berries."
            )

        prompt = f"""Generate a personalized workout and diet plan for this user:
- Name: {user_profile.name}
- Age: {user_profile.age} years
- Weight: {user_profile.weight} kg
- Height: {user_profile.height} cm
- Gender: {user_profile.gender}
- Goal: {user_profile.goal}
- Experience: {user_profile.experience}
- Workout Location: {user_profile.workout_place}

RULES:
1. Only generate plans for these categories: {formatted_categories}
2. For each category, create a 3-day plan with keys "day1", "day2", "day3"
3. Always include "diet_plan"
4. Output ONLY a raw JSON object. No markdown, no backticks, no explanation.
5. Diet Plan Customization Instruction: {diet_instruction} The meals and calories must match the user's focus.
6. You MUST specify the exact consumption time in 24-hr [HH:MM:SS] format directly at the end of each meal description string. E.g., 'breakfast': 'Paneer bhurji with 2 wheat chapatis [08:30:00]'.

JSON FORMAT:
{{"""

        if "weight_training" in categories:
            prompt += """
  "weight_training": {{
    "day1": [{{"exercise": "name", "sets": "3", "reps": "10 reps", "rest": "60s"}}],
    "day2": [{{"exercise": "name", "sets": "3", "reps": "10 reps", "rest": "60s"}}],
    "day3": [{{"exercise": "name", "sets": "3", "reps": "10 reps", "rest": "60s"}}]
  }},"""

        if "cardio" in categories:
            prompt += """
  "cardio": {{
    "day1": [{{"exercise": "name", "duration": "20 mins"}}],
    "day2": [{{"exercise": "name", "duration": "20 mins"}}],
    "day3": [{{"exercise": "name", "duration": "20 mins"}}]
  }},"""

        if "yoga" in categories:
            prompt += """
  "yoga": {{
    "day1": [{{"exercise": "name", "duration": "10 mins"}}],
    "day2": [{{"exercise": "name", "duration": "10 mins"}}],
    "day3": [{{"exercise": "name", "duration": "10 mins"}}]
  }},"""

        prompt += """
  "diet_plan": {{
    "breakfast": "description and exact time in [HH:MM:SS]",
    "lunch": "description and exact time in [HH:MM:SS]",
    "dinner": "description and exact time in [HH:MM:SS]",
    "snacks": "description and exact time in [HH:MM:SS]",
    "daily_calories": "e.g. 2000 kcal",
    "water_intake": "e.g. 3 Liters"
  }}
}}"""
        return prompt

    @staticmethod
    def _generate_mock_plan(user_profile, categories):
        response_data = {}
        if "weight_training" in categories:
            response_data["weight_training"] = {
                "day1": [
                    {"exercise": "Push-Ups", "sets": "3", "reps": "12 reps", "rest": "60s"},
                    {"exercise": "Dumbbell Squats", "sets": "3", "reps": "10 reps", "rest": "90s"},
                    {"exercise": "Dumbbell Rows", "sets": "3", "reps": "10 reps", "rest": "60s"}
                ],
                "day2": [
                    {"exercise": "Pull-Ups", "sets": "3", "reps": "8 reps", "rest": "90s"},
                    {"exercise": "Dumbbell Chest Press", "sets": "3", "reps": "12 reps", "rest": "60s"},
                    {"exercise": "Shoulder Press", "sets": "3", "reps": "10 reps", "rest": "60s"}
                ],
                "day3": [
                    {"exercise": "Plank", "sets": "3", "reps": "45 seconds", "rest": "45s"},
                    {"exercise": "Lunges", "sets": "3", "reps": "12 per leg", "rest": "60s"},
                    {"exercise": "Bicep Curls", "sets": "3", "reps": "12 reps", "rest": "45s"}
                ]
            }
        if "cardio" in categories:
            response_data["cardio"] = {
                "day1": [{"exercise": "Treadmill Run", "duration": "20 mins"}],
                "day2": [{"exercise": "Jump Rope", "duration": "15 mins"}],
                "day3": [{"exercise": "Stationary Cycling", "duration": "25 mins"}]
            }
        if "yoga" in categories:
            response_data["yoga"] = {
                "day1": [{"exercise": "Downward Dog Pose", "duration": "5 mins"}],
                "day2": [{"exercise": "Child's Pose", "duration": "8 mins"}],
                "day3": [{"exercise": "Warrior Pose", "duration": "10 mins"}]
            }

        goal_lower = user_profile.goal.lower()
        if "loss" in goal_lower or "cut" in goal_lower:
            response_data["diet_plan"] = {
                "breakfast": "Sprouted Moong & Kala Chana salad with chopped cucumbers, tomatoes, lemon juice [08:30:00]",
                "lunch": "2 Chapatis (whole wheat roti) with a bowl of Yellow Dal Tadka and a cup of homemade low-fat curd [13:30:00]",
                "dinner": "150g scrambled Paneer Bhurji cooked in minimal oil with 1 Chapati and cucumber salad [20:30:00]",
                "snacks": "A handful of roasted chana (chickpeas) with a cup of sugar-free green tea [17:00:00]",
                "daily_calories": "1600 kcal",
                "water_intake": "3 Liters"
            }
        elif "gain" in goal_lower or "bulk" in goal_lower:
            response_data["diet_plan"] = {
                "breakfast": "Peanut butter banana sandwich (2 slices brown bread, 2 tbsp peanut butter) with a glass of whole milk and 3 boiled eggs [08:00:00]",
                "lunch": "A large plate of Rajma Rice (kidney bean curry with parboiled rice) with a dollop of ghee and side of onion salad [13:30:00]",
                "dinner": "150g Paneer Tikka or soya chunks curry with 3 Butter Rotis and a cup of thick dal [20:30:00]",
                "snacks": "Boiled spice Kala Chana chaat with a glass of fresh buttermilk [17:00:00]",
                "daily_calories": "3000 kcal",
                "water_intake": "3.5 Liters"
            }
        else:
            response_data["diet_plan"] = {
                "breakfast": "Oats Upma or Dalia cooked with milk and a banana [08:30:00]",
                "lunch": "Dal Tadka, Rice, Mix Veg Sabzi (spinach/cauliflower) and a cup of dahi [13:30:00]",
                "dinner": "Paneer Pulao cooked in minimal ghee with a bowl of cucumber raita [20:30:00]",
                "snacks": "2 boiled eggs or a handful of roasted peanuts with tea [17:00:00]",
                "daily_calories": "2200 kcal",
                "water_intake": "3 Liters"
            }

        return response_data
