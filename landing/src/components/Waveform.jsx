import React from 'react';

const Waveform = ({ width = 340, height = 80 }) => {
  // Simple SVG waveform mock suitable for a live preview (not real audio)
  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} className="rounded-md w-full h-auto bg-black/20 p-2">
      <defs>
        <linearGradient id="wf" x1="0" x2="1">
          <stop offset="0%" stopColor="#6b33ff" stopOpacity="0.9" />
          <stop offset="100%" stopColor="#00f2ff" stopOpacity="0.7" />
        </linearGradient>
      </defs>
      <g stroke="url(#wf)" strokeWidth="2" fill="none" strokeLinecap="round">
        <path d={`M0 ${height / 2} Q ${width * 0.125} ${height * 0.4} ${width * 0.25} ${height / 2} Q ${width * 0.375} ${height * 0.6} ${width * 0.5} ${height / 2} Q ${width * 0.625} ${height * 0.35} ${width * 0.75} ${height / 2} Q ${width * 0.875} ${height * 0.7} ${width} ${height / 2}`} />
      </g>
    </svg>
  );
};

export default Waveform;