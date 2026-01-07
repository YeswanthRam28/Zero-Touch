import React from 'react';
import { motion } from 'framer-motion';
import LightPillar from './components/LightPillar';
import Hero from './components/Hero';
import Features from './components/Features';
import LivePreview from './components/LivePreview';
import Dashboard from './components/Dashboard';
import Samples from './pages/Samples';
import Viewer from './pages/Viewer';
import Footer from './components/Footer';

const App = () => {
  const getRoute = () => window.location.hash.replace(/^#\/?/, '') || 'home';
  const [route, setRoute] = React.useState(getRoute());

  React.useEffect(() => {
    const onHash = () => setRoute(getRoute());
    window.addEventListener('hashchange', onHash);
    return () => window.removeEventListener('hashchange', onHash);
  }, []);

  const handleLaunch = () => {
    window.location.hash = '/dashboard';
  };

  const handleBack = () => {
    window.location.hash = '';
  };

  return (
    <div className="relative min-h-screen bg-bg overflow-hidden">
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

      <main className="relative z-10 w-full">
        {route === 'home' ? (
          <>
            <Hero onLaunch={handleLaunch} />
            <Features />

            {/* AI Fusion & Why sections inline */}
            <section className="py-16 px-6">
              <div className="max-w-6xl mx-auto">
                <motion.h2 initial={{ opacity: 0, y: 8 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.6 }} className="text-2xl font-bold mb-4">AI Fusion Engine</motion.h2>
                <p className="text-gray-300 max-w-3xl mb-6">Voice, gaze, and gesture are fused in a context-aware engine to produce safe, explainable decisions in OR workflows. The engine aligns timestamps, weights confidences, and follows deterministic rules validated by clinical workflows.</p>

                <motion.div className="glass p-4 rounded-lg text-sm text-gray-300">Reliability: Research-driven • OR-ready • Sterility-compliant</motion.div>
              </div>
            </section>

            <LivePreview />
            <Footer />
          </>
        ) : route === 'dashboard' ? (
          <Dashboard onBack={handleBack} />
        ) : route === 'samples' ? (
          <Samples />
        ) : route === 'viewer' ? (
          <Viewer />
        ) : (
          <div className="p-8">Not found</div>
        )}
      </main>

      {/* Bottom decorative line */}
      <div className="fixed bottom-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-primary/50 to-transparent opacity-50" />
    </div>
  );
};

export default App;
