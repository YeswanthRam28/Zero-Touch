// Simple fusion client for frontend to fetch /fusion with timeout and a mock fallback
export async function fetchFusion(timeoutMs = 1500) {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const res = await fetch('/fusion', { signal: controller.signal });
    clearTimeout(id);
    if (!res.ok) throw new Error('Network response not ok');
    const data = await res.json();
    return { ok: true, data };
  } catch (e) {
    clearTimeout(id);
    return { ok: false, error: String(e) };
  }
}

export function mockFusion() {
  const now = Date.now() / 1000;
  const choices = [
    { action: 'OPEN_PATIENT_FILE', status: 'APPROVED', reason: 'Patient file requested', score: 0.92 },
    { action: 'SHOW_CT_SCAN', status: 'APPROVED', reason: 'CT scan requested', score: 0.9 },
    { action: 'ZOOM_IN', status: 'APPROVED', reason: 'Zoom command', score: 0.86 },
    { action: 'HIGHLIGHT_ABNORMALITIES', status: 'APPROVED', reason: 'Highlight command', score: 0.88 },
    { action: 'NONE', status: 'REJECTED', reason: 'No valid conditions', score: 0.45 },
    { action: 'IGNORE', reason: 'Out of sync', score: 0.0 },
  ];
  // Return a semi-random stable sequence
  const pick = choices[Math.floor(Math.abs(Math.sin(now)) * choices.length) % choices.length];
  return { ok: true, data: { ...pick, timestamp: now } };
}
