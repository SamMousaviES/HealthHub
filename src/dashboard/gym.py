import json


def _safe_float(value: str | None):
    if value in {None, ""}:
        return None
    try:
        return round(float(str(value).strip().replace(",", ".")), 2)
    except (TypeError, ValueError):
        return None


def build_gym_agent_prompt(profile: dict, plan: dict, sessions: list[dict]):
    recent_sessions = [
        {
            "performed_on": item.get("performed_on"),
            "split_label": item.get("split_label"),
            "duration_minutes": item.get("duration_minutes"),
            "body_weight_kg": item.get("body_weight_kg"),
        }
        for item in sessions[:3]
    ]
    exercise_items = []
    for item in plan.get("exercise_rows", []):
        exercise_items.append(
            {
                "exercise_name": item.get("exercise_name"),
                "sets_text": item.get("sets_text"),
                "reps_text": item.get("reps_text"),
                "rest_text": item.get("rest_text"),
                "equipment_type": item.get("equipment_type"),
                "suggested_weight_kg": item.get("suggested_weight_kg"),
                "current_weight_kg": _safe_float(item.get("input_weight_kg")),
                "status": item.get("status"),
                "latest_history": item.get("history_latest_text"),
            }
        )
    payload = {
        "profile": {
            "display_name": profile.get("display_name"),
            "goal": profile.get("goal_label"),
            "gender": profile.get("gender_label"),
            "age_years": profile.get("age_years"),
            "current_weight_kg": profile.get("current_weight_kg"),
            "target_weight_kg": profile.get("desired_weight_kg"),
            "preferred_session_minutes": profile.get("preferred_session_minutes"),
            "training_days_per_week": profile.get("training_days_per_week"),
        },
        "current_session": {
            "title": plan.get("title"),
            "split_key": plan.get("split_key"),
            "performed_on": plan.get("performed_on"),
            "progress_text": plan.get("progress_text"),
            "duration_text": plan.get("duration_text"),
            "rationale": plan.get("rationale", []),
            "override_notes": plan.get("override_notes", []),
            "exercises": exercise_items,
        },
        "recent_sessions": recent_sessions,
    }
    return (
        "You are the Gym AI Coach for a private personal dashboard.\n"
        "Return JSON only with keys headline, bullets, watchout.\n"
        "Rules:\n"
        "- headline: one short sentence\n"
        "- bullets: exactly 3 short strings\n"
        "- watchout: one short sentence\n"
        "- focus on the current session only\n"
        "- be practical about progression, technique focus, and fatigue management\n"
        "- use only the provided data\n"
        "- do not ask questions\n"
        "- do not include markdown fences or extra keys\n\n"
        f"Context JSON:\n{json.dumps(payload, ensure_ascii=True)}"
    )
