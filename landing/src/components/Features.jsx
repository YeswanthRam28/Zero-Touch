import React from 'react';
import FeatureCard from './FeatureCard';
import { Mic, Eye, Hand } from 'lucide-react';
import { motion } from 'framer-motion';

const Features = () => {
  return (
    <section id="features" className="py-20 px-6">
      <div className="max-w-6xl mx-auto">
        <motion.h2
          initial={{ opacity: 0, y: 8 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-3xl md:text-4xl font-bold mb-6"
        >
          AI-driven Surgical Capabilities
        </motion.h2>

        <motion.p
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="text-gray-300 max-w-3xl mb-8"
        >
          Hands-free navigation of scans using voice, gaze, and gesture. Precise commands for zoom, rotate, slice, and view switching — designed for the sterile field.
        </motion.p>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          <FeatureCard
            title="Voice-Driven Command Interface"
            subtitle="Medical-grade speech control"
            icon={<Mic size={18} />}
          >
            Execute commands like <span className="font-mono">zoom in</span>, <span className="font-mono">next image</span>, or <span className="font-mono">increase contrast</span> using secure, local ASR.
          </FeatureCard>

          <FeatureCard
            title="Gaze-Aware Navigation"
            subtitle="Eye-tracking focus detection"
            icon={<Eye size={18} />}
          >
            Focus-aware highlighting and gaze cursors for rapid, hands-free selection of regions of interest on medical images.
          </FeatureCard>

          <FeatureCard
            title="Gesture Recognition Control"
            subtitle="Sterile-field safe interactions"
            icon={<Hand size={18} />}
          >
            Natural hand gestures for precise control — swipe, pinch, rotate — with smooth, low-latency feedback.
          </FeatureCard>
        </div>
      </div>
    </section>
  );
};

export default Features;
