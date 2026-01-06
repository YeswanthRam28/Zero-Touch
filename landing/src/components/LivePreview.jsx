import React, { useEffect, useState, useRef } from 'react';
import { motion } from 'framer-motion';
import Waveform from './Waveform';
import GazeRing from './GazeRing';
import { fetchFusion, mockFusion } from '../services/fusionClient';

const LivePreview = () => {
  const [fusion, setFusion] = useState(null);
  const [sim, setSim] = useState(true);
  const [streaming, setStreaming] = useState(false);
  const mounted = useRef(true);
  const streamCancel = useRef(null);

  // Ensure this component fills vertical space when used in Dashboard right column
  const rootRef = useRef(null);

  useEffect(() => {
    mounted.current = true;

    const startPolling = () => {
      const interval = setInterval(async () => {
        let res;
        if (sim) {
          res = mockFusion();
        } else {
          res = await fetchFusion(1200);
          if (!res.ok) res = mockFusion();
        }

        if (mounted.current) setFusion(res.data);
      }, 1800);
      return interval;
    };

    let intervalId = startPolling();

    // initial fetch
    (async () => {
      const r = sim ? mockFusion() : await fetchFusion(1200);
      setFusion(r.data);
    })();

    return () => {
      mounted.current = false;
      clearInterval(intervalId);
    };
  }, [sim]);

  // streaming effect
  useEffect(() => {
    import('../services/fusionSocket.js').then((mod) => {
      if (!streaming) {
        if (streamCancel.current) {
          streamCancel.current();
          streamCancel.current = null;
        }
        return;
      }

      // try to connect to ws endpoint proxied at /fusion-stream
      const url = (location.protocol === 'https:' ? 'wss:' : 'ws:') + '//' + location.host + '/fusion-stream';
      let ws;
      let cancelMock;

      try {
        ws = mod.connectFusionSocket(url, (msg) => {
          if (msg.ok) setFusion(msg.data);
        });
      } catch (e) {
        // fallback to mock stream
      }

      if (!ws) {
        cancelMock = mod.startMockStream((msg) => setFusion(msg.data), 1000);
      }

      streamCancel.current = () => {
        if (ws) ws.close();
        if (cancelMock) cancelMock();
      };
    });

    return () => {
      if (streamCancel.current) {
        streamCancel.current();
        streamCancel.current = null;
      }
    };
  }, [streaming]);

  return (
    <section id="demo" ref={rootRef} className="h-full py-4 px-2">
      <div className="h-full grid grid-cols-1 lg:grid-cols-1 gap-4 h-full">
        <div className="flex flex-col h-full">
          <div className="flex items-center justify-between mb-3">
            <motion.h3
              initial={{ opacity: 0, y: 6 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="text-xl font-bold"
            >
              Live Interaction Preview
            </motion.h3>
            <div className="flex items-center gap-3">
              <label className="text-sm text-gray-300">Simulation</label>
              <input type="checkbox" checked={sim} onChange={() => setSim((s) => !s)} />
              <label className="text-sm text-gray-300 ml-2">Streaming</label>
              <input type="checkbox" checked={streaming} onChange={() => setStreaming((s) => !s)} />
            </div>
          </div>

          <div className="glass p-4 rounded-lg flex-1 flex flex-col overflow-hidden">
            <div className="text-sm text-gray-300 mb-3">Sample Voice Commands</div>
            <div className="flex gap-4 h-full">
              <div className="w-1/2 overflow-auto">
                <ul className="text-sm text-gray-200 list-disc pl-5">
                  <li>Open patient file</li>
                  <li>Show CT scan</li>
                  <li>Next image / Previous image</li>
                  <li>Zoom in / Zoom out / Reset view</li>
                  <li>Highlight abnormalities</li>
                  <li>Analyze this region</li>
                  <li>Compare with pre-op scan</li>
                </ul>
              </div>

              <div className="flex-1 flex flex-col gap-4">
                <div className="glass p-4 rounded-lg flex-1 overflow-hidden">
                  <div className="text-sm text-gray-300 mb-2">Voice Waveform</div>
                  <Waveform key={fusion?.timestamp} />
                </div>

                <div className="glass p-4 rounded-lg h-28 flex items-center justify-center">
                  <div className="text-sm text-gray-300">Gaze Focus</div>
                  <GazeRing size={60} />
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="glass p-4 rounded-lg h-40 mt-0">
          <div className="flex items-center justify-between mb-2">
            <div className="text-sm text-gray-300">Fusion Decision</div>
            <div className="text-xs text-gray-400">Updated live</div>
          </div>

          <div className="p-3 rounded-md bg-black/20">
            <div className="font-medium mb-2">Action: <span className="text-primary">{fusion?.action ?? '—'}</span></div>
            <div className="text-sm text-gray-300">Status: {fusion?.status ?? '—'}</div>
            <div className="text-sm text-gray-300">Reason: {fusion?.reason ?? '—'}</div>
            <div className="text-sm text-gray-300">Score: {fusion?.score ?? '—'}</div>
          </div>

          <div className="mt-3 text-xs text-gray-400">Note: This preview uses the `/fusion` endpoint or simulated telemetry when Simulation is enabled.</div>
        </div>
      </div>
    </section>
  );
};

export default LivePreview;