from flask import Flask, request, jsonify, send_from_directory
import os
import json
from datetime import datetime

app = Flask(__name__, static_folder='.', static_url_path='')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'

for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER]:
    os.makedirs(folder, exist_ok=True)

@app.route('/', methods=['GET'])
def index():
    """Serve HTML form or API info based on Accept header"""
    # Check if browser is requesting HTML
    accept_header = request.headers.get('Accept', '')
    if 'text/html' in accept_header or not accept_header:
        try:
            return send_from_directory('.', 'index.html')
        except:
            pass
    # Return JSON API info
    return jsonify({
        'service': 'OcrVerification API',
        'version': '1.0.0',
        'status': 'running',
        'endpoints': {
            'GET /': 'API information / Web UI',
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
    """Process uploaded Aadhaar images (single or both)"""
    try:
        # Check if at least one image is provided
        has_front = 'front' in request.files and request.files['front'].filename != ''
        has_back = 'back' in request.files and request.files['back'].filename != ''
        
        if not has_front and not has_back:
            return jsonify({'error': 'Upload at least one image (front or back)'}), 400
        
        front_path = None
        back_path = None
        
        # Handle front image
        if has_front:
            front = request.files['front']
            front_path = os.path.join(UPLOAD_FOLDER, 'aff.jpg')
            front.save(front_path)
        
        # Handle back image
        if has_back:
            back = request.files['back']
            back_path = os.path.join(UPLOAD_FOLDER, 'aadhaarBack.jpg')
            back.save(back_path)
        
        # If only one image provided, use it for both (parser will handle it)
        if not has_front:
            front_path = back_path
        elif not has_back:
            back_path = front_path
        
        # Import and run main processing
        from main import process_images, assemble_final
        from modules.output_formatter import format_detailed_response
        
        result = process_images(front_path, back_path)
        final = assemble_final(result)
        
        # Extract components for formatter
        final_data = final.get('final_data', {})
        translations = final.get('translations', {})
        ocr_details_front = final.get('detailed_breakdown', {}).get('ocr_front_extracted', {}).get('ocr_parsed_dict', {})
        ocr_details_back = final.get('detailed_breakdown', {}).get('ocr_back_extracted', {}).get('ocr_parsed_dict', {})
        qr_data = final.get('detailed_breakdown', {}).get('qr_xml_extracted', {}).get('qr_decoded', {})
        
        # Format for cleaner output
        formatted_result = format_detailed_response(final_data, translations, ocr_details_front, ocr_details_back, qr_data)
        
        # Add raw data for advanced users
        formatted_result['raw_data'] = final.get('raw_sources', {})
        
        # Add upload info
        formatted_result['upload_info'] = {
            'front_uploaded': has_front,
            'back_uploaded': has_back,
            'single_image_mode': (has_front and not has_back) or (has_back and not has_front)
        }
        
        # Save result to outputs folder
        output_file = os.path.join(OUTPUT_FOLDER, f'output_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        with open(output_file, 'w') as f:
            json.dump(formatted_result, f, indent=2, ensure_ascii=False)
        
        return jsonify(formatted_result), 200
        
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
