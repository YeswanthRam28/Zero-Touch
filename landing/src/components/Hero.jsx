import React from 'react';
import { motion } from 'framer-motion';
import { ArrowRight, Play } from 'lucide-react';

const Hero = ({ onLaunch }) => {
  return (
    <section className="min-h-screen flex flex-col items-center justify-center px-6 text-center">
      <motion.h1
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1, duration: 0.7 }}
        className="text-5xl md:text-7xl lg:text-8xl font-bold glow-text mb-6 select-none"
      >
        Zero-Touch Surgical Navigation
      </motion.h1>

      <motion.p
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.25, duration: 0.7 }}
        className="text-lg md:text-xl text-gray-300 max-w-3xl mb-10 leading-relaxed"
      >
        Hands-free control of medical imaging using <strong>Voice</strong>, <strong>Gaze</strong>, and <strong>Gesture</strong>. Clinical-grade, OR-ready, and designed to reduce infection risk.
      </motion.p>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5, duration: 0.7 }}
        className="flex flex-col sm:flex-row gap-4"
      >
        <a
          aria-label="Launch Interface"
          className="btn-primary py-3 px-8 text-lg font-bold shadow-[0_0_30px_rgba(82,39,255,0.18)] hover:shadow-[0_0_50px_rgba(82,39,255,0.35)] transition-all transform hover:scale-[1.03] active:scale-95"
          href="#"
          onClick={(e) => {
            e.preventDefault();
            if (onLaunch) onLaunch();
          }}
        >
          Launch Interface
          <ArrowRight size={18} />
        </a>

        <a
          aria-label="View demo"
          href="#demo"
          className="btn-secondary py-2 px-6 text-lg font-semibold"
        >
          <Play size={16} className="inline-block mr-2" /> View Demo
        </a>
      </motion.div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.8, duration: 1.0 }}
        className="mt-12 w-full max-w-4xl"
      >
        {/* Optional subtle background visual or tagline */}
        <div className="glass p-4 text-left text-sm text-gray-300">
          <strong>Clinical focus:</strong> Sterility compliance • Reduced cognitive load • Faster intraoperative decision-making
        </div>
      </motion.div>
    </section>
  );
};

export default Hero;
