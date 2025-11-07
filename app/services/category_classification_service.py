# services/processing_detection_service.py
import re
from collections import defaultdict

CATEGORY_CLASSES = [
    "Canned",
    "Dry",
    "Treats"
]

KEYWORDS = {
    "Raw Food": {
        "main": ["raw"],
        "supporting": ["raw food", "raw frozen", "raw patties", "raw nuggets", "uncooked", "minimally processed", "primal raw", "nature's variety instinct raw", "raw meal", "raw recipe", "raw medallions", "frozen raw dog food", "raw blend", "raw coated", "raw bites", "raw infused", "raw bones", "raw mix ins", "raw meat formula", "raw beef blend", "barf diet", "biologically appropriate raw food"]
    },
    "Fresh Food": {
        "main": ["fresh"],
        "supporting": ["fresh food", "gently cooked", "lightly cooked", "refrigerated", "homemade style", "fresh food", "gently cooked", "lightly cooked", "fresh frozen", "fresh meals, human grade meals", "cooked fresh", "fresh pet food", "whole food diet", "fridge-stored", "fresh delivery", "real food for dogs", "refrigerated dog food", "made fresh weekly", "freshly prepared", "gently prepared", "made fresh", "home style dog food", "cooked to order", "fresh from our kitchen"]
    },
    "Dry Food": {
        "main": ["dry"],
        "supporting": ["Kibble", "dry food", "dry kibble", "crunchy bites", "oven baked dry", "extruded", "dry formula", "premium dry", "grain free kibble", "dry food", "kibble", "crunchy bites", "dry dog formula", "dehydrated nuggets", "dry meal", "extuded food", "dry blend", "baked kibble", "shelf stable kibble", "grain free kibble", "complete dry food", "balanced dry food", "oven baked bites", "dry protein blend", "everyday kibble", "traditional kibble", "premium dry dog food", "dry crunch", "vet recommended kibble", "hard dog food", "biscuit style food"]
    },
    "Wet Food": {
        "main": ["wet"],
        "supporting": ["canned", "wet food", "slow cooked in gravy", "shelf stable pouch", "stew like consistency", "gently cooked and sealed", "cooked in the can", "retort pouch", "cooked for safety", "moisture rich food", "wet food", "canned food", "moist food", "stewed", "loaf", "pate", "broth", "gravy", "chunk in gravy", "shredded in broth", "homestyle stew", "meat chunks in jelly", "pouch food", "pull-tab can", "shelf stable wet food", "slow cooked", "canned entrée", "meat loaf style", "toppers in gravy", "wet entree", "classic canned dog food", "wet food", "canned food", "moist food", "pâté", "stew style", "gravy rich", "soft dog food", "tender chunks", "loaf style", "meaty stew", "canned recipe", "hydrated meals", "slow cooked wet food", "premium canned dog food", "savory wet meal", "juicy dog food", "ready to serve wet", "pull tab can", "broth infused", "vet recommended wet food", "wet entree", "complete wet food"]
    }
}

NEGATORS = ["no", "not", "never", "without", "free of", "doesn't", "isn't", "aren't", "non", "un"]

def normalize_text(text: str) -> str:
    if text is None or not text or text == "":
        return ""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def contains_negation(window: str) -> bool:
    return any(neg in window for neg in NEGATORS)

def score_category(text: str):
    scores = defaultdict(int)
    reasons = defaultdict(list)
    
    # Safety check for None or empty text
    if not text:
        return scores, reasons
    
    tokens = text.split()
    
    for category, kw in KEYWORDS.items():
        for k in kw["main"]:
            for match in re.finditer(r"\b" + re.escape(k) + r"\b", text):
                start_idx = len(text[:match.start()].split())
                window = " ".join(tokens[max(0, start_idx-4):start_idx+1])
                if contains_negation(window):
                    scores[category] -= 3
                    reasons[category].append(f"Negated main keyword '{k}'")
                else:
                    scores[category] += 5
                    reasons[category].append(f"Main keyword '{k}'")
        for k in kw["supporting"]:
            for match in re.finditer(r"\b" + re.escape(k) + r"\b", text):
                start_idx = len(text[:match.start()].split())
                window = " ".join(tokens[max(0, start_idx-4):start_idx+1])
                if contains_negation(window):
                    scores[category] -= 1
                    reasons[category].append(f"Negated supporting keyword '{k}'")
                else:
                    scores[category] += 2
                    reasons[category].append(f"Supporting keyword '{k}'")
    return scores, reasons

def select_category(scores, reasons):
    if not scores:
        return None, "No valid category"
    max_score = max(scores.values())
    best = [m for m, s in scores.items() if s == max_score and s > 0]
    if not best:
        return None, "No category scores"
    if len(best) > 1:
        best.sort(key=lambda m: sum("Main keyword" in r for r in reasons[m]), reverse=True)
    return best[0], reasons[best[0]]

def infer_category(page_text: str):
    if page_text is None or not page_text or page_text == "":
        return {
            "category": None
        }
    text = normalize_text(page_text)
    scores, reasons = score_category(text)
    category = select_category(scores, reasons)
    return {
        "category": category
    }
