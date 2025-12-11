"""
Improved output formatter for Aadhaar OCR results
Returns cleaner, more readable results in English/Hindi
"""

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
    Format a detailed response with all extracted data
    Includes raw OCR text, parsed data, and translations
    """
    
    formatted = format_aadhaar_result(final_data, translations)
    
    # Add detailed breakdown
    formatted["detailed_breakdown"] = {
        "front_image_ocr": {
            "extracted_fields": clean_dict({
                "aadhaar": ocr_details_front.get('aadhaar'),
                "name": ocr_details_front.get('name'),
                "dob": ocr_details_front.get('dob'),
                "gender": ocr_details_front.get('gender'),
                "address": ocr_details_front.get('address'),
            })
        },
        "back_image_ocr": {
            "extracted_fields": clean_dict({
                "aadhaar": ocr_details_back.get('aadhaar'),
                "name": ocr_details_back.get('name'),
                "address": ocr_details_back.get('address'),
                "city": ocr_details_back.get('city'),
                "pincode": ocr_details_back.get('pincode'),
                "state": ocr_details_back.get('state'),
            })
        },
        "qr_code_data": clean_dict({
            "uid": qr_data.get('uid') if qr_data else None,
            "vid": qr_data.get('vid') if qr_data else None,
        })
    }
    
    return formatted


def clean_dict(d):
    """Remove null, None, and empty string values from dictionary"""
    if not d:
        return {}
    return {k: v for k, v in d.items() if v and str(v).strip() and v != "None"}
