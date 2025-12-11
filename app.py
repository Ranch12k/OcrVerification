from flask import Flask, request, jsonify
import os
import json
from datetime import datetime

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'

for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER]:
    os.makedirs(folder, exist_ok=True)

@app.route('/', methods=['GET'])
def index():
    """Root endpoint with API info"""
    return jsonify({
        'service': 'OcrVerification API',
        'version': '1.0.0',
        'status': 'running',
        'endpoints': {
            'GET /': 'API information',
            'GET /health': 'Health check',
            'GET /version': 'API version',
            'POST /process': 'Process Aadhaar images (upload front and back)'
        },
        'documentation': 'https://github.com/Ranch12k/OcrVerification'
    }), 200

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'OcrVerification API',
        'timestamp': datetime.now().isoformat()
    }), 200

@app.route('/version', methods=['GET'])
def version():
    """Get API version"""
    return jsonify({
        'version': '1.0.0',
        'service': 'OcrVerification API',
        'timestamp': datetime.now().isoformat()
    }), 200

@app.route('/process', methods=['POST'])
def process_aadhaar():
    """Process uploaded Aadhaar images"""
    try:
        if 'front' not in request.files or 'back' not in request.files:
            return jsonify({'error': 'Missing front or back image'}), 400
        
        front = request.files['front']
        back = request.files['back']
        
        if front.filename == '' or back.filename == '':
            return jsonify({'error': 'Empty filename'}), 400
        
        # Save uploaded files
        front_path = os.path.join(UPLOAD_FOLDER, 'aff.jpg')
        back_path = os.path.join(UPLOAD_FOLDER, 'aadhaarBack.jpg')
        
        front.save(front_path)
        back.save(back_path)
        
        # Import and run main processing
        from main import process_images
        result = process_images(front_path, back_path)
        
        # Save result to outputs folder
        output_file = os.path.join(OUTPUT_FOLDER, f'output_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        return jsonify(result), 200
        
    except ImportError as e:
        return jsonify({'error': f'Import error: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Processing error: {str(e)}'}), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'error': 'Endpoint not found',
        'message': 'Use / to see available endpoints'
    }), 404

@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Server error'}), 500

if __name__ == '__main__':
    print("=" * 50)
    print("OcrVerification API Server")
    print("=" * 50)
    print("Starting Flask server...")
    print("Visit: http://localhost:5000")
    print("=" * 50)
    app.run(debug=False, host='0.0.0.0', port=5000, threaded=True)
