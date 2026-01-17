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
    <div className="h-full flex flex-col gap-6">
      <div className="space-y-6">
        {/* Voice Visualization */}
        <div>
          <div className="text-[10px] text-gray-500 uppercase tracking-[0.2em] mb-3 px-1">Audio Signature</div>
          <div className="glass-morphism shadow-inner p-4 rounded-3xl flex items-center justify-center bg-white/[0.02] border border-white/5 h-32 relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-b from-cyan-500/5 to-transparent pointer-events-none"></div>
            <Waveform key={voiceData?.timestamp} />
          </div>
        </div>

        {/* Gaze Tracking */}
        <div>
          <div className="text-[10px] text-gray-500 uppercase tracking-[0.2em] mb-3 px-1">Ocular Tracking</div>
          <div className="glass-morphism p-6 rounded-3xl flex items-center justify-center bg-white/[0.02] border border-white/5 h-32 relative">
            <GazeRing size={48} />
            <div className="absolute bottom-2 right-4 text-[8px] font-mono text-cyan-500/50">XYZ: 0.12, 0.45, -0.89</div>
          </div>
        </div>
      </div>

      {/* Telemetry Details */}
      <div className="glass-morphism p-5 rounded-3xl bg-white/[0.02] border border-white/5 mt-auto">
        <div className="text-[10px] text-white/40 uppercase tracking-[0.2em] mb-4 font-medium border-b border-white/5 pb-2">Telemetry</div>
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-[10px] text-gray-500 uppercase">Focus</span>
            <span className="text-[11px] text-cyan-400 font-mono tracking-tight">{visionData?.object || 'SCANNING...'}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-[10px] text-gray-500 uppercase">Intent</span>
            <span className="text-[11px] text-secondary font-mono tracking-tight">{voiceData?.intent || 'LISTENING...'}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-[10px] text-gray-500 uppercase">Confidence</span>
            <span className="text-[11px] text-green-400 font-mono">{(voiceData?.confidence * 100 || 0).toFixed(1)}%</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LivePreview;