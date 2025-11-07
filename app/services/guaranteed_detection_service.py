import json
import re

def normalize_text(text: str) -> str:
    if text is None:
        return ""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def select_guaranteed_analysis(text: str) -> str:
    return re.findall(r"(Protein|Fat|Fiber|Moisture|Ash).*?(\d+\.?\d*)%", text)

def infer_guaranteed_analysis(text: str) -> str:
    # text = normalize_text(json.dumps(text))
    matches = select_guaranteed_analysis(text)

    ga_dict = {}
    for nutrient, value in matches:
        ga_dict[nutrient.lower()] = f"{value}"

    return ga_dict
    # return "aaa"