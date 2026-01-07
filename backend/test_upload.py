import io
import os
from backend.app import app, SAMPLES_DIR


def test_upload_and_serve():
    client = app.test_client()

    data = {
        'file': (io.BytesIO(b'\x89PNG\r\n\x1a\n'), 'test.png')
    }

    resp = client.post('/upload', data=data, content_type='multipart/form-data')
    assert resp.status_code == 201
    j = resp.get_json()
    assert j.get('saved') == 'test.png'

    # Check file exists
    path = os.path.join(SAMPLES_DIR, 'test.png')
    assert os.path.exists(path)

    # Check listing endpoint includes metadata for the file
    list_resp = client.get('/samples')
    assert list_resp.status_code == 200
    lst = list_resp.get_json()
    filenames = [it['filename'] for it in lst]
    assert 'test.png' in filenames

    # Check metadata endpoints
    md_resp = client.post('/samples/test.png/tags', json={'tags': ['CT', 'urgent']})
    assert md_resp.status_code == 200
    assert 'CT' in md_resp.get_json().get('tags', [])

    notes_resp = client.post('/samples/test.png/notes', json={'notes': 'Test note'})
    assert notes_resp.status_code == 200
    assert 'Test note' in notes_resp.get_json().get('notes')

    fav_resp = client.post('/samples/test.png/favorite', json={'favorite': True})
    assert fav_resp.status_code == 200
    assert fav_resp.get_json().get('favorite') is True

    # Cleanup
    try:
        os.remove(path)
        os.remove(os.path.join(SAMPLES_DIR, 'metadata.json'))
    except Exception:
        pass
