import json
import re
from datetime import datetime

from .config import (
    ASSISTANT_ALLOWED_ACTIONS,
    COACH_DIET_MEAL_FOOD_OPTIONS,
    DIET_MEAL_CUSTOMIZATION_MODES,
    COACH_SCOPE_OPTIONS,
    DEFAULT_DIET_MEALS_PER_DAY,
    DEFAULT_GYM_PREFERRED_MINUTES,
    DIET_MEAL_COUNT_OPTIONS,
    DIET_PREFERENCE_OPTIONS,
    GYM_PROFILE_GOALS,
    HEALTH_GENDER_OPTIONS,
)


def _truncate_text(value: str | None, limit: int):
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip() + "..."


def _safe_float(value: str | None):
    if value in {None, ""}:
        return None
    try:
        return round(float(str(value).strip().replace(",", ".")), 2)
    except (TypeError, ValueError):
        return None


def _safe_int(value: str | None, default: int | None = None):
    if value in {None, ""}:
        return default
    try:
        return int(float(str(value).strip().replace(",", ".")))
    except (TypeError, ValueError):
        return default


def _normalize_gender(value: str | None):
    current = str(value or "").strip().lower()
    return current if current in HEALTH_GENDER_OPTIONS else "unspecified"


def _normalize_meals_per_day(value: str | int | None, default: int = DEFAULT_DIET_MEALS_PER_DAY):
    current = _safe_int(str(value), default) if value is not None else default
    if current not in DIET_MEAL_COUNT_OPTIONS:
        return 5 if current and current >= 5 else 3
    return current


def _normalize_date(value: str | None, default: str | None = None):
    current = str(value or "").strip() or str(default or datetime.now().date().isoformat())
    if not re.fullmatch(r"20\d{2}-\d{2}-\d{2}", current):
        return str(default or datetime.now().date().isoformat())
    return current


def _normalize_scope(value: str | None):
    current = str(value or "").strip().lower()
    return current if current in COACH_SCOPE_OPTIONS else None


def _normalize_split_key(value: str | None):
    slug = re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower()).strip("_")
    if slug in {"lower_body", "lower"}:
        return "legs"
    return slug or None


def _normalize_diet_slot_key(value: str | None):
    slug = re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower()).strip("_")
    aliases = {
        "breakfast": "breakfast",
        "morning": "breakfast",
        "lunch": "lunch",
        "dinner": "dinner",
        "snack": "snack",
        "snack_1": "snack",
        "snack_2": "snack",
        "snack_am": "snack",
        "snack_pm": "snack",
    }
    return aliases.get(slug)


def _supported_diet_food_names():
    return [str(item.get("label") or "").strip() for item in COACH_DIET_MEAL_FOOD_OPTIONS if str(item.get("label") or "").strip()]


def _normalize_diet_food_name(value: str | None):
    raw = str(value or "").strip().lower()
    if not raw:
        return None
    normalized = re.sub(r"[^a-z0-9]+", " ", raw).strip()
    normalized_words = {word for word in normalized.split() if word}
    for option in COACH_DIET_MEAL_FOOD_OPTIONS:
        label = str(option.get("label") or "").strip()
        aliases = [label, *(option.get("aliases") or ())]
        for alias in aliases:
            alias_normalized = re.sub(r"[^a-z0-9]+", " ", str(alias or "").strip().lower()).strip()
            alias_words = {word for word in alias_normalized.split() if word}
            if not alias_normalized:
                continue
            if normalized == alias_normalized or (alias_words and alias_words == normalized_words):
                return label
            if len(alias_words) >= 2 and len(normalized_words) >= 2 and (alias_normalized in normalized or normalized in alias_normalized):
                return label
    return None


def _normalize_diet_meal_customization_mode(value: str | None):
    raw = str(value or "").strip().lower()
    if raw in DIET_MEAL_CUSTOMIZATION_MODES:
        return raw
    return None


def _normalize_diet_nutrient_payload(value):
    source = value if isinstance(value, dict) else {}
    normalized = {}
    for nutrient_code in ("protein_g", "carbs_g", "fat_g", "fiber_g"):
        amount = _safe_float(source.get(nutrient_code))
        if amount is None or amount < 0:
            continue
        normalized[nutrient_code] = amount
    return normalized


def _estimate_calories_from_nutrients(nutrients: dict):
    if not nutrients:
        return None
    protein = float(nutrients.get("protein_g") or 0.0)
    carbs = float(nutrients.get("carbs_g") or 0.0)
    fat = float(nutrients.get("fat_g") or 0.0)
    if protein <= 0 and carbs <= 0 and fat <= 0:
        return None
    return round(protein * 4.0 + carbs * 4.0 + fat * 9.0, 1)


def _normalize_diet_meal_items(payload: dict):
    raw_items = payload.get("items") if isinstance(payload.get("items"), list) else None
    if raw_items:
        candidates = raw_items
    else:
        candidates = [payload]
    normalized_items = []
    for raw_item in candidates[:6]:
        if not isinstance(raw_item, dict):
            continue
        raw_food_name = _truncate_text(raw_item.get("food_name"), 120)
        known_food_name = _normalize_diet_food_name(raw_food_name)
        food_name = known_food_name or raw_food_name
        if not food_name:
            continue
        servings = _safe_float(raw_item.get("servings"))
        servings = min(8.0, max(0.25, servings if servings is not None else 1.0))
        serving_text = _truncate_text(raw_item.get("serving_text"), 80)
        nutrients = _normalize_diet_nutrient_payload(raw_item.get("nutrients"))
        calories = _safe_float(raw_item.get("calories"))
        if calories is None:
            calories = _estimate_calories_from_nutrients(nutrients)
        normalized_items.append(
            {
                "food_name": food_name,
                "servings": servings,
                "serving_text": serving_text,
                "calories": calories,
                "nutrients": nutrients,
            }
        )
    return normalized_items


def _format_diet_item_summary(item: dict):
    servings = float(item.get("servings") or 1.0)
    servings_text = f"{int(round(servings))}" if abs(servings - round(servings)) < 0.01 else f"{servings:.1f}".rstrip("0").rstrip(".")
    return f"{servings_text} x {item.get('food_name')}"


def _normalize_diet_preference_keys(value):
    raw_items = value if isinstance(value, list) else [value]
    normalized = []
    for item in raw_items:
        key = re.sub(r"[^a-z0-9]+", "_", str(item or "").strip().lower()).strip("_")
        if key in DIET_PREFERENCE_OPTIONS:
            normalized.append(key)
    if not normalized:
        return []
    if "balanced" in normalized:
        return ["balanced"]
    macro_preferences = [key for key in normalized if key in {"lower_carb", "higher_carb"}]
    if len(macro_preferences) > 1:
        latest_macro = macro_preferences[-1]
        normalized = [key for key in normalized if key not in {"lower_carb", "higher_carb"}]
        normalized.append(latest_macro)
    ordered = []
    seen = set()
    for key in normalized:
        if key in seen:
            continue
        seen.add(key)
        ordered.append(key)
    return ordered


def _measurement_summary(payload: dict):
    parts = []
    labels = {
        "weight_kg": "weight",
        "arm_cm": "arm",
        "chest_cm": "chest",
        "waist_cm": "waist",
        "thigh_cm": "thigh",
        "calf_cm": "calf",
    }
    units = {
        "weight_kg": "kg",
        "arm_cm": "cm",
        "chest_cm": "cm",
        "waist_cm": "cm",
        "thigh_cm": "cm",
        "calf_cm": "cm",
    }
    for key in ("weight_kg", "arm_cm", "chest_cm", "waist_cm", "thigh_cm", "calf_cm"):
        value = payload.get(key)
        if value is None:
            continue
        parts.append(f"{labels[key]} {value:.1f} {units[key]}")
    return ", ".join(parts)


def normalize_assistant_action(raw_action):
    if not isinstance(raw_action, dict):
        return None
    action_type = str(raw_action.get("type") or "").strip().lower()
    if action_type not in ASSISTANT_ALLOWED_ACTIONS:
        return None
    payload = raw_action.get("payload")
    if not isinstance(payload, dict):
        payload = {}
    summary = _truncate_text(raw_action.get("summary"), 180)
    if action_type == "record_weight_checkin":
        weight_kg = _safe_float(payload.get("weight_kg"))
        if weight_kg is None or weight_kg <= 0:
            return None
        measured_on = _normalize_date(payload.get("measured_on"))
        note = _truncate_text(payload.get("note"), 200)
        payload = {
            "weight_kg": weight_kg,
            "measured_on": measured_on,
            "note": note,
        }
        summary = summary or f"Record weight {weight_kg:.1f} kg for {measured_on}."
    elif action_type == "record_health_measurement":
        measured_on = _normalize_date(payload.get("measured_on"))
        note = _truncate_text(payload.get("note"), 200)
        normalized_payload = {
            "measured_on": measured_on,
            "weight_kg": _safe_float(payload.get("weight_kg")),
            "arm_cm": _safe_float(payload.get("arm_cm")),
            "chest_cm": _safe_float(payload.get("chest_cm")),
            "waist_cm": _safe_float(payload.get("waist_cm")),
            "thigh_cm": _safe_float(payload.get("thigh_cm")),
            "calf_cm": _safe_float(payload.get("calf_cm")),
            "note": note,
        }
        if all(normalized_payload[key] is None for key in ("weight_kg", "arm_cm", "chest_cm", "waist_cm", "thigh_cm", "calf_cm")):
            return None
        payload = normalized_payload
        summary = summary or f"Record health check-in for {measured_on}: {_measurement_summary(payload)}."
    elif action_type == "update_height_cm":
        height_cm = _safe_float(payload.get("height_cm"))
        if height_cm is None or height_cm < 100 or height_cm > 260:
            return None
        payload = {"height_cm": height_cm}
        summary = summary or f"Set height to {height_cm:.1f} cm."
    elif action_type == "update_age_years":
        age_years = _safe_float(payload.get("age_years"))
        if age_years is None or age_years < 10 or age_years > 120:
            return None
        payload = {"age_years": round(float(age_years), 1)}
        summary = summary or f"Set age to {payload['age_years']:.0f} years."
    elif action_type == "update_target_weight":
        target_weight_kg = _safe_float(payload.get("target_weight_kg"))
        if target_weight_kg is None or target_weight_kg <= 0 or target_weight_kg > 400:
            return None
        payload = {"target_weight_kg": target_weight_kg}
        summary = summary or f"Set target weight to {target_weight_kg:.1f} kg."
    elif action_type == "update_gender":
        gender = _normalize_gender(payload.get("gender"))
        if gender not in HEALTH_GENDER_OPTIONS:
            return None
        payload = {"gender": gender}
        summary = summary or f"Set gender to {HEALTH_GENDER_OPTIONS[gender]}."
    elif action_type == "update_goal":
        goal = str(payload.get("goal") or "").strip()
        if goal not in GYM_PROFILE_GOALS:
            return None
        payload = {"goal": goal}
        summary = summary or f"Change goal to {GYM_PROFILE_GOALS[goal]}."
    elif action_type == "update_training_days_per_week":
        training_days = _safe_int(payload.get("training_days_per_week"), DEFAULT_DIET_MEALS_PER_DAY) or DEFAULT_DIET_MEALS_PER_DAY
        training_days = max(1, min(7, training_days))
        payload = {"training_days_per_week": training_days}
        summary = summary or f"Set training days per week to {training_days}."
    elif action_type == "update_session_minutes":
        scope = _normalize_scope(payload.get("scope"))
        if scope is None:
            return None
        session_minutes = _safe_int(payload.get("preferred_session_minutes"), DEFAULT_GYM_PREFERRED_MINUTES) or DEFAULT_GYM_PREFERRED_MINUTES
        session_minutes = max(20, min(180, session_minutes))
        effective_date = _normalize_date(payload.get("effective_date")) if scope == "today" else None
        payload = {"scope": scope, "preferred_session_minutes": session_minutes, "effective_date": effective_date}
        summary = summary or f"Set session length to {session_minutes} minutes for {COACH_SCOPE_OPTIONS[scope].lower()}."
    elif action_type == "update_meals_per_day":
        scope = _normalize_scope(payload.get("scope"))
        if scope is None:
            return None
        meals_per_day = _normalize_meals_per_day(payload.get("meals_per_day"), DEFAULT_DIET_MEALS_PER_DAY)
        effective_date = _normalize_date(payload.get("effective_date")) if scope == "today" else None
        payload = {"scope": scope, "meals_per_day": meals_per_day, "effective_date": effective_date}
        summary = summary or f"Set meals per day to {meals_per_day} for {COACH_SCOPE_OPTIONS[scope].lower()}."
    elif action_type == "customize_diet_meal":
        scope = _normalize_scope(payload.get("scope"))
        slot_key = _normalize_diet_slot_key(payload.get("slot_key"))
        mode = _normalize_diet_meal_customization_mode(payload.get("mode")) or "append"
        items = _normalize_diet_meal_items(payload)
        if scope is None or not slot_key or not items:
            return None
        effective_date = _normalize_date(payload.get("effective_date")) if scope == "today" else None
        payload = {
            "scope": scope,
            "slot_key": slot_key,
            "mode": mode,
            "items": items,
            "effective_date": effective_date,
        }
        item_summary = ", ".join(_format_diet_item_summary(item) for item in items[:3])
        verb = "Replace" if mode == "replace" else "Customize"
        summary = summary or (
            f"{verb} {slot_key.replace('_', ' ')} with {item_summary} for {COACH_SCOPE_OPTIONS[scope].lower()}."
        )
    elif action_type == "set_diet_preferences":
        scope = _normalize_scope(payload.get("scope"))
        if scope is None:
            return None
        preference_keys = _normalize_diet_preference_keys(payload.get("preference_keys") or payload.get("preference_key"))
        if not preference_keys:
            return None
        effective_date = _normalize_date(payload.get("effective_date")) if scope == "today" else None
        payload = {
            "scope": scope,
            "preference_keys": preference_keys,
            "effective_date": effective_date,
        }
        label_text = ", ".join(DIET_PREFERENCE_OPTIONS[key] for key in preference_keys)
        summary = summary or f"Use {label_text.lower()} diet preferences for {COACH_SCOPE_OPTIONS[scope].lower()}."
    elif action_type == "set_gym_split":
        scope = _normalize_scope(payload.get("scope"))
        split_key = _normalize_split_key(payload.get("split_key"))
        if scope is None or not split_key:
            return None
        effective_date = _normalize_date(payload.get("effective_date")) if scope == "today" else None
        payload = {"scope": scope, "split_key": split_key, "effective_date": effective_date}
        summary = summary or f"Use the {split_key.replace('_', ' ')} split for {COACH_SCOPE_OPTIONS[scope].lower()}."
    elif action_type == "replace_gym_exercise":
        scope = _normalize_scope(payload.get("scope"))
        split_key = _normalize_split_key(payload.get("split_key"))
        exercise_name = _truncate_text(payload.get("exercise_name"), 120)
        replacement_name = _truncate_text(payload.get("replacement_exercise_name"), 120)
        if scope is None or not split_key or not exercise_name or not replacement_name:
            return None
        effective_date = _normalize_date(payload.get("effective_date")) if scope == "today" else None
        payload = {
            "scope": scope,
            "split_key": split_key,
            "exercise_name": exercise_name,
            "replacement_exercise_name": replacement_name,
            "effective_date": effective_date,
        }
        summary = summary or f"Replace {exercise_name} with {replacement_name} for the {split_key.replace('_', ' ')} split ({COACH_SCOPE_OPTIONS[scope].lower()})."
    elif action_type == "update_gym_exercise_scheme":
        scope = _normalize_scope(payload.get("scope"))
        split_key = _normalize_split_key(payload.get("split_key"))
        exercise_name = _truncate_text(payload.get("exercise_name"), 120)
        sets_text = _truncate_text(payload.get("sets_text"), 32)
        reps_text = _truncate_text(payload.get("reps_text"), 32)
        rest_text = _truncate_text(payload.get("rest_text"), 32)
        if scope is None or not split_key or not exercise_name or not any((sets_text, reps_text, rest_text)):
            return None
        effective_date = _normalize_date(payload.get("effective_date")) if scope == "today" else None
        payload = {
            "scope": scope,
            "split_key": split_key,
            "exercise_name": exercise_name,
            "sets_text": sets_text,
            "reps_text": reps_text,
            "rest_text": rest_text,
            "effective_date": effective_date,
        }
        parts = []
        if sets_text:
            parts.append(f"sets {sets_text}")
        if reps_text:
            parts.append(f"reps {reps_text}")
        if rest_text:
            parts.append(f"rest {rest_text}")
        summary = summary or f"Adjust {exercise_name} in the {split_key.replace('_', ' ')} split: {', '.join(parts)} ({COACH_SCOPE_OPTIONS[scope].lower()})."
    elif action_type == "update_gym_exercise_load":
        scope = _normalize_scope(payload.get("scope"))
        split_key = _normalize_split_key(payload.get("split_key"))
        exercise_name = _truncate_text(payload.get("exercise_name"), 120)
        suggested_weight_kg = _safe_float(payload.get("suggested_weight_kg"))
        if scope is None or not split_key or not exercise_name or suggested_weight_kg is None or suggested_weight_kg < 0:
            return None
        effective_date = _normalize_date(payload.get("effective_date")) if scope == "today" else None
        payload = {
            "scope": scope,
            "split_key": split_key,
            "exercise_name": exercise_name,
            "suggested_weight_kg": suggested_weight_kg,
            "effective_date": effective_date,
        }
        summary = summary or f"Set the suggested load for {exercise_name} to {suggested_weight_kg:.1f} kg in the {split_key.replace('_', ' ')} split ({COACH_SCOPE_OPTIONS[scope].lower()})."
    elif action_type == "refresh_diet_plan":
        plan_date = _normalize_date(payload.get("plan_date"))
        payload = {"plan_date": plan_date}
        summary = summary or f"Refresh the diet plan for {plan_date}."
    return {
        "type": action_type,
        "summary": summary,
        "payload": payload,
    }


def empty_assistant_response():
    return {
        "reply": "I can help with your health, diet, and gym data and ask for confirmation before making changes.",
        "actions": [],
    }


def parse_assistant_response_text(text: str):
    raw = str(text or "").strip()
    if not raw:
        return empty_assistant_response()
    candidate = raw
    match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
    if match:
        candidate = match.group(0)
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        lines = [line.strip() for line in raw.splitlines() if line.strip()]
        return {
            "reply": _truncate_text(lines[0] if lines else empty_assistant_response()["reply"], 900),
            "actions": [],
        }
    reply = _truncate_text(parsed.get("reply"), 900) or empty_assistant_response()["reply"]
    raw_actions = parsed.get("actions") if isinstance(parsed.get("actions"), list) else []
    actions = [item for item in (normalize_assistant_action(action) for action in raw_actions[:4]) if item]
    return {
        "reply": reply,
        "actions": actions,
    }


def build_assistant_prompt(context: dict, user_message: str):
    allowed_actions_json = {
        "record_health_measurement": {
            "payload": {
                "measured_on": "YYYY-MM-DD optional",
                "weight_kg": "optional number",
                "arm_cm": "optional number",
                "chest_cm": "optional number",
                "waist_cm": "optional number",
                "thigh_cm": "optional number",
                "calf_cm": "optional number",
                "note": "optional short string",
            },
        },
        "record_weight_checkin": {
            "payload": {"weight_kg": "number", "measured_on": "YYYY-MM-DD optional", "note": "optional short string"},
        },
        "update_height_cm": {
            "payload": {"height_cm": "number"},
        },
        "update_age_years": {
            "payload": {"age_years": "number 10-120"},
        },
        "update_target_weight": {
            "payload": {"target_weight_kg": "number"},
        },
        "update_gender": {
            "payload": {"gender": list(HEALTH_GENDER_OPTIONS.keys())},
        },
        "update_goal": {
            "payload": {"goal": list(GYM_PROFILE_GOALS.keys())},
        },
        "update_training_days_per_week": {
            "payload": {"training_days_per_week": "integer 1-7"},
        },
        "update_session_minutes": {
            "payload": {
                "scope": list(COACH_SCOPE_OPTIONS.keys()),
                "preferred_session_minutes": "integer 20-180",
                "effective_date": "YYYY-MM-DD optional when scope=today",
            },
        },
        "update_meals_per_day": {
            "payload": {
                "scope": list(COACH_SCOPE_OPTIONS.keys()),
                "meals_per_day": list(DIET_MEAL_COUNT_OPTIONS),
                "effective_date": "YYYY-MM-DD optional when scope=today",
            },
        },
        "customize_diet_meal": {
            "payload": {
                "scope": list(COACH_SCOPE_OPTIONS.keys()),
                "slot_key": ["breakfast", "lunch", "dinner", "snack"],
                "mode": list(DIET_MEAL_CUSTOMIZATION_MODES.keys()),
                "items": [
                    {
                        "food_name": "any specific food name",
                        "servings": "optional number like 1, 2, or 3",
                        "serving_text": "optional text for one serving when the food is new, for example 1 egg white",
                        "calories": "optional calories for one serving when the food is new",
                        "nutrients": {
                            "protein_g": "optional grams per serving",
                            "carbs_g": "optional grams per serving",
                            "fat_g": "optional grams per serving",
                            "fiber_g": "optional grams per serving",
                        },
                    }
                ],
                "effective_date": "YYYY-MM-DD optional when scope=today",
            },
        },
        "set_diet_preferences": {
            "payload": {
                "scope": list(COACH_SCOPE_OPTIONS.keys()),
                "preference_keys": list(DIET_PREFERENCE_OPTIONS.keys()),
                "effective_date": "YYYY-MM-DD optional when scope=today",
            },
        },
        "set_gym_split": {
            "payload": {
                "scope": list(COACH_SCOPE_OPTIONS.keys()),
                "split_key": "string like push, pull, legs, full_body",
                "effective_date": "YYYY-MM-DD optional when scope=today",
            },
        },
        "replace_gym_exercise": {
            "payload": {
                "scope": list(COACH_SCOPE_OPTIONS.keys()),
                "split_key": "string like push, pull, legs, full_body",
                "exercise_name": "current exercise name",
                "replacement_exercise_name": "new exercise name",
                "effective_date": "YYYY-MM-DD optional when scope=today",
            },
        },
        "update_gym_exercise_scheme": {
            "payload": {
                "scope": list(COACH_SCOPE_OPTIONS.keys()),
                "split_key": "string like push, pull, legs, full_body",
                "exercise_name": "current exercise name",
                "sets_text": "optional short string",
                "reps_text": "optional short string",
                "rest_text": "optional short string",
                "effective_date": "YYYY-MM-DD optional when scope=today",
            },
        },
        "update_gym_exercise_load": {
            "payload": {
                "scope": list(COACH_SCOPE_OPTIONS.keys()),
                "split_key": "string like push, pull, legs, full_body",
                "exercise_name": "current exercise name",
                "suggested_weight_kg": "number >= 0",
                "effective_date": "YYYY-MM-DD optional when scope=today",
            },
        },
        "refresh_diet_plan": {
            "payload": {"plan_date": "YYYY-MM-DD optional"},
        },
    }
    return (
        "You are Control Deck Coach, a personal assistant inside a private dashboard.\n"
        "You can read the supplied personal health, gym, and diet data and answer the user's request.\n"
        "You may also receive attached file metadata, extracted text, and structured meal-photo analysis inside the supplied JSON context. Use that context when it is relevant.\n"
        "You must never suggest changing project code, infrastructure, Docker services, or server settings.\n"
        "You have no tools besides the supplied JSON context. You cannot edit code, inspect repositories, or manage servers.\n"
        "Do not say that you cannot change the dashboard directly. You can propose supported health, diet, and gym changes, and confirmed changes apply immediately in the dashboard.\n"
        "If the user asks to update data, return a proposed action instead of assuming it is already approved.\n"
        "If the request would change a plan and scope matters, ask one short follow-up when the user did not say whether it is for today only or the regular plan. In that case, return actions as an empty array.\n"
        "Use append-only measurements for body data like weight, waist, chest, thigh, calf, and arm. Do not overwrite measurement history.\n"
        "Use long_term scope for regular ongoing plan changes. Use today scope for one-day meal or workout adjustments.\n"
        "When the user only clarifies scope after a follow-up, use recent_chat to infer the pending request and then propose the concrete action.\n"
        "Use customize_diet_meal for a specific meal content request like adding boiled egg to breakfast. A single customize_diet_meal action may contain multiple exact items in payload.items.\n"
        "Use mode=replace when the user asks for a new meal, redesigns a meal, removes the current meal, or wants the meal rebuilt around requested foods. Use mode=append only when the user explicitly wants to add items on top of the current meal.\n"
        "If the requested food is not already in the known food list, you may still use it. In that case include serving_text plus reasonable per-serving calories and nutrient estimates in the item payload so the dashboard can store it and reuse it later.\n"
        "When the user asks for a mix like 2 boiled eggs and 3 egg whites, keep them as separate items in one customize_diet_meal action. Do not collapse them into the closest supported match.\n"
        "When the user asks for a specific meal design, every requested food must appear in payload.items. Do not omit any requested item.\n"
        "If an attached image includes analyzed meal items and the user asks to use that photo as breakfast, lunch, dinner, or a snack, use customize_diet_meal with those analyzed items.\n"
        "If the user wants to replace a meal with the attached photo, use mode=replace. If they want to add the photo meal on top of the current meal, use mode=append.\n"
        "If the attached image analysis is empty or unavailable, explain that clearly instead of inventing foods.\n"
        "Use refresh_diet_plan only when the user wants the whole day or a whole meal plan regenerated, not for a specific food item.\n"
        "Only use these action types, and only when the user's request clearly asks for a change:\n"
        f"{json.dumps(allowed_actions_json, ensure_ascii=True)}\n\n"
        "Return JSON only with keys reply and actions.\n"
        "- reply: short helpful answer in plain text.\n"
        "- actions: array of zero or more action objects with keys type, summary, payload.\n"
        "- never include markdown fences.\n"
        "- if you ask a clarification question, actions must be [].\n"
        "- if the user asks something outside health/diet/gym data management, politely refuse.\n\n"
        f"Dashboard context JSON:\n{json.dumps(context, ensure_ascii=True)}\n\n"
        f"User message:\n{_truncate_text(user_message, 1200)}"
    )
