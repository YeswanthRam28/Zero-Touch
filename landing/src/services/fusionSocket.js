// Minimal WebSocket helper for LivePreview streaming
export function connectFusionSocket(url, onMessage) {
  try {
    const ws = new WebSocket(url);
    ws.onopen = () => console.debug('fusion socket open');
    ws.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data);
        onMessage({ ok: true, data });
      } catch (e) {
        onMessage({ ok: false, error: String(e) });
      }
    };
    ws.onerror = (e) => onMessage({ ok: false, error: 'socket error' });
    ws.onclose = () => console.debug('fusion socket closed');
    return ws;
  } catch (e) {
    onMessage({ ok: false, error: String(e) });
    return null;
  }
}

// Simulated streaming generator (calls onMessage periodically)
export function startMockStream(onMessage, ms = 1000) {
  const id = setInterval(() => {
    const now = Date.now() / 1000;
    const choices = [
      { action: 'OPEN_PATIENT_FILE', status: 'APPROVED', reason: 'Patient file requested', score: 0.92 },
      { action: 'SHOW_CT_SCAN', status: 'APPROVED', reason: 'CT scan requested', score: 0.9 },
      { action: 'ZOOM_IN', status: 'APPROVED', reason: 'Zoom command', score: 0.86 },
      { action: 'NONE', status: 'REJECTED', reason: 'No valid conditions', score: 0.45 },
      { action: 'IGNORE', reason: 'Out of sync', score: 0.0 },
    ];
    const pick = choices[Math.floor(Math.abs(Math.sin(now)) * choices.length) % choices.length];
    onMessage({ ok: true, data: { ...pick, timestamp: now } });
  }, ms);
  return () => clearInterval(id);
}