"""
Improved output formatter for Aadhaar OCR results
Returns cleaner, more readable results in English/Hindi
"""

def mask_aadhaar(aadhaar_str):
    """Mask Aadhaar number: show only last 4 digits, rest as ****"""
    if not aadhaar_str or len(aadhaar_str) < 4:
        return "****"
    return "*" * (len(aadhaar_str) - 4) + aadhaar_str[-4:]


def format_aadhaar_result(final_data, translations):
    """
    Format the Aadhaar OCR result into a clean, readable structure
    with separated fields and English translations
    """
    
    # Extract data from final_data
    person_info = final_data.get('personal_info', {})
    address_info = final_data.get('address', {})
    photo_info = final_data.get('photo', {})
    qr_info = final_data.get('qr_and_xml', {})
    
    # Clean function to remove null/empty values
    def clean_dict(d):
        return {k: v for k, v in d.items() if v and v != "None"}
    
    # Format result
    result = {
        "metadata": {
            "status": "success",
            "language": "English/Hindi",
            "processing_type": "Aadhaar OCR with Masking"
        },
        
        "personal_information": clean_dict({
            "aadhaar_number": person_info.get('aadhaar'),
            "aadhaar_number_masked": person_info.get('aadhaar_masked'),
            "name": person_info.get('name'),
            "name_english": translate_field(person_info.get('name')),
            "gender": person_info.get('gender'),
            "date_of_birth": person_info.get('date_of_birth'),
            "date_of_birth_formatted": person_info.get('dob'),
            "year_of_birth": person_info.get('year_of_birth'),
        }),
        
        "address_details": clean_dict({
            "full_address": address_info.get('full_address'),
            "full_address_english": translate_field(address_info.get('full_address')),
            "street": address_info.get('street'),
            "street_english": translate_field(address_info.get('street')),
            "locality": address_info.get('locality'),
            "locality_english": translate_field(address_info.get('locality')),
            "village_town_city": address_info.get('vtc'),
            "vtc_english": translate_field(address_info.get('vtc')),
            "city": address_info.get('city'),
            "city_english": translate_field(address_info.get('city')),
            "state": address_info.get('state'),
            "state_english": translate_field(address_info.get('state')),
            "pincode": address_info.get('pincode'),
        }),
        
        "qr_data": clean_dict({
            "uid": qr_info.get('uid'),
            "vid": qr_info.get('vid'),
            "qr_raw_masked": qr_info.get('qr_raw_masked'),
            "qr_status": "Present" if qr_info.get('qr_raw') else "Not Found",
        }),
        
        "document_images": {
            "front_image_available": bool(photo_info.get('face_image_base64')),
            "face_image_base64": photo_info.get('face_image_base64')[:100] + "..." if photo_info.get('face_image_base64') else None,
        },
        
        "summary": {
            "message": "Aadhaar data extracted successfully with automatic masking of sensitive information",
            "fields_extracted": count_non_empty(person_info) + count_non_empty(address_info),
            "confidence": "High" if person_info.get('aadhaar') else "Medium"
        }
    }
    
    return result


def count_non_empty(d):
    """Count non-empty fields in a dictionary"""
    return len([v for v in d.values() if v and v != "None"])


def translate_field(text):
    """
    Translate a single field to English
    Uses the translation module if available
    """
    if not text:
        return None
    
    try:
        from deep_translator import GoogleTranslator
        translator = GoogleTranslator(source='auto', target='en')
        translated = translator.translate(text[:500])  # Limit to 500 chars
        return translated if translated != text else text
    except:
        return text


def format_error_response(error_message):
    """Format error response"""
    return {
        "status": "error",
        "message": error_message,
        "language": "English"
    }


def format_detailed_response(final_data, translations, ocr_details_front, ocr_details_back, qr_data):
    """
    Format JSON response with 2 sections:
    1. FRONT IMAGE - Name, DOB, Gender, Aadhaar
    2. BACK IMAGE - Aadhaar, Address, Pincode, State
    3. DATA_SOURCE - Where each field was extracted from
    """
    
    # Map fields to their source
    data_source_map = {
        # Front image fields
        "name": "Front image - extracted before DOB line",
        "gender": "Front image - near DOB area (English or Hindi)",
        "date_of_birth": "Front image - DOB pattern matching",
        "year_of_birth": "Front image - year extraction from DOB",
        "aadhaar_front": "Front image - 12-digit pattern",
        
        # Back image fields  
        "guardian_name": "Back image - C/O: or Father: pattern",
        "aadhaar_back": "Back image - 12-digit pattern",
        "full_address": "Back image - 'Address:' label or PIN-based extraction",
        "locality": "Back image - line above PIN code",
        "city": "Back image - DIST: or District: pattern",
        "state": "Back image - state name matching from address",
        "pincode": "Back image - 6-digit PIN code pattern",
        
        # QR code fields
        "uid": "QR Code - 2D barcode decoding",
        "vid": "QR Code - 2D barcode decoding",
    }
    
    formatted = {
        "status": "success",
        "message": "Aadhaar data extracted successfully",
        
        # ===== SECTION 1: FRONT IMAGE =====
        "front_image": {
            "section": "Front Side",
            "data": clean_dict({
                "name": ocr_details_front.get('name'),
                "name_english": translate_field(ocr_details_front.get('name')),
                "gender": ocr_details_front.get('gender'),
                "date_of_birth": ocr_details_front.get('dob'),
                "year_of_birth": ocr_details_front.get('yob'),
                "aadhaar_number": ocr_details_front.get('aadhaar'),
                "aadhaar_number_masked": mask_aadhaar(ocr_details_front.get('aadhaar')),
            })
        },
        
        # ===== SECTION 2: BACK IMAGE =====
        "back_image": {
            "section": "Back Side",
            "data": clean_dict({
                "guardian_name": ocr_details_back.get('guardian_name'),
                "guardian_name_english": translate_field(ocr_details_back.get('guardian_name')),
                "aadhaar_number": ocr_details_back.get('aadhaar'),
                "aadhaar_number_masked": mask_aadhaar(ocr_details_back.get('aadhaar')),
                "full_address": ocr_details_back.get('address'),
                "full_address_english": translate_field(ocr_details_back.get('address')),
                "locality": ocr_details_back.get('locality'),
                "locality_english": translate_field(ocr_details_back.get('locality')),
                "city": ocr_details_back.get('city'),
                "city_english": translate_field(ocr_details_back.get('city')),
                "state": ocr_details_back.get('state'),
                "state_english": translate_field(ocr_details_back.get('state')),
                "pincode": ocr_details_back.get('pincode'),
            })
        },
        
        # ===== SECTION 3: QR CODE DATA (Optional) =====
        "qr_code": clean_dict({
            "uid": qr_data.get('uid') if qr_data else None,
            "vid": qr_data.get('vid') if qr_data else None,
        }) if qr_data else None,
        
        # ===== SECTION 4: DATA SOURCE TRACKING =====
        "data_source": {
            "front_image": {
                "name": data_source_map.get("name") if ocr_details_front.get('name') else None,
                "gender": data_source_map.get("gender") if ocr_details_front.get('gender') else None,
                "date_of_birth": data_source_map.get("date_of_birth") if ocr_details_front.get('dob') else None,
                "year_of_birth": data_source_map.get("year_of_birth") if ocr_details_front.get('yob') else None,
                "aadhaar_number": data_source_map.get("aadhaar_front") if ocr_details_front.get('aadhaar') else None,
            },
            "back_image": {
                "guardian_name": data_source_map.get("guardian_name") if ocr_details_back.get('guardian_name') else None,
                "aadhaar_number": data_source_map.get("aadhaar_back") if ocr_details_back.get('aadhaar') else None,
                "full_address": data_source_map.get("full_address") if ocr_details_back.get('address') else None,
                "locality": data_source_map.get("locality") if ocr_details_back.get('locality') else None,
                "city": data_source_map.get("city") if ocr_details_back.get('city') else None,
                "state": data_source_map.get("state") if ocr_details_back.get('state') else None,
                "pincode": data_source_map.get("pincode") if ocr_details_back.get('pincode') else None,
            },
            "qr_code": {
                "uid": data_source_map.get("uid") if qr_data and qr_data.get('uid') else None,
                "vid": data_source_map.get("vid") if qr_data and qr_data.get('vid') else None,
            } if qr_data else None
        },
        
        "summary": {
            "total_fields_extracted": count_non_empty(ocr_details_front) + count_non_empty(ocr_details_back),
            "front_fields": count_non_empty(ocr_details_front),
            "back_fields": count_non_empty(ocr_details_back),
            "confidence": "High" if ocr_details_front.get('name') else "Medium"
        }
    }
    
    return formatted


def clean_dict(d):
    """Remove null, None, and empty string values from dictionary"""
    if not d:
        return {}
    return {k: v for k, v in d.items() if v and str(v).strip() and v != "None"}
