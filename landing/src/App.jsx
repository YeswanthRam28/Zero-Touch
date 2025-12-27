import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Activity, Eye, Mic, HandMetal, ShieldCheck, Zap, ArrowRight, Github, ExternalLink, Menu, X } from 'lucide-react';
import LightPillar from './components/LightPillar';

const App = () => {
  return (
    <div className="relative min-h-screen bg-bg overflow-hidden flex flex-col items-center justify-center">
      {/* Background Component */}
      <div className="fixed inset-0 z-0 pointer-events-none opacity-40">
        <LightPillar
          topColor="#5227FF"
          bottomColor="#FF9FFC"
          intensity={0.8}
          rotationSpeed={0.2}
          glowAmount={0.003}
          pillarWidth={4.0}
          pillarHeight={0.6}
          noiseIntensity={0.3}
          interactive={true}
        />
      </div>

      {/* Precision Grid Overlay */}
      <div className="fixed inset-0 z-1 pointer-events-none opacity-[0.03] bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:40px_40px] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)]"></div>

      <main className="relative z-10 w-full animate-in fade-in duration-1000">
        {/* Only Hero Section remains as requested */}
        <section className="min-h-screen flex flex-col items-center justify-center px-4 text-center">
          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.8 }}
            className="text-6xl md:text-9xl font-bold glow-text mb-12 mt-4 select-none"
          >
            Zero-Touch
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4, duration: 0.8 }}
            className="text-xl md:text-2xl text-gray-400 max-w-3xl mb-20 leading-relaxed"
          >
            The future of <span className="text-primary font-bold">surgical navigation</span>. Control medical imaging through
            <span className="text-white italic"> gesture</span>,
            <span className="text-white italic"> gaze</span>, and
            <span className="text-white italic"> voice</span> without ever touching a screen.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6, duration: 0.8 }}
            className="flex flex-col sm:flex-row gap-6 mt-80"
          >
            <a href="http://localhost:5173/" className="btn-primary py-4 px-12 text-lg font-bold shadow-[0_0_30px_rgba(82,39,255,0.3)] hover:shadow-[0_0_50px_rgba(82,39,255,0.6)] transition-all transform hover:scale-105 active:scale-95">
              Launch Interface
              <ArrowRight size={22} className="group-hover:translate-x-1 transition-transform" />
            </a>
          </motion.div>
        </section>
      </main>

      {/* Bottom decorative line */}
      <div className="fixed bottom-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-primary/50 to-transparent opacity-50" />
    </div>
  );
};

export default App;
