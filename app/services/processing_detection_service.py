# services/processing_detection_service.py
import re
from collections import defaultdict

PROCESSING_CLASSES = [
    "Uncooked (Not Frozen)",
    "Uncooked (Flash Frozen)",
    "Uncooked (Frozen)",
    "Lightly Cooked (Not Frozen)",
    "Lightly Cooked (Frozen)",
    "Freeze Dried",
    "Air Dried",
    "Dehydrated",
    "Baked",
    "Extruded",
    "Retorted"
]

KEYWORDS = {
    "Extruded": {
        "main": ["extruded"],
        "supporting": ["traditional kibble", "cold pressed kibble", "pellet kibble", "crunchy kibble", "high heat processed", "standard kibble", "oven extruded", "expanded kibble", "steam extruded", "heat extruded", "high temp kibble", "processed kibble", "machine processed kibble", "dry expanded pet food", "typical kibble", "mass produced kibble", "kibble", "dry food", "dry kibble", "crunchy bites", "dry formula", "premium dry", "grain free kibble", "extruded kibble", "high pressure extrusion", "extruded dry food", "puffed kibble", "commercial kibble", "hot extruded", "dry extruded", "standard kibble", "extruded pet food"]
    },
    "Baked": {
        "main": ["baked"],
        "supporting": ["oven baked", "gently baked", "slow baked", "low temp baked", "baked kibble", "oven roasted", "handcrafted baked", "artisan baked", "small batch baked", "baked dry food", "air baked", "dry baked", "baked recipe", "baked formula", "crunchy bites", "dry oven cooked", "lightly baked", "oven baked dog food", "baked in small batches", "slow cooked in oven", "crunchy baked bites"]
    },
    "Freeze Dried": {
        "main": ["freeze dried"],
        "supporting": ["freeze dried nuggets", "primal freeze dried", "primal freeze dried", "freeze dried raw", "freeze dried meal", "freeze dried patties", "freeze dried bites", "freeze dried toppers", "freeze dried formula", "freeze dried dog food", "freeze dried treats", "freeze dried beef", "freeze dried chicken", "freeze dried nuggets for dogs", "freeze dried complete meal", "freeze dried whole food", "raw freeze dried", "shelf stable raw", "raw preserved through freeze drying", "primal nuggets", "freeze dried complete and balanced", "freeze dried blend", "freeze dried entrée", "freeze dried lamb formula", "freeze dried raw diet", "shelf stable freeze dried"]
    },
    "Retorted": {
        "main": ["retorted", "retort pouch", "wet food"],
        "supporting": ["canned food", "high heat sterilized", "shelf stable wet", "thermally processed", "pressure cooked", "canned", "slow cooked in gravy", "shelf stable pouch", "stew like consistency", "gently cooked and sealed", "cooked in the can", "cooked for safety", "moisture rich food", "moist food", "stewed", "loaf", "pate", "broth", "gravy", "chunk in gravy", "shredded in broth", "homestyle stew", "meat chunks in jelly", "pouch food", "pull tab can", "shelf stable wet food", "slow cooked", "canned entrée", "meat loaf style", "toppers in gravy", "wet entree", "classic canned dog food", "retort processed", "canned dog food", "wet food in can", "shelf stable can", "pressure cooked", "heat sterilized", "sealed can", "cooked in can", "moist food in can"]
    },
    "Air Dried": {
        "main": ["air dried"],
        "supporting": ["cold dried", "air dried raw", "gently air dried", "sun dried", "wind dried", "low temperature dried", "gently dried", "slow dried", "cold air dried", "fresh dried", "slow air dried", "air dried nuggets", "air dried bites", "air dried recipes", "low heat dried", "nutrient rich air dried", "air dehydrated", "handcrafted air dried", "natural air dried", "artisan air dried", "air dried food", "air dried patties"]
    },
    "Dehydrated": {
        "main": ["dehydrated"],
        "supporting": ["gently dehydrated", "slow dehydrated", "dried raw", "raw dehydrated", "dehydrated dog food", "dehydrated meals", "dehydrated patties", "dehydrated recipes", "rehydrate with water", "dry mix formula", "add water to serve", "warm water preparation", "shelf stable dehydrated", "dry pre mix", "dehydrated whole foods", "dehydrated base mix"]
    },
    "Lightly Cooked (Frozen)": {
        "main": ["fresh food, lightly cooked, frozen"],
        "supporting": ["frozen lightly cooked", "gently cooked", "gently prepared", "slow cooked", "sous vide", "flash cooked", "lightly steamed", "partially cooked", "gently blanched", "fresh frozen", "frozen fresh", "kept frozen", "ships frozen", "frozen meals", "cooked then frozen", "cooked and frozen", "frozen cooked meals", "frozen gently prepared", "small batch cooked and frozen", "frozen dog entrees", "frozen pet cuisine", "frozen fresh cooked", "cooked frozen food", "frozen homemade meals", "cooked frozen recipes", "slow cooked and frozen", "minimally cooked and frozen"]
    },
    "Lightly Cooked (Not Frozen)": {
        "main": ["fresh food", "lightly cooked", "not frozen"],
        "supporting": ["gently cooked", "gently prepared", "slow cooked", "sous vide", "flash cooked", "lightly steamed", "partially cooked", "gently blanched", "fresh frozen", "frozen fresh", "kept frozen", "ships frozen", "human grade", "usda kitchen", "usda certified", "made in human food facility", "refrigerated", "fresh never frozen", "ready to serve", "fridge fresh", "fridge stored", "delivered fresh", "no freezing", "fresh cooked", "minimally cooked", "small batch cooked", "cooked fresh", "home cooked", "just cooked", "prepared fresh", "cooked meals", "fridge cooked meals", "cooked not frozen", "ready to-serve cooked", "fridge ready meals", "lightly simmered", "cooked and refrigerated", "real cooked food", "cooked daily", "heat prepared meals"]
    },
    "Uncooked (Frozen)": {
        "main": ["raw", "frozen"],
        "supporting": ["deep frozen", "freeze to preserve", "frozen chubs", "frozen dog food", "frozen form", "frozen meals", "frozen nuggets", "frozen packaging", "frozen patties", "frozen raw", "frozen recipe", "kept frozen", "raw frozen", "ships frozen", "store frozen", "human grade raw meals", "uncooked", "not cooked", "frozen raw dog food", "raw kept frozen", "stored frozen", "freeze to preserve", "raw frozen blend", "raw frozen meal", "raw and frozen", "frozen meat mix", "frozen formula", "frozen fresh raw", "stay frozen", "raw in freezer", "freezer stored raw", "frozen raw mix", "raw frozen medallions", "frozen whole prey", "frozen bones and meat"]
    },
    "Uncooked (Flash Frozen)": {
        "main": ["raw", "flash frozen"],
        "supporting": ["raw flash frozen", "instantly frozen", "preserved raw", "rapid frozen", "iqf raw", "flash freeze", "flash frozen raw", "rapidly frozen", "frozen immediately", "preserved by flash freezing", "ultra cold frozen", "raw frozen fast", "instant frozen", "fresh then flash frozen", "flash frozen patties", "flash frozen nuggets", "flash frozen raw blend", "flash frozen formula", "raw quick frozen", "flash frozen meals", "nitrogen frozen", "raw sealed and flash frozen", "raw fast frozen preservation", "raw deep frozen", "flash freeze preserved"]
    }
    ,
    "Uncooked (Not Frozen)": {
        "main": ["raw", "not frozen"],
        "supporting": ["refrigerated", "ready to serve", "fridge fresh", "gently handled", "prepared daily", "fridge stored", "raw and fresh", "delivered fresh", "no freezing", "never frozen", "fresh never frozen", "uncooked", "fridge kept", "stored in fridge", "raw refrigerated", "uncooked and unfrozen", "raw ready to eat", "raw kept cold not frozen", "fresh raw blend", "raw uncooked blend", "raw not frozen formula", "raw not frozen patties", "raw not frozen nuggets", "raw meal no freezing", "cold but not frozen", "raw no freeze preservation", "raw minimal processing", "raw kept in refrigerator"]
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

def score_methods(text: str):
    scores = defaultdict(int)
    reasons = defaultdict(list)
    
    # Safety check for None or empty text
    if not text:
        return scores, reasons
    
    tokens = text.split()
    
    for method, kw in KEYWORDS.items():
        for k in kw["main"]:
            for match in re.finditer(r"\b" + re.escape(k) + r"\b", text):
                start_idx = len(text[:match.start()].split())
                window = " ".join(tokens[max(0, start_idx-4):start_idx+1])
                if contains_negation(window):
                    scores[method] -= 3
                    reasons[method].append(f"Negated main keyword '{k}'")
                else:
                    scores[method] += 5
                    reasons[method].append(f"Main keyword '{k}'")
        for k in kw["supporting"]:
            for match in re.finditer(r"\b" + re.escape(k) + r"\b", text):
                start_idx = len(text[:match.start()].split())
                window = " ".join(tokens[max(0, start_idx-4):start_idx+1])
                if contains_negation(window):
                    scores[method] -= 1
                    reasons[method].append(f"Negated supporting keyword '{k}'")
                else:
                    scores[method] += 2
                    reasons[method].append(f"Supporting keyword '{k}'")
    return scores, reasons

def select_method(scores, reasons):
    if not scores:
        return None, "No scores"
    max_score = max(scores.values())
    best = [m for m, s in scores.items() if s == max_score and s > 0]
    if not best:
        return None, "No valid method"
    if len(best) > 1:
        best.sort(key=lambda m: sum("Main keyword" in r for r in reasons[m]), reverse=True)
    return best[0], reasons[best[0]]

def confidence(score):
    if score >= 7:
        return "high"
    elif score >= 4:
        return "medium"
    else:
        return "low"

def infer_processing_method(page_text: str):
    if page_text is None or not page_text or page_text == "":
        return {
            "method": None,
            "confidence": "low",
            "score": 0,
            "reasons": []
        }
    text = normalize_text(page_text)
    scores, reasons = score_methods(text)
    method, chosen_reasons = select_method(scores, reasons)
    conf = confidence(scores.get(method, 0)) if method else "low"
    return {
        "method": method,
        "confidence": conf,
        "score": scores.get(method, 0),
        "reasons": chosen_reasons
    }
