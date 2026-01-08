import React, { useEffect, useState, useRef } from 'react';
import { motion } from 'framer-motion';
import Waveform from './Waveform';
import GazeRing from './GazeRing';

const LivePreview = () => {
  const [visionData, setVisionData] = useState(null);
  const [voiceData, setVoiceData] = useState(null);
  const mounted = useRef(true);

  useEffect(() => {
    mounted.current = true;

    const loadData = async () => {
      try {
        const visRes = await fetch('/vision');
        const voiRes = await fetch('/voice');
        if (visRes.ok) {
          const vData = await visRes.json();
          if (mounted.current) setVisionData(vData);
        }
        if (voiRes.ok) {
          const vData = await voiRes.json();
          if (mounted.current) setVoiceData(vData);
        }
      } catch (e) {
        // ignore
      }
    };

    const intervalId = setInterval(loadData, 2000);
    loadData();

    return () => {
      mounted.current = false;
      clearInterval(intervalId);
    };
  }, []);

  return (
    <section id="demo" className="h-full py-4 px-2">
      <div className="h-full flex flex-col gap-4">
        <div className="flex flex-col h-full">
          <div className="flex items-center justify-between mb-3">
            <motion.h2
              initial={{ opacity: 0, y: 6 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="text-xl font-bold"
            >
              Live Sensor Feedback
            </motion.h2>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
              <span className="text-[10px] text-gray-400 uppercase tracking-widest font-bold">Active</span>
            </div>
          </div>

          <div className="glass p-4 rounded-lg flex-1 flex flex-col overflow-hidden">
            <div className="text-sm text-gray-300 mb-2">Voice Activity</div>
            <div className="glass p-4 rounded-lg flex-1 mb-4 flex items-center justify-center overflow-hidden">
              <Waveform key={voiceData?.timestamp} />
            </div>

            <div className="text-sm text-gray-300 mb-2">Gaze Tracking</div>
            <div className="glass p-4 rounded-lg h-28 flex items-center justify-center">
              <GazeRing size={60} />
            </div>
          </div>
        </div>

        <div className="glass p-4 rounded-lg">
          <div className="text-sm text-gray-300 mb-2 font-medium">Real-time Telemetry</div>
          <div className="space-y-2">
            <div className="flex justify-between text-xs">
              <span className="text-gray-400">Vision Detected:</span>
              <span className="text-primary font-mono">{visionData?.object || 'none'}</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-gray-400">Voice Intent:</span>
              <span className="text-secondary font-mono">{voiceData?.intent || 'listening...'}</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-gray-400">Signal Confidence:</span>
              <span className="text-green-400 font-mono">{(voiceData?.confidence * 100 || 0).toFixed(1)}%</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default LivePreview;