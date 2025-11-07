# app/services/ingredient_classification_service.py

from typing import List, Dict

# -------------------------------
# Keyword Dictionaries
# -------------------------------

MACRO_KEYWORDS = {
    "protein": {
        "high": ["chicken meal", "turkey meal", "salmon", "lamb meal"],
        "good": ["egg", "duck", "chicken"],
        "moderate": ["meat meal"],
        "low": ["by-product meal", "poultry by-product"]
    },
    "fat": {
        "high": ["chicken fat", "fish oil", "flaxseed oil"],
        "good": ["vegetable oil", "canola oil"],
        "low": ["animal fat", "tallow"]
    },
    "carbohydrate": {
        "high": ["pumpkin", "sweet potato", "brown rice"],
        "good": ["oatmeal", "barley"],
        "moderate": ["rice", "potato"],
        "low": ["corn gluten meal", "wheat", "soybean meal", "corn"]
    },
    "fiber": {
        "high": ["apple fiber", "beet pulp", "pumpkin fiber"],
        "good": ["cellulose"],
        "moderate": ["pea fiber"],
        "low": ["wheat bran"]
    }
}

MACRO_PRIORITY = ["protein", "fat", "fiber", "carbohydrate"]

QUALITY_RANK = {"High": 4, "Good": 3, "Moderate": 2, "Low": 1, "Unknown": 0}


# -------------------------------
# Ingredient Classifier
# -------------------------------

def normalize_text(text: str) -> str:
    return text.lower().strip()

def find_macro_and_quality(ingredient: str):
    """Return (macro, quality) if matched."""
    ing = normalize_text(ingredient)
    for macro in MACRO_PRIORITY:
        for tier, keywords in MACRO_KEYWORDS[macro].items():
            for kw in keywords:
                if kw in ing:
                    return macro, tier.capitalize()
    return None, None


def classify_ingredient_list(ingredients: List[str]) -> List[Dict]:
    macro_best_quality = {"protein": "Unknown", "fat": "Unknown", "fiber": "Unknown", "carbohydrate": "Unknown"}

    for ing in ingredients:
        macro, quality = find_macro_and_quality(ing)
        if macro:
            # If this macro already has a quality, compare and keep the best one
            current_best = macro_best_quality.get(macro, "Unknown")
            if QUALITY_RANK[quality] > QUALITY_RANK[current_best]:
                macro_best_quality[macro] = quality

    return macro_best_quality
