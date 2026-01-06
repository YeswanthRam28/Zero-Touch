import os
import sys

# Ensure project root is on sys.path so imports like `from fusion import fuse`
# work when running this file from the backend/ directory.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, jsonify, request, send_from_directory
from werkzeug.utils import secure_filename
from fusion import fuse
from backend.vision import get_vision_output
from backend.voice import get_voice_output

app = Flask(__name__)

# Directory where sample images are stored/uploaded
SAMPLES_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'samples'))
os.makedirs(SAMPLES_DIR, exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def _allowed(filename: str) -> bool:
    if not filename or '.' not in filename:
        return False
    return filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Allow CORS in development so the Vite dev server can call /fusion
try:
    from flask_cors import CORS
    CORS(app)
except Exception:
    @app.after_request
    def _cors_headers(response):
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
        response.headers['Access-Control-Allow-Methods'] = 'GET,POST,OPTIONS'
        return response

@app.route("/fusion")
def fusion_endpoint():
    vision_data = get_vision_output()
    voice_data = get_voice_output()
    decision = fuse(vision_data, voice_data)
    return jsonify(decision)


@app.route('/upload', methods=['POST'])
def upload_file():
    """Accept a single file upload with form field 'file' and save to ./samples."""
    if 'file' not in request.files:
        return jsonify({'error': 'no file part'}), 400
    f = request.files['file']
    if f.filename == '':
        return jsonify({'error': 'no filename'}), 400
    filename = secure_filename(f.filename)
    if not _allowed(filename):
        return jsonify({'error': 'invalid file type'}), 400
    dest = os.path.join(SAMPLES_DIR, filename)
    f.save(dest)
    return jsonify({'saved': filename, 'path': f'/samples/{filename}'}), 201


@app.route('/samples', methods=['GET'])
def list_samples():
    """Return JSON list of sample filenames (newest first)."""
    files = [f for f in os.listdir(SAMPLES_DIR) if _allowed(f)]
    files.sort(key=lambda f: os.path.getmtime(os.path.join(SAMPLES_DIR, f)), reverse=True)
    return jsonify(files)


@app.route('/samples/<path:filename>')
def serve_sample(filename):
    """Serve uploaded sample images for preview."""
    return send_from_directory(SAMPLES_DIR, filename)

if __name__ == "__main__":
    app.run(debug=True)
