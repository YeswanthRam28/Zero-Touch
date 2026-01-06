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

    # Check listing endpoint includes file
    list_resp = client.get('/samples')
    assert list_resp.status_code == 200
    lst = list_resp.get_json()
    assert 'test.png' in lst

    # Cleanup
    try:
        os.remove(path)
    except Exception:
        pass
