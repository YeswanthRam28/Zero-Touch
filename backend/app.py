import os
import sys

# Ensure project root is on sys.path so imports like `from fusion import fuse`
# work when running this file from the backend/ directory.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, jsonify, request, send_from_directory, send_file
from werkzeug.utils import secure_filename
from fusion import fuse
from backend.vision import get_vision_output
from backend.voice import get_voice_output
import json
import datetime

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


METADATA_PATH = os.path.join(SAMPLES_DIR, 'metadata.json')


def _read_metadata():
    try:
        with open(METADATA_PATH, 'r', encoding='utf-8') as fh:
            return json.load(fh)
    except Exception:
        return {}


def _write_metadata(md: dict):
    with open(METADATA_PATH, 'w', encoding='utf-8') as fh:
        json.dump(md, fh, ensure_ascii=False, indent=2)


def _ensure_metadata_for(filename: str):
    md = _read_metadata()
    if filename not in md:
        path = os.path.join(SAMPLES_DIR, filename)
        md[filename] = {
            'filename': filename,
            'uploaded_at': datetime.datetime.utcfromtimestamp(os.path.getmtime(path)).isoformat() + 'Z',
            'size': os.path.getsize(path),
            'tags': [],
            'uploader': None,
            'notes': '',
            'favorite': False,
        }
        _write_metadata(md)
    return md[filename]


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

    # ensure metadata record exists and update
    rec = _ensure_metadata_for(filename)
    rec['uploaded_at'] = datetime.datetime.utcnow().isoformat() + 'Z'
    rec['size'] = os.path.getsize(dest)
    _write_metadata(_read_metadata())

    return jsonify({'saved': filename, 'path': f'/samples/{filename}'}), 201


@app.route('/samples', methods=['GET'])
def list_samples():
    """Return JSON list of sample metadata objects (newest first)."""
    md = _read_metadata()
    # ensure metadata exists for any files present
    files = [f for f in os.listdir(SAMPLES_DIR) if _allowed(f)]
    for f in files:
        _ensure_metadata_for(f)
    md = _read_metadata()
    items = list(md.values())
    items.sort(key=lambda it: it.get('uploaded_at', ''), reverse=True)
    return jsonify(items)


@app.route('/samples/<path:filename>')
def serve_sample(filename):
    """Serve uploaded sample images for preview."""
    return send_from_directory(SAMPLES_DIR, filename)


@app.route('/samples/download/<path:filename>')
def download_sample(filename):
    """Send a sample as an attachment for download."""
    path = os.path.join(SAMPLES_DIR, filename)
    if not os.path.exists(path):
        return jsonify({'error': 'not found'}), 404
    return send_file(path, as_attachment=True)


@app.route('/samples/<path:filename>/tags', methods=['POST'])
def set_tags(filename):
    """Set tags for a given sample. JSON: { tags: [..] }"""
    data = request.get_json() or {}
    tags = data.get('tags')
    if tags is None or not isinstance(tags, list):
        return jsonify({'error': 'invalid tags'}), 400
    md = _read_metadata()
    if filename not in md:
        return jsonify({'error': 'not found'}), 404
    md[filename]['tags'] = tags
    _write_metadata(md)
    return jsonify(md[filename])


@app.route('/samples/<path:filename>/notes', methods=['POST'])
def set_notes(filename):
    """Set freeform notes for a sample. JSON: { notes: '...' }"""
    data = request.get_json() or {}
    notes = data.get('notes', '')
    md = _read_metadata()
    if filename not in md:
        return jsonify({'error': 'not found'}), 404
    md[filename]['notes'] = str(notes)
    _write_metadata(md)
    return jsonify(md[filename])


@app.route('/samples/<path:filename>', methods=['DELETE'])
def delete_sample(filename):
    path = os.path.join(SAMPLES_DIR, filename)
    if os.path.exists(path):
        os.remove(path)
    md = _read_metadata()
    if filename in md:
        del md[filename]
        _write_metadata(md)
    return jsonify({'deleted': filename})


@app.route('/samples/<path:filename>/favorite', methods=['POST'])
def toggle_favorite(filename):
    data = request.get_json() or {}
    fav = bool(data.get('favorite', True))
    md = _read_metadata()
    if filename not in md:
        return jsonify({'error': 'not found'}), 404
    md[filename]['favorite'] = fav
    _write_metadata(md)
    return jsonify(md[filename])

if __name__ == "__main__":
    app.run(debug=True)
