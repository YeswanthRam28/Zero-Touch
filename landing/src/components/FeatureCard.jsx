import React from 'react';
import { motion } from 'framer-motion';

const FeatureCard = ({ title, subtitle, icon, children }) => {
  return (
    <motion.div
      whileHover={{ translateY: -6, boxShadow: '0 12px 30px rgba(82,39,255,0.12)' }}
      className="glass p-6 rounded-lg border border-transparent hover:border-purple-600/30 transition-all"
    >
      <div className="flex items-center gap-4 mb-3">
        <div className="w-12 h-12 rounded-full bg-gradient-to-br from-purple-700 to-blue-400 flex items-center justify-center text-white shadow-md">
          {icon}
        </div>
        <div>
          <div className="font-semibold text-lg">{title}</div>
          <div className="text-sm text-gray-300">{subtitle}</div>
        </div>
      </div>
      <div className="text-sm text-gray-300">{children}</div>
    </motion.div>
  );
};

export default FeatureCard;
