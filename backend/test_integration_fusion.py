"""Integration tests for /fusion endpoint.

1) In-process test using Flask `test_client()` (no network required).
2) Network binding test: start a background WSGI server and perform an HTTP GET.
"""
import json
import time
from urllib.request import urlopen
from urllib.error import URLError

# In-process test

def test_inprocess():
    import backend.app as app_mod
    app = app_mod.app

    # Patch the vision/voice providers to deterministic sample inputs
    app_mod.get_vision_output = lambda: {"object": "person", "confidence": 0.91, "timestamp": 12.42}
    app_mod.get_voice_output = lambda: {"transcript": "open patient file", "intent": "COMMAND", "confidence": 0.87, "timestamp": 12.55}

    client = app.test_client()
    resp = client.get('/fusion')
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, dict)
    assert data.get('action') == 'OPEN_PATIENT_FILE'
    print('in-process /fusion test PASSED')


# Network binding test using werkzeug make_server

def test_network_bind(host='127.0.0.1', port=5001, timeout=3.0):
    try:
        from werkzeug.serving import make_server
    except Exception as e:
        print('werkzeug not available; skipping network binding test:', e)
        return

    import backend.app as app_mod
    app = app_mod.app

    # Use deterministic inputs so output is stable
    app_mod.get_vision_output = lambda: {"object": "person", "confidence": 0.91, "timestamp": 12.42}
    app_mod.get_voice_output = lambda: {"transcript": "open patient file", "intent": "COMMAND", "confidence": 0.87, "timestamp": 12.55}

    srv = make_server(host, port, app)

    from threading import Thread

    thread = Thread(target=srv.serve_forever)
    thread.daemon = True
    thread.start()

    url = f'http://{host}:{port}/fusion'
    try:
        t0 = time.time()
        while True:
            try:
                with urlopen(url, timeout=timeout) as r:
                    body = r.read()
                    data = json.loads(body)
                    assert data.get('action') == 'OPEN_PATIENT_FILE'
                    print('network binding /fusion test PASSED')
                    break
            except URLError as e:
                if time.time() - t0 > timeout:
                    raise
                time.sleep(0.1)
    finally:
        try:
            srv.shutdown()
        except Exception:
            pass


if __name__ == '__main__':
    test_inprocess()
    test_network_bind()
