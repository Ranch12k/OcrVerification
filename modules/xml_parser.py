import xmltodict


def parse_aadhaar_xml(xml_str):
    """Parse Aadhaar XML (from QR) and return a dict of extracted attributes.

    The Aadhaar QR typically contains a single element like
    `PrintLetterBarcodeData` with attributes (uid, name, gender, yob, dob, etc.).
    This function returns a dict with commonly used keys, or None on failure.
    """
    try:
        parsed = xmltodict.parse(xml_str)
    except Exception:
        return None

    # xmltodict maps attributes with '@' prefix. Find the element containing attributes.
    root = None
    if isinstance(parsed, dict):
        # Usually top-level key is 'PrintLetterBarcodeData'
        for k, v in parsed.items():
            root = v
            break

    if not isinstance(root, dict):
        return None

    # Extract common Aadhaar fields stored as attributes
    result = {}
    result['uid'] = root.get('@uid')
    result['name'] = root.get('@name')
    result['gender'] = root.get('@gender')
    result['yob'] = root.get('@yob')
    result['dob'] = root.get('@dob')
    result['co'] = root.get('@co')
    result['house'] = root.get('@house')
    result['street'] = root.get('@street')
    result['lm'] = root.get('@lm')
    result['loc'] = root.get('@loc')
    result['vtc'] = root.get('@vtc')
    result['po'] = root.get('@po')
    result['dist'] = root.get('@dist')
    result['subdist'] = root.get('@subdist')
    result['state'] = root.get('@state')
    result['pc'] = root.get('@pc')

    return result
