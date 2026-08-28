from __future__ import annotations

from itertools import product
from typing import Any

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

STANDARD_DRINK_GRAMS = 14.0
METABOLISM_RATE = 0.015
MEAL_REDUCTIONS = {
    "none": 0.0,
    "light": 0.10,
    "regular": 0.22,
    "heavy": 0.33,
}
TIMING_MULTIPLIERS = {
    "while_drinking": 1.00,
    "under_1_hour": 0.95,
    "one_to_two_hours": 0.80,
    "two_to_three_hours": 0.55,
    "over_3_hours": 0.25,
}
DRINK_LABELS = {
    "beer": "beer",
    "vodka_gin": "vodka/gin shot",
    "tequila": "tequila shot",
    "whisky": "whisky shot",
    "wine": "wine/champagne glass",
    "cocktails": "cocktail",
}
COCKTAILS = {
    "vodka_soda": ("Vodka soda", 1.0),
    "gin_tonic": ("Gin and tonic", 1.0),
    "rum_cola": ("Rum and cola", 1.0),
    "tequila_soda": ("Tequila soda", 1.0),
    "margarita": ("Margarita", 1.5),
    "mojito": ("Mojito", 1.5),
    "cosmopolitan": ("Cosmopolitan", 1.5),
    "whiskey_sour": ("Whiskey sour", 1.5),
    "espresso_martini": ("Espresso martini", 1.5),
    "long_island": ("Long Island iced tea", 2.5),
    "negroni": ("Negroni", 2.0),
    "old_fashioned": ("Old fashioned", 1.5),
    "martini": ("Martini", 2.0),
}
TARGET_BANDS = {
    "lower": (0.0, 0.02),
    "medium": (0.02, 0.08),
    "high": (0.08, 0.15),
}


def bad_request(message: str) -> tuple[Any, int]:
    return jsonify({"error": message}), 400


def number(data: dict[str, Any], name: str, minimum: float, maximum: float) -> float:
    try:
        value = float(data[name])
    except (KeyError, TypeError, ValueError):
        raise ValueError(f"{name.replace('_', ' ').capitalize()} must be a number.") from None
    if not minimum <= value <= maximum:
        raise ValueError(
            f"{name.replace('_', ' ').capitalize()} must be between {minimum:g} and {maximum:g}."
        )
    return value


def whole_count(data: dict[str, Any], name: str) -> int:
    try:
        value = int(data.get("drinks", {}).get(name, 0))
    except (TypeError, ValueError):
        raise ValueError(f"{DRINK_LABELS[name].capitalize()} count must be a whole number.") from None
    if isinstance(data.get("drinks", {}).get(name, 0), float) and not data["drinks"][name].is_integer():
        raise ValueError(f"{DRINK_LABELS[name].capitalize()} count must be a whole number.")
    if not 0 <= value <= 20:
        raise ValueError(f"{DRINK_LABELS[name].capitalize()} count must be between 0 and 20.")
    return value


def category_for(bac: float) -> str:
    if bac < 0.02:
        return "Low alcohol level"
    if bac < 0.08:
        return "Tipsy"
    if bac < 0.15:
        return "Drunk"
    return "Very high alcohol level"


def calculate_bac(total_drinks: float, gender: str, weight_kg: float, hours: float, reduction: float) -> dict[str, float]:
    r_value = 0.68 if gender == "male" else 0.55
    initial_bac = ((total_drinks * STANDARD_DRINK_GRAMS) / (weight_kg * 1000 * r_value)) * 100
    unadjusted_bac = max(0.0, initial_bac - (METABOLISM_RATE * hours))
    food_adjusted_bac = max(0.0, unadjusted_bac * (1 - reduction))
    return {
        "unadjusted_bac": unadjusted_bac,
        "food_adjusted_bac": food_adjusted_bac,
        "bac_low": max(0.0, food_adjusted_bac * 0.8),
        "bac_high": food_adjusted_bac * 1.2,
    }


def summary_for(counts: dict[str, int], cocktail_key: str) -> str:
    parts: list[str] = []
    for drink_type, count in counts.items():
        if not count:
            continue
        label = COCKTAILS[cocktail_key][0].lower() if drink_type == "cocktails" else DRINK_LABELS[drink_type]
        plural = label if count == 1 else f"{label}es" if label.endswith("glass") else f"{label}s"
        parts.append(f"{count} {plural}")
    return " + ".join(parts) if parts else "No drinks entered"


def combinations(data: dict[str, Any], gender: str, weight: float, hours: float, reduction: float, cocktail_key: str) -> list[dict[str, Any]]:
    lower, upper = TARGET_BANDS[data["target_band"]]
    servings = {
        "beer": 1.0,
        "vodka_gin": 1.0,
        "tequila": 1.0,
        "whisky": 1.0,
        "wine": 1.0,
        "cocktails": COCKTAILS[cocktail_key][1],
    }
    results: list[dict[str, Any]] = []
    keys = list(servings)
    for values in product(range(6), repeat=len(keys)):
        counts = dict(zip(keys, values))
        alcohol_families = sum(counts[key] > 0 for key in keys if key != "beer")
        if alcohol_families > 1:
            continue
        total = sum(counts[key] * servings[key] for key in keys)
        if total == 0 or total > 6:
            continue
        estimate = calculate_bac(total, gender, weight, hours, reduction)
        bac = estimate["food_adjusted_bac"]
        if bac >= 0.15 or not lower <= bac < upper:
            continue
        results.append({
            "summary": summary_for(counts, cocktail_key),
            "total_standard_drinks": round(total, 1),
            "bac_low": round(estimate["bac_low"], 3),
            "bac_high": round(estimate["bac_high"], 3),
            "estimated_bac": round(bac, 3),
        })
    results.sort(key=lambda item: (item["estimated_bac"], item["total_standard_drinks"], item["summary"]))
    return results[:6]


def calculate(data: dict[str, Any]) -> dict[str, Any]:
    gender = data.get("gender")
    if gender not in {"male", "female"}:
        raise ValueError("Gender must be male or female.")
    weight = number(data, "weight", 30, 250)
    hours = number(data, "duration", 0.25, 24)
    meal_size = data.get("meal_size")
    meal_timing = data.get("meal_timing")
    cocktail_key = data.get("cocktail_type")
    if meal_size not in MEAL_REDUCTIONS or meal_timing not in TIMING_MULTIPLIERS:
        raise ValueError("Choose a valid meal size and meal timing.")
    if cocktail_key not in COCKTAILS:
        raise ValueError("Choose a valid cocktail.")
    if data.get("target_band") not in TARGET_BANDS:
        raise ValueError("Choose a valid target band.")

    counts = {name: whole_count(data, name) for name in DRINK_LABELS}
    total = sum(count for name, count in counts.items() if name != "cocktails")
    total += counts["cocktails"] * COCKTAILS[cocktail_key][1]
    reduction = MEAL_REDUCTIONS[meal_size] * TIMING_MULTIPLIERS[meal_timing]
    estimate = calculate_bac(total, gender, weight, hours, reduction)
    return {
        "total_standard_drinks": round(total, 1),
        "unadjusted_bac": round(estimate["unadjusted_bac"], 3),
        "food_adjusted_bac": round(estimate["food_adjusted_bac"], 3),
        "bac_low": round(estimate["bac_low"], 3),
        "bac_high": round(estimate["bac_high"], 3),
        "food_reduction_percent": round(reduction * 100, 1),
        "category": category_for(estimate["food_adjusted_bac"]),
        "drink_summary": summary_for(counts, cocktail_key),
        "combinations": combinations(data, gender, weight, hours, reduction, cocktail_key),
    }


@app.route("/")
def index() -> str:
    return render_template("index.html", cocktails=COCKTAILS)


@app.post("/calculate")
def calculate_endpoint() -> tuple[Any, int] | Any:
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return bad_request("Send a JSON object with the calculator inputs.")
    try:
        return jsonify(calculate(data))
    except ValueError as error:
        return bad_request(str(error))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
