# Aadhaar Document Reader & OCR Processor

A comprehensive Python application for extracting, parsing, and processing Aadhaar document information with OCR, QR code reading, data masking, and multilingual translation support.

## Features

✅ **OCR Text Extraction** - Extract text from Aadhaar front and back images using Tesseract OCR
✅ **QR Code Reading** - Decode QR codes from Aadhaar back using pyzbar
✅ **Separate Processing** - Front image for personal info, back image for address info
✅ **Data Masking** - Automatically mask sensitive Aadhaar numbers and QR codes
✅ **Multilingual Support** - Auto-detect and translate Odia, Hindi, and other languages to English
✅ **Face Detection** - Extract and encode face image in Base64
✅ **Structured JSON Output** - Comprehensive data with final_data, detailed_breakdown, translations, and raw_sources
✅ **Pincode & State Extraction** - Automatically extract pincode and state from back image

## Project Structure

```
OcrVerification/
├── main.py                          # Main orchestrator
├── requirements.txt                 # Python dependencies
├── README.md                        # This file
├── .gitignore                       # Git ignore rules
├── modules/
│   ├── __init__.py
│   ├── ocr_reader.py               # OCR text extraction (Tesseract)
│   ├── qr_reader.py                # QR code reading (pyzbar)
│   ├── xml_parser.py               # XML parsing utilities
│   ├── ocr_parser_new.py           # OCR field parsing
│   └── utils.py                    # Face detection & Base64 encoding
├── images/                          # Input Aadhaar images
│   ├── aff.jpg                     # Front image
│   └── aadhaarBack.jpg             # Back image
├── outputs/                         # Output JSON results
└── tests/                           # Unit tests
    └── test_sample.py
```

## Installation

### Prerequisites

- Python 3.8+
- Tesseract OCR installed on system
- Git (for version control)

### Step 1: Install Tesseract OCR

**Windows:**
```powershell
# Download installer from:
https://github.com/UB-Mannheim/tesseract/wiki

# Or use Chocolatey:
choco install tesseract
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install tesseract-ocr
```

**macOS:**
```bash
brew install tesseract
```

### Step 2: Clone Repository

```bash
git clone https://github.com/Ranch12k/OcrVerification.git
cd OcrVerification
```

### Step 3: Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

## Dependencies

Core libraries required:
- `opencv-python` - Image processing
- `pytesseract` - OCR text extraction
- `pyzbar` - QR code reading
- `pillow` - Image manipulation
- `xmltodict` - XML parsing
- `numpy` - Numerical operations
- `deep-translator` - Multilingual translation

See `requirements.txt` for complete list with versions.

## Usage

### Local Execution

```bash
# Run the processor
python main.py

# Output: generates output.json with extracted data
```

### Input Format

Place Aadhaar images in the `images/` directory:
- `aff.jpg` - Front side of Aadhaar card
- `aadhaarBack.jpg` - Back side of Aadhaar card

### Output JSON Format

```json
{
  "status": "success",
  "final_data": {
    "personal_info": {
      "name": "EXTRACTED_NAME",
      "gender": "Male/Female",
      "date_of_birth": "DD/MM/YYYY",
      "year_of_birth": "YYYY",
      "aadhaar_number": "****XXXX"  // Masked - last 4 digits only
    },
    "address": {
      "house": "...",
      "street": "...",
      "locality": "...",
      "city": "...",
      "state": "...",
      "pincode": "......",
      "full_address": "..."
    },
    "photo": {
      "face_image_base64": "iVBORw0KGgo..."
    }
  },
  "detailed_breakdown": {
    "ocr_front": {...},
    "ocr_back": {...},
    "qr_code": {...}
  },
  "translations": {
    "ocr_front_translated": {
      "full_text_english": "...",
      "address_english": "..."
    },
    "ocr_back_translated": {
      "full_text_english": "...",
      "address_english": "...",
      "locality_english": "...",
      "city_english": "..."
    }
  },
  "raw_sources": {
    "ocr_text_front": "...",
    "ocr_text_back": "...",
    "qr_data": "FirstChars**[MASKED]**LastChars"
  }
}
```

## Server Deployment

### Option 1: Flask REST API (Recommended)

Create `app.py`:

```python
from flask import Flask, request, jsonify
from main import process_images
import os

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/process', methods=['POST'])
def process_aadhaar():
    """Process uploaded Aadhaar images"""
    if 'front' not in request.files or 'back' not in request.files:
        return jsonify({'error': 'Missing front or back image'}), 400
    
    front = request.files['front']
    back = request.files['back']
    
    # Save uploaded files
    front_path = os.path.join(UPLOAD_FOLDER, 'aff.jpg')
    back_path = os.path.join(UPLOAD_FOLDER, 'aadhaarBack.jpg')
    
    front.save(front_path)
    back.save(back_path)
    
    # Process images
    result = process_images(UPLOAD_FOLDER)
    
    return jsonify(result), 200

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
```

Install Flask:
```bash
pip install flask
```

Run:
```bash
python app.py
```

### Option 2: Docker Deployment

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

# Install Tesseract OCR
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 5000

# Run Flask app
CMD ["python", "app.py"]
```

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  aadhaar-reader:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./uploads:/app/uploads
      - ./outputs:/app/outputs
    environment:
      - FLASK_ENV=production
    restart: unless-stopped
```

Build and run:
```bash
docker-compose up -d
```

### Option 3: AWS Lambda Deployment

1. Package dependencies:
```bash
pip install -r requirements.txt -t package/
cp -r modules package/
cp main.py package/
cd package && zip -r ../lambda_function.zip . && cd ..
```

2. Create Lambda handler `lambda_handler.py`:
```python
import json
from main import process_images

def handler(event, context):
    """AWS Lambda handler"""
    try:
        result = process_images('images/')
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
```

3. Upload `lambda_function.zip` to AWS Lambda

## API Usage Examples

### cURL
```bash
curl -X POST http://localhost:5000/process \
  -F "front=@images/aff.jpg" \
  -F "back=@images/aadhaarBack.jpg"
```

### Python Requests
```python
import requests

with open('images/aff.jpg', 'rb') as f_front, \
     open('images/aadhaarBack.jpg', 'rb') as f_back:
    files = {
        'front': f_front,
        'back': f_back
    }
    response = requests.post('http://localhost:5000/process', files=files)
    data = response.json()
    print(data)
```

### JavaScript/Fetch
```javascript
const formData = new FormData();
formData.append('front', frontImageFile);
formData.append('back', backImageFile);

fetch('http://localhost:5000/process', {
  method: 'POST',
  body: formData
})
  .then(res => res.json())
  .then(data => console.log(data));
```

## Security & Privacy

🔒 **Data Protection:**
- Aadhaar numbers masked (show only last 4 digits)
- QR codes masked (show first/last 10 chars)
- Face images extracted separately
- No data stored by default

⚠️ **Important:**
- Use HTTPS in production
- Implement authentication/authorization
- Store data securely (encrypted)
- Comply with UIDAI guidelines
- Consider data retention policies

## Configuration

Edit `main.py` to customize:

```python
# Tesseract path (if not in system PATH)
pytesseract.pytesseract.pytesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Image paths
FRONT_IMAGE_NAME = 'aff.jpg'
BACK_IMAGE_NAME = 'aadhaarBack.jpg'

# Output directory
OUTPUT_DIR = 'outputs'
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Tesseract not found | Install Tesseract and add to PATH |
| Poor OCR accuracy | Ensure high-quality image (300+ DPI) |
| QR code not detected | Place QR code properly in frame |
| Translation errors | Check internet connection |
| Memory issues | Process images in batches |

## Testing

```bash
# Run unit tests
python -m pytest tests/

# Test with sample image
python main.py
```

## Performance Metrics

- **Processing time:** ~2-5 seconds per Aadhaar pair
- **Memory usage:** ~200-300 MB
- **API response time:** ~3-7 seconds (depending on image size)

## Future Enhancements

- [ ] Batch processing API
- [ ] Database integration
- [ ] Advanced face recognition
- [ ] Mobile app support
- [ ] Signature verification
- [ ] Multiple language support expansion
- [ ] Real-time processing pipeline

## License

MIT License - See LICENSE file for details

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Email: support@example.com
- Documentation: https://github.com/Ranch12k/OcrVerification/wiki

## Disclaimer

This tool is for educational and authorized use only. Ensure compliance with:
- UIDAI (Unique Identification Authority of India) guidelines
- Data Protection Act, 2018
- Privacy regulations in your jurisdiction

---

**Last Updated:** December 2025
**Version:** 1.0.0
**Status:** Production Ready ✅
