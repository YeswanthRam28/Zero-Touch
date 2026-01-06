import React from 'react';

const GazeRing = ({ size = 120 }) => {
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="rounded-full">
      <defs>
        <radialGradient id="rg" cx="50%" cy="50%" r="50%">
          <stop offset="20%" stopColor="#fff" stopOpacity="0.06" />
          <stop offset="60%" stopColor="#5227FF" stopOpacity="0.14" />
          <stop offset="100%" stopColor="#00F2FF" stopOpacity="0.02" />
        </radialGradient>
      </defs>
      <circle cx={size / 2} cy={size / 2} r={size / 2 - 2} fill="url(#rg)" />
      <circle cx={size / 2} cy={size / 2} r={6} fill="#00F2FF" />
    </svg>
  );
};

export default GazeRing;