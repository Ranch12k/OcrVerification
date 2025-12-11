# Quick Reference: India States & Districts Database

## Installation & Usage

### Basic Usage

```python
# Import functions
from modules.india_states_districts import (
    validate_state,
    validate_district,
    fuzzy_match_state,
    fuzzy_match_district,
    get_all_states,
    get_districts_for_state
)

# Validate exact state/district
if validate_state('Odisha'):
    print("Valid state!")

if validate_district('Balasore', 'Odisha'):
    print("Valid district in Odisha!")

# Fuzzy matching (handles case variations, OCR typos)
matched_state = fuzzy_match_state('ODISHA')  # Returns: 'Odisha'
matched_state = fuzzy_match_state('maharashtra')  # Returns: 'Maharashtra'

state, district = fuzzy_match_district('BALASORE', 'Odisha')
# Returns: ('Odisha', 'Balasore')

# Get all districts for a state
districts = get_districts_for_state('Odisha')
# Returns: ['Angul', 'Balangir', 'Balasore', ...]

# Get all states
all_states = get_all_states()
# Returns: ['Andhra Pradesh', 'Arunachal Pradesh', ...]
```

## Integration with Aadhaar OCR

The parser automatically validates extracted state/district against the database:

```python
from modules.ocr_parser_new import parse_ocr_text

ocr_text = "BALASORE, ODISHA 756111"
result = parse_ocr_text(ocr_text)

# result contains:
# {
#   'state': 'Odisha',        # Validated
#   'city': None,              # Extracted
#   'pincode': '756111',       # Extracted
#   'guardian_name': '...'     # Extracted if C/O: present
# }
```

## Common States & Districts

### Odisha (30 districts)
Angul, Balangir, **Balasore**, Bargarh, Boudh, Cuttack, Debagarh, Dhenkanal, Gajapati, Ganjam, Jagatsinghpur, Jajpur, Jharsuguda, Kalahandi, Kandhamal, Kendrapara, Kendujhar, Khordha, Koraput, Malkangiri, **Mayurbhanj**, Nabarangpur, Nayagarh, Nuapada, **Puri**, Rayagada, Sambalpur, Sankhara, Subarnapur, Sundergarh

### West Bengal (23 districts)
Alipurduar, Bankura, Birbhum, Cooch Behar, Dakshin Dinajpur, Darjeeling, Hooghly, Howrah, Jalpaiguri, Jhargram, Kalimpong, **Kolkata**, Malda, Murshidabad, Nadia, North 24 Parganas, Paschim Bardhaman, Paschim Medinipur, Purba Bardhaman, Purba Medinipur, Purulia, South 24 Parganas, Uttar Dinajpur

### Maharashtra (36 districts)
Ahmednagar, Akola, Amravati, Aurangabad, Beed, Bhandara, Buldhana, Chandrapur, Dhule, Gadchiroli, Gondia, Hingoli, Jalgaon, Jalna, Kolhapur, Latur, Mumbai City, Mumbai Suburban, Nagpur, Nanded, Nandurbar, Nashik, Osmanabad, Palghar, Parbhani, Pune, Raigad, Ratnagiri, Sangli, Satara, Sindhudurg, Solapur, Thane, Wardha, Washim, Yavatmal

### Uttar Pradesh (75 districts)
Agra, Aligarh, Ambedkar Nagar, Amethi, Amroha, Auraiya, Ayodhya, Azamgarh, Baghpat, Bahraich, Ballia, Balrampur, Banda, Barabanki, Bareilly, Basti, Bhadohi, Bijnor, Budaun, Bulandshahr, Chandauli, Chitrakoot, Deoria, Etah, Etawah, Farrukhabad, Fatehpur, Firozabad, Gautam Buddha Nagar, Ghaziabad, Ghazipur, Gonda, Gorakhpur, Hamirpur, Hapur, Hardoi, Hathras, Jalaun, Jaunpur, Jhansi, Kannauj, Kanpur Dehat, Kanpur Nagar, Kasganj, Kaushambi, Kheri, Kushinagar, Lalitpur, Lucknow, Maharajganj, Mahoba, Mainpuri, Mathura, Mau, Meerut, Mirzapur, Moradabad, Muzaffarnagar, Pilibhit, Pratapgarh, Prayagraj, Raebareli, Rampur, Saharanpur, Sambhal, Sant Kabir Nagar, Shahjahanpur, Shamli, Shravasti, Siddharthnagar, Sitapur, Sonbhadra, Sultanpur, Unnao, Varanasi

## API Response Example

```json
{
  "status": "success",
  "front_image": {
    "section": "Front Side",
    "data": {
      "name": "HERIE ARE",
      "gender": "Male",
      "dob": "09/01/2014",
      "yob": "2014",
      "aadhaar": "613596880906",
      "aadhaar_masked": "****0906"
    }
  },
  "back_image": {
    "section": "Back Side",
    "data": {
      "guardian_name": "Sadhu Sing",
      "aadhaar": "303903700828",
      "address": "SANAMAITAPUR, BALASORE, ODISHA 756111",
      "pincode": "756111",
      "state": "Odisha",
      "city": "BALASORE",
      "locality": "SANAMAITAPUR"
    }
  },
  "qr_code": {
    "uid": "...",
    "vid": "..."
  },
  "summary": {
    "total_fields_extracted": 15,
    "confidence": "0.92"
  }
}
```

## Error Handling

```python
from modules.india_states_districts import fuzzy_match_state

# Invalid state
result = fuzzy_match_state('InvalidState')
if result is None:
    print("State not found in database")

# Valid state variations
fuzzy_match_state('TELANGANA')  # Returns: 'Telangana'
fuzzy_match_state('telangana')  # Returns: 'Telangana'
fuzzy_match_state('TEL')        # Returns: 'Telangana'
```

## Performance Tips

1. **Cache results**: If validating many states/districts in a loop, cache the results
2. **Batch validation**: Use `get_all_states()` once at startup instead of multiple calls
3. **Fuzzy matching**: Only use fuzzy matching for OCR output, not for database queries

## Testing the Database

```bash
# Test state validation
python -c "from modules.india_states_districts import validate_state; print(validate_state('Odisha'))"

# Test district validation  
python -c "from modules.india_states_districts import validate_district; print(validate_district('Balasore', 'Odisha'))"

# Test fuzzy matching
python -c "from modules.india_states_districts import fuzzy_match_state; print(fuzzy_match_state('ODISHA'))"
```

## Support & Reference

**Database Version**: 1.0  
**Total Coverage**: 29 States + 719+ Districts  
**Last Updated**: December 11, 2025  
**File**: `modules/india_states_districts.py`

For complete documentation, see `STATES_DISTRICTS_DATABASE.md`
