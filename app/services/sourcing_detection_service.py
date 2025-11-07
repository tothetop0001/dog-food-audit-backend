# services/processing_detection_service.py
import re
from collections import defaultdict

SOURCING_CLASSES = [
    "Human Grade (organic)",
    "Human Grade",
    "Feed Grade"
]

KEYWORDS = {
    "Human Grade (organic)": {
        "main": ["organic human grade"],
        "supporting": ["usda organic", "certified organic", "organic meat", "organic vegetables", "organic certified", "human grade organic", "usda organic", "certified organic", "organic meat", "organic vegetables", "organic certified", "human grade organic", "made with organic ingredients", "organic certified facility", "organic produce", "organically sourced", "all organic formula", "non gmo and organic", "organic pet food", "100 organic", "premium organic ingredients", "organic human grade food", "organic superfoods", "clean organic label", "small batch organic", "organic chicken", "organic beef", "organic lamb", "organic turkey", "humanely raised organic", "organic whole foods"]
    },
    "Human Grade": {
        "main": ["human grade"],
        "supporting": ["human grade ingredients", "human quality", "usda inspected", "fit for human consumption", "human edible", "made in human food facility", "made in usda inspected facility", "cooked in human grade kitchens", "made in human food kitchens", "crafted to human food standards", "made in usda kitchen", "inspected for human consumption", "food grade facility", "premium human grade meat", "prepared in human quality facilities", "meets human food safety standards", "small batch human grade", "restaurant quality", "human approved formulas", "made with human edible meat", "real food for dogs", "human grade sourcing", "home cooked quality"]
    },
    "Feed Grade": {
        "main": ["feed grade"],
        "supporting": ["feed quality", "animal feed", "not for human consumption", "rendered meat", "by products", "meat meal", "feed safe", "pet feed", "feed quality", "animal feed", "not for human consumption", "rendered meat", "by products", "meat meal", "pet feed", "feed grade ingredients", "feed use only", "not usda inspected", "4d meat", "meat by product meal", "not human edible", "factory scraps", "feed grade facility", "waste derived protein", "animal digest", "feed standard", "bulk animal feed", "meat and bone meal", "slaughterhouse waste", "unfit for human consumption"]
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

def score_sourcing(text: str):
    scores = defaultdict(int)
    reasons = defaultdict(list)
    
    # Safety check for None or empty text
    if not text:
        return scores, reasons
    
    tokens = text.split()
    
    for sourcing, kw in KEYWORDS.items():
        for k in kw["main"]:
            for match in re.finditer(r"\b" + re.escape(k) + r"\b", text):
                start_idx = len(text[:match.start()].split())
                window = " ".join(tokens[max(0, start_idx-4):start_idx+1])
                if contains_negation(window):
                    scores[sourcing] -= 3
                    reasons[sourcing].append(f"Negated main keyword '{k}'")
                else:
                    scores[sourcing] += 5
                    reasons[sourcing].append(f"Main keyword '{k}'")
        for k in kw["supporting"]:
            for match in re.finditer(r"\b" + re.escape(k) + r"\b", text):
                start_idx = len(text[:match.start()].split())
                window = " ".join(tokens[max(0, start_idx-4):start_idx+1])
                if contains_negation(window):
                    scores[sourcing] -= 1
                    reasons[sourcing].append(f"Negated supporting keyword '{k}'")
                else:
                    scores[sourcing] += 2
                    reasons[sourcing].append(f"Supporting keyword '{k}'")
    return scores, reasons

def select_sourcing(scores, reasons):
    if not scores:
        return None, "No valid sourcing"
    max_score = max(scores.values())
    best = [m for m, s in scores.items() if s == max_score and s > 0]
    if not best:
        return None, "No sourcing scores"
    if len(best) > 1:
        best.sort(key=lambda m: sum("Main keyword" in r for r in reasons[m]), reverse=True)
    return best[0], reasons[best[0]]

def infer_sourcing(page_text: str):
    if page_text is None or not page_text or page_text == "":
        return {
            "sourcing": None
        }
    text = normalize_text(page_text)
    scores, reasons = score_sourcing(text)
    sourcing = select_sourcing(scores, reasons)
    return {
        "sourcing": sourcing
    }
