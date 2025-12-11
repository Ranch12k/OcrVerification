import re
from typing import Optional, Dict
from .india_states_districts import (
    validate_state, validate_district, fuzzy_match_state, 
    fuzzy_match_district, get_all_states
)


def _filter_aadhaar_headers_footers(text: str) -> str:
    """Remove common Aadhaar document headers and footers"""
    # Patterns to ignore/remove
    ignore_patterns = [
        r'Government\s+of\s+India',
        r'Unique\s+Identification\s+Authority',
        r'UIDAI',
        r'My\s+Aadhaar',
        r'Mera\s+Aadhaar',
        r'UIDAI\s+Mobile\s+Number',
        r'@aadhaar',
        r'@india\.gov\.in',
        r'help\.aadhaar@uidai\.net\.in',
        r'uidai\.gov\.in',
        r'www\.uidai\.gov\.in',
        r'Aadhaar\s+Number',
        r'AADHAAR\s+NUMBER',
        r'Logo\s+of\s+Aadhaar',
        r'Issued\s+by\s+UIDAI',
        r'Ministry\s+of\s+Electronics',
        r'Government\s+Logo',
        r'India\s+Government',
    ]
    
    result = text
    for pattern in ignore_patterns:
        result = re.sub(pattern, '', result, flags=re.IGNORECASE)
    
    # Also remove lines that are mostly these patterns
    lines = result.splitlines()
    filtered_lines = []
    for line in lines:
        # Skip lines that are too short and contain only noise
        if len(line.strip()) < 3:
            continue
        # Skip lines with too many @ symbols or dots (usually email/website noise)
        if line.count('@') > 1 or line.count('.') > 3:
            continue
        # Skip lines that are mostly numbers and special chars (usually footer)
        alphanumeric_ratio = sum(1 for c in line if c.isalnum()) / max(1, len(line))
        if alphanumeric_ratio < 0.3:
            continue
        filtered_lines.append(line)
    
    return '\n'.join(filtered_lines)


def _clean_lines(text: str):
    return [l.strip() for l in text.splitlines() if l.strip()]


def _fuzzy_match_state_from_text(text: str) -> Optional[str]:
    """Find valid state name in text using fuzzy matching"""
    all_states = get_all_states()
    for state in all_states:
        if re.search(r"\b" + re.escape(state) + r"\b", text, flags=re.IGNORECASE):
            return state
    # Try fuzzy match on each line
    lines = _clean_lines(text)
    for line in lines:
        matched = fuzzy_match_state(line)
        if matched:
            return matched
    return None


def extract_aadhaar_number(text: str) -> Optional[str]:
    # Match 12 digits with optional spaces
    m = re.search(r"\b(\d{4}\s?\d{4}\s?\d{4})\b", text)
    if m:
        return re.sub(r"\s+", "", m.group(1))
    m2 = re.search(r"\b(\d{12})\b", text)
    if m2:
        return m2.group(1)
    return None


def extract_dob(text: str) -> Optional[str]:
    m = re.search(r"(\d{2}[/-]\d{2}[/-]\d{4})", text)
    if m:
        return m.group(1)
    # fallback: look for year
    m2 = re.search(r"\b(19\d{2}|20\d{2})\b", text)
    if m2:
        return m2.group(1)
    return None


def extract_name(text: str) -> Optional[str]:
    """Extract name - prioritize text BEFORE DOB (front image structure)"""
    cleaned_text = _filter_aadhaar_headers_footers(text)
    lines = _clean_lines(cleaned_text)
    
    # Find DOB position
    dob_idx = None
    for i, l in enumerate(lines):
        if re.search(r"\d{2}[/-]\d{2}[/-]\d{4}", l):
            dob_idx = i
            break
    
    # Strategy 1: Look BEFORE DOB for name (typical front image layout)
    if dob_idx is not None and dob_idx > 0:
        for i in range(dob_idx - 1, -1, -1):
            l = lines[i]
            bad_kw = ('AADHAAR', 'Aadhaar', 'Issued', 'DOB', 'Date', 'VID', 'AUTHORITY',
                     'UIDAI', 'Government', 'india', 'India', 'Registration', 'Authority',
                     'uidai.gov', '@', 'help', 'www', 'Mobile', 'Email', 'Phone', 'Father', 'C/O', 'Care')
            if any(k in l for k in bad_kw):
                continue
            words = [w for w in re.split(r"\s+", l.strip()) if w]
            alpha_words = sum(1 for w in words if re.search(r"[A-Za-z]", w))
            if 1 < len(words) <= 6 and alpha_words >= 1 and sum(c.isdigit() for c in l) <= 1:
                if len(l) <= 60 and sum(c in l for c in ['|', '&', '/', '~']) <= 1:
                    return l.strip()
    
    # Strategy 2: General extraction if DOB not found
    bad_keywords = (
        'AADHAAR', 'Aadhaar', 'Issued', 'DOB', 'Date', 'VID', 'AUTHORITY', 
        'Address', 'UIDAI', 'No', 'Number', 'Government', 'india', 'India',
        'Registration', 'Authority', 'uidai.gov', '@', 'help', 'www',
        'Mobile', 'Email', 'Phone', 'Call', 'SMS', 'Help', 'Support',
        'Ministry', 'Electronics', 'IT', 'Government', 'Logo'
    )
    candidates = []
    for l in lines:
        if any(k in l for k in bad_keywords):
            continue
        if sum(c.isdigit() for c in l) > 3:
            continue
        if len(l) > 60:
            continue
        if sum(c in l for c in ['|', '&', '/', '~', '(', ')', '[', ']']) > 2:
            continue
        if '@' in l or 'http' in l.lower() or '.gov' in l.lower() or '.in' in l.lower():
            continue
        candidates.append(l)

    for l in candidates:
        words = [w for w in re.split(r"\s+", l) if w]
        alpha_words = sum(1 for w in words if re.search(r"[A-Za-z]", w))
        if 1 < len(words) <= 6 and alpha_words >= 1:
            return l

    return candidates[0] if candidates else None


def extract_guardian_name(text: str) -> Optional[str]:
    """Extract guardian/father/parent name from 'C/O:' or 'Care of:' pattern"""
    # Look for C/O, Care of, Father, Parent patterns
    patterns = [
        r"C/O[:\s]+([A-Z][A-Za-z\s\.]+?)(?:,|$)",  # C/O: Name,
        r"CARE\s+OF[:\s]+([A-Z][A-Za-z\s\.]+?)(?:,|$)",  # CARE OF: Name,
        r"F/O[:\s]+([A-Z][A-Za-z\s\.]+?)(?:,|$)",  # F/O: Name,
        r"FATHER[:\s]+([A-Z][A-Za-z\s\.]+?)(?:,|$)",  # FATHER: Name,
    ]
    
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            name = m.group(1).strip()
            # Clean up the name
            if name and len(name) > 2:
                return name
    
    return None


def extract_address_components(text: str) -> Dict[str, Optional[str]]:
    lines = _clean_lines(text)
    result = {"address": None, "locality": None, "city": None, "state": None, "pincode": None}

    # Strategy 1: Look for explicit "Address:" pattern - MOST ACCURATE
    addr_match = re.search(r"Address\s*:?\s*(.+?)(?:$|\n)", text, re.IGNORECASE | re.MULTILINE)
    if addr_match:
        full_addr = addr_match.group(1).strip()
        result['address'] = full_addr
        
        # Extract pincode from address
        pin_m = re.search(r"(\d{6})", full_addr)
        if pin_m:
            result['pincode'] = pin_m.group(1)
        
        # Extract state from address
        state_m = _fuzzy_match_state_from_text(full_addr)
        if state_m:
            result['state'] = state_m
        
        # Extract locality (last part after comma)
        addr_parts = [p.strip() for p in full_addr.split(',')]
        if len(addr_parts) > 1:
            result['locality'] = addr_parts[-1]
        
        return result

    # Strategy 2: Find PIN (6 digits) and build address around it
    pin_idx = None
    for i, l in enumerate(lines):
        m = re.search(r"\b(\d{6})\b", l)
        if m:
            result['pincode'] = m.group(1)
            pin_idx = i
            break

    if pin_idx is not None:
        # take up to 4 lines above the PIN as address
        start = max(0, pin_idx - 4)
        addr_lines = lines[start:pin_idx + 1]
        result['address'] = ', '.join(addr_lines)
        # try to set locality (line just above pin)
        if pin_idx - 1 >= 0:
            result['locality'] = lines[pin_idx - 1]
        # try to detect state by matching known state names
        state_match = _fuzzy_match_state_from_text(text)
        if state_match:
            result['state'] = state_match
        # city: if 'DIST' or 'DIST:' appears
        for l in lines:
            if re.search(r"\bDIST\b|\bDistrict\b|\bDIST:\b", l, flags=re.IGNORECASE):
                # attempt to extract name after DIST or DIST:
                m = re.search(r"DIST[:\s-]*([A-Za-z\s-]+)", l, flags=re.IGNORECASE)
                if m:
                    result['city'] = m.group(1).strip(' ,')
                    break

    else:
        # No PIN found: take first 3 lines as address candidate
        if lines:
            result['address'] = ', '.join(lines[:3])

    return result


def parse_ocr_text(text: str) -> Dict[str, Optional[str]]:
    """Return parsed fields from OCR text: name, dob, yob, gender, aadhaar, address components, guardian name."""
    # First, filter out common headers and footers
    cleaned_text = _filter_aadhaar_headers_footers(text)
    
    extracted = {}
    extracted['name'] = extract_name(cleaned_text)
    extracted['dob'] = extract_dob(cleaned_text)
    extracted['guardian_name'] = extract_guardian_name(cleaned_text)
    yob = None
    if extracted.get('dob') and re.match(r"\d{4}$", extracted['dob']):
        yob = extracted['dob']
    else:
        m = re.search(r"\b(19\d{2}|20\d{2})\b", cleaned_text)
        yob = m.group(1) if m else None
    extracted['yob'] = yob

    gender = None
    if re.search(r"\bMALE\b", cleaned_text, flags=re.IGNORECASE):
        gender = 'Male'
    elif re.search(r"\bFEMALE\b", cleaned_text, flags=re.IGNORECASE):
        gender = 'Female'
    extracted['gender'] = gender

    extracted['aadhaar'] = extract_aadhaar_number(cleaned_text)

    addr = extract_address_components(cleaned_text)
    extracted.update(addr)

    return extracted
