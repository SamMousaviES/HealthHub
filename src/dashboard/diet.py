import json


def build_diet_agent_prompt(profile: dict, plan: dict):
    meal_items = []
    for meal in plan.get("meals", []):
        meal_items.append(
            {
                "slot": meal.get("meal_label"),
                "time_window": meal.get("meal_time_text"),
                "title": meal.get("meal_title"),
                "status": meal.get("status"),
                "item_progress": meal.get("item_summary"),
                "counted_calories": meal.get("consumed_calories"),
                "calories": meal.get("calories"),
                "protein_g": meal.get("protein_g"),
                "carbs_g": meal.get("carbs_g"),
                "fat_g": meal.get("fat_g"),
                "ingredients": meal.get("ingredients", []),
                "items": [
                    {
                        "text": item.get("item_text"),
                        "status": item.get("status"),
                        "calories": item.get("calories"),
                    }
                    for item in meal.get("items", [])
                ],
            }
        )
    payload = {
        "profile": {
            "display_name": profile.get("display_name"),
            "goal": profile.get("goal_label"),
            "gender": profile.get("gender_label"),
            "age_years": profile.get("age_years"),
            "current_weight_kg": profile.get("current_weight_kg"),
            "target_weight_kg": plan.get("desired_weight_kg"),
            "training_days_per_week": profile.get("training_days_per_week"),
            "meals_per_day": profile.get("preferred_meals_per_day"),
        },
        "today_plan": {
            "date": plan.get("plan_date"),
            "target_calories": plan.get("target_calories"),
            "planned_calories": plan.get("total_calories"),
            "consumed_calories": plan.get("progress", {}).get("consumed_calories"),
            "daily_deficit_kcal": plan.get("daily_deficit_kcal"),
            "progress_text": plan.get("progress_text"),
            "active_preferences": plan.get("active_preference_labels", []),
            "override_notes": plan.get("override_notes", []),
            "rationale_text": plan.get("rationale_text"),
            "meals": meal_items,
        },
    }
    return (
        "You are the Diet AI Coach for Health Hub.\n"
        "Return JSON only with keys headline, bullets, watchout.\n"
        "Rules:\n"
        "- headline: one short sentence\n"
        "- bullets: exactly 3 short strings\n"
        "- watchout: one short sentence\n"
        "- stay practical, simple, and meal-prep focused\n"
        "- use only the provided data\n"
        "- do not ask questions\n"
        "- do not include markdown fences or extra keys\n\n"
        f"Context JSON:\n{json.dumps(payload, ensure_ascii=True)}"
    )
