import re


def parse_ocr_text(text):
    extracted = {}

    lines = [l for l in text.split("\n") if l.strip()]
    extracted["name"] = lines[0].strip() if lines and len(lines[0].strip()) > 3 else None

    dob = re.search(r"(\d{2}/\d{2}/\d{4})", text)
    # Prefer realistic 4-digit years (1900-2025) to avoid picking parts of pincodes
    yob_match = re.search(r"\b(19\d{2}|20\d{2})\b", text)

    extracted["dob"] = dob.group(1) if dob else None
    extracted["yob"] = yob_match.group(1) if yob_match else None

    if "MALE" in text.upper():
        extracted["gender"] = "Male"
    elif "FEMALE" in text.upper():
        extracted["gender"] = "Female"
    else:
        extracted["gender"] = None

    return extracted
