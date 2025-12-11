import json
import os
from modules.qr_reader import extract_qr_data
from modules.xml_parser import parse_aadhaar_xml
from modules.ocr_reader import extract_text_from_image
from modules.ocr_parser_new import parse_ocr_text
from modules.utils import extract_largest_face_base64

try:
    from deep_translator import GoogleTranslator
    TRANSLATOR_AVAILABLE = True
except:
    TRANSLATOR_AVAILABLE = False


def translate_to_english(text):
    """Translate text to English using Google Translator"""
    if not text or not TRANSLATOR_AVAILABLE:
        return text
    try:
        # Limit text to 5000 chars to avoid API issues
        text_to_translate = text[:5000] if len(text) > 5000 else text
        translator = GoogleTranslator(source='auto', target='en')
        translated = translator.translate(text_to_translate)
        return translated if translated else text
    except Exception as e:
        # Silently fail and return original text
        return text


def mask_aadhaar_number(aadhaar_str):
    """Mask Aadhaar number: show only last 4 digits, rest as ****"""
    if not aadhaar_str or len(aadhaar_str) < 4:
        return "****"
    return "*" * (len(aadhaar_str) - 4) + aadhaar_str[-4:]


def mask_qr_code(qr_str):
    """Mask QR code: show only first 10 and last 10 chars"""
    if not qr_str or len(qr_str) < 20:
        return "*" * len(qr_str) if qr_str else "****"
    return qr_str[:10] + "**[MASKED]**" + qr_str[-10:]


def find_images(folder="images"):
    """Find candidate front/back images in `folder`.

    Front name patterns: startswith af, aff, front
    Back name patterns: startswith ab, back
    Returns tuple (front_path or None, back_path or None)
    """
    if not os.path.isdir(folder):
        return None, None

    files = sorted(os.listdir(folder))
    front = None
    back = None
    for f in files:
        lf = f.lower()
        path = os.path.join(folder, f)
        if not os.path.isfile(path):
            continue
        if front is None and (lf.startswith("af") or lf.startswith("aff") or lf.startswith("front") or "front" in lf):
            front = path
        if back is None and (lf.startswith("ab") or lf.startswith("back") or "back" in lf):
            back = path
    # fallback: if only two images present, take first as front, second as back
    if front is None and back is None and len([x for x in files if os.path.isfile(os.path.join(folder, x))]) >= 2:
        candidates = [os.path.join(folder, x) for x in files if os.path.isfile(os.path.join(folder, x))]
        front, back = candidates[0], candidates[1]

    return front, back


def process_images(front_path, back_path):
    result = {
        "front_image": front_path,
        "back_image": back_path,
        "qr_raw": None,
        "xml_data": None,
        "ocr_text_front": None,
        "ocr_details_front": None,
        "ocr_text_back": None,
        "ocr_details_back": None,
        "face_image_base64": None,
    }

    # Process back image first (QR + address/pincode/state)
    if back_path:
        try:
            qr = extract_qr_data(back_path)
            result["qr_raw"] = qr
        except Exception as e:
            result["qr_raw_error"] = str(e)

        if result.get("qr_raw"):
            try:
                result["xml_data"] = parse_aadhaar_xml(result["qr_raw"])
            except Exception as e:
                result["xml_data_error"] = str(e)

        # Extract address/pincode/state from back image OCR
        try:
            ocr_back = extract_text_from_image(back_path)
            result["ocr_text_back"] = ocr_back
            result["ocr_details_back"] = parse_ocr_text(ocr_back)
        except Exception as e:
            result["ocr_text_back_error"] = str(e)

    # Process front (OCR for name/dob/gender)
    if front_path:
        try:
            ocr_front = extract_text_from_image(front_path)
            result["ocr_text_front"] = ocr_front
        except Exception as e:
            result["ocr_text_front_error"] = str(e)

        if result.get("ocr_text_front"):
            try:
                result["ocr_details_front"] = parse_ocr_text(result["ocr_text_front"])
            except Exception as e:
                result["ocr_details_front_error"] = str(e)

        # Try to extract face image from front photo
        try:
            face_b64 = extract_largest_face_base64(front_path)
            result["face_image_base64"] = face_b64
        except Exception as e:
            result["face_image_error"] = str(e)

    return result


def assemble_final(combined):
    """
    Assemble comprehensive JSON output with all data fields.
    Prefer: QR/XML > Back OCR > Front OCR
    Personal info (name, DOB, gender, aadhaar) from front OCR
    Address info (pincode, state, locality, city) from back OCR
    """
    xml = combined.get('xml_data') or {}
    ocr_front = combined.get('ocr_details_front') or {}
    ocr_back = combined.get('ocr_details_back') or {}

    # ==== QR/XML Fields (Highest Priority) ====
    qr_xml_section = {
        "from_qr": {
            "uid": mask_aadhaar_number(xml.get('uid')) if xml.get('uid') else None,
            "name": xml.get('name'),
            "gender": xml.get('gender'),
            "yob": xml.get('yob'),
            "dob": xml.get('dob'),
        },
        "address_xml": {
            "house": xml.get('house'),
            "street": xml.get('street'),
            "lm": xml.get('lm'),
            "loc": xml.get('loc'),
            "vtc": xml.get('vtc'),
            "po": xml.get('po'),
            "dist": xml.get('dist'),
            "state": xml.get('state'),
            "pc": xml.get('pc'),
        }
    }

    # ==== OCR Front Fields (Personal info) ====
    ocr_front_section = {
        "from_ocr_front": {
            "name": ocr_front.get('name'),
            "gender": ocr_front.get('gender'),
            "yob": ocr_front.get('yob'),
            "dob": ocr_front.get('dob'),
            "aadhaar_number": mask_aadhaar_number(ocr_front.get('aadhaar')),
        },
    }

    # ==== OCR Back Fields (Address info) ====
    ocr_back_section = {
        "from_ocr_back": {
            "full_address": ocr_back.get('address'),
            "locality": ocr_back.get('locality'),
            "city": ocr_back.get('city'),
            "state": ocr_back.get('state'),
            "pincode": ocr_back.get('pincode'),
        }
    }

    # ==== Merged Final Data (Prefer QR → Back OCR → Front OCR) ====
    aadhaar_full = xml.get('uid') or ocr_front.get('aadhaar')
    final_data = {
        "personal_info": {
            "name": xml.get('name') or ocr_front.get('name'),
            "gender": xml.get('gender') or ocr_front.get('gender'),
            "date_of_birth": xml.get('dob') or ocr_front.get('dob'),
            "year_of_birth": xml.get('yob') or ocr_front.get('yob'),
            "dob": xml.get('dob') or ocr_front.get('dob'),
            "yob": xml.get('yob') or ocr_front.get('yob'),
            "aadhaar": aadhaar_full,
            "aadhaar_masked": mask_aadhaar_number(aadhaar_full),
        },
        "address": {
            "house": xml.get('house'),
            "street": xml.get('street'),
            "locality": xml.get('loc') or ocr_back.get('locality'),
            "vtc": xml.get('vtc'),
            "city": xml.get('dist') or ocr_back.get('city'),
            "state": xml.get('state') or ocr_back.get('state'),
            "pincode": xml.get('pc') or ocr_back.get('pincode'),
            "full_address": ocr_back.get('address') or ocr_front.get('address'),
        },
        "qr_and_xml": {
            "uid": xml.get('uid'),
            "vid": xml.get('vid'),
            "qr_raw": combined.get('qr_raw'),
            "qr_raw_masked": mask_qr_code(combined.get('qr_raw')) if combined.get('qr_raw') else None,
        },
        "photo": {
            "face_image_base64": combined.get('face_image_base64'),
        },
    }

    # ==== Raw Data Section ====
    raw_data = {
        "sources": {
            "front_image_path": combined.get('front_image'),
            "back_image_path": combined.get('back_image'),
        },
        "qr_decoding": {
            "qr_raw_string": mask_qr_code(combined.get('qr_raw')) if combined.get('qr_raw') else None,
            "qr_decode_error": combined.get('qr_raw_error'),
        },
        "xml_parsing": {
            "xml_parsed_dict": combined.get('xml_data'),
            "xml_parse_error": combined.get('xml_data_error'),
        },
        "ocr_front": {
            "ocr_raw_text": combined.get('ocr_text_front'),
            "ocr_parsed_dict": combined.get('ocr_details_front'),
            "ocr_extract_error": combined.get('ocr_text_front_error'),
        },
        "ocr_back": {
            "ocr_raw_text": combined.get('ocr_text_back'),
            "ocr_parsed_dict": combined.get('ocr_details_back'),
            "ocr_extract_error": combined.get('ocr_text_back_error'),
        },
        "face_detection": {
            "face_extract_error": combined.get('face_image_error'),
        }
    }

    # Assemble complete output
    final_output = {
        "status": "success" if (xml or ocr_front or ocr_back) else "partial_success",
        "final_data": final_data,
        "detailed_breakdown": {
            "qr_xml_extracted": qr_xml_section,
            "ocr_front_extracted": ocr_front_section,
            "ocr_back_extracted": ocr_back_section,
        },
        "translations": {
            "ocr_front_translated": {
                "full_text_english": translate_to_english(combined.get('ocr_text_front')) if combined.get('ocr_text_front') else None,
                "address_english": translate_to_english(ocr_front.get('address')) if ocr_front.get('address') else None,
            },
            "ocr_back_translated": {
                "full_text_english": translate_to_english(combined.get('ocr_text_back')) if combined.get('ocr_text_back') else None,
                "address_english": translate_to_english(ocr_back.get('address')) if ocr_back.get('address') else None,
                "locality_english": translate_to_english(ocr_back.get('locality')) if ocr_back.get('locality') else None,
                "city_english": translate_to_english(ocr_back.get('city')) if ocr_back.get('city') else None,
            }
        },
        "raw_sources": raw_data,
    }

    return final_output


if __name__ == "__main__":
    front, back = find_images("images")
    combined = process_images(front, back)
    final = assemble_final(combined)
    print(json.dumps(final, ensure_ascii=False, indent=2))
