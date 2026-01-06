# Frontend updates — Zero-Touch landing

This file documents recent UI updates made to the Vite + React + Tailwind landing page.

What changed
- Added industry-level, medical-grade landing page components under `src/components`:
  - `Hero.jsx` — updated hero with clinical headline, CTAs, and animated copy
  - `Features.jsx` + `FeatureCard.jsx` — three feature cards for Voice, Gaze, Gesture
  - `LivePreview.jsx` with small `Waveform.jsx` and `GazeRing.jsx` — mock live preview visuals
  - `Footer.jsx` — refined minimal footer
- Kept `LightPillar` background and improved dark theme styles in `index.css` and `App.css`.
- Used `framer-motion` for subtle fade/slide animations and maintain professional motion.

How to preview
1. From `landing/` run the Vite dev server (existing project setup):

```bash
cd landing
npm install # if needed
npm run dev
```

2. Open http://localhost:5173 and review the redesigned landing.

Notes / Next steps
- Live Preview now polls the `/fusion` endpoint and falls back to simulated telemetry (toggleable via the Simulation checkbox in the Live Interaction Preview).

Simulation: The Live Preview can run in simulation mode if the backend isn't available. Toggle 'Simulation' in the Live Interaction Preview to switch between real backend polling and simulated telemetry. You can also enable **Streaming** to test a WebSocket-based live stream (proxied via `/fusion-stream`) that updates the preview in near real-time.

Developer note: If your frontend dev server runs on a different origin than the backend (for example, Vite on :5173 and Flask on :5000), you may need to configure a proxy (already included in `vite.config.js`) or CORS to allow the browser to request `/fusion` directly.

- Add more visual polish in Figma if required (color tokens, spacing, micro-interactions).
