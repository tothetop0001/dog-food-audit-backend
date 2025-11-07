import re

def normalize_text(text: str) -> str:
    if text is None:
        return ""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def select_nutritionally_adequate(text: str) -> str:
    aaa = re.finditer(r"\b" + re.escape("complete and balanced") + r"\b", text)
    bbb = re.finditer(r"\b" + re.escape("complete & balanced") + r"\b", text)
    for match in bbb:
        return "Yes"
    for match in aaa:
        return "Yes"
    return "No"

def infer_nutritionally_adequate(text: str) -> str:
    text = normalize_text(text)
    return select_nutritionally_adequate(text)