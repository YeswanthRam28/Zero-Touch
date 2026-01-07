import React, { useEffect, useState, useRef } from 'react';
import LivePreview from './LivePreview';
import { fetchFusion, mockFusion } from '../services/fusionClient';
import { Upload, ChevronLeft, ChevronRight, Image as ImageIcon, HelpCircle, ArrowLeft } from 'lucide-react';

const Dashboard = ({ onBack }) => {
  const [fusion, setFusion] = useState(null);

  // Helper to handle both string filenames and object metadata
  const getName = (img) => (typeof img === 'string' ? img : img.filename || img.name || 'unknown');

  useEffect(() => {
    let mounted = true;
    const load = async () => {
      const res = await fetchFusion(1200);
      if (!res.ok) setFusion(mockFusion().data);
      else setFusion(res.data);
    };
    load();
    const id = setInterval(load, 2000);
    return () => {
      mounted = false;
      clearInterval(id);
    };
  }, []);

  const [images, setImages] = useState([]);
  const [selectedImage, setSelectedImage] = useState(null);
  const [showHelp, setShowHelp] = useState(false);
  const [showControls, setShowControls] = useState(true);

  const uploadFile = async (file) => {
    const fd = new FormData();
    fd.append('file', file);
    try {
      const res = await fetch('/upload', { method: 'POST', body: fd });
      if (!res.ok) throw new Error('Upload failed');
      const j = await res.json();
      setImages((s) => [j.saved, ...s]);
      setSelectedImage(j.saved);
    } catch (e) {
      console.error(e);
      alert('Upload failed: ' + e.message);
    }
  };

  useEffect(() => {
    const loadSamples = async () => {
      try {
        const res = await fetch('/samples');
        if (res.ok) {
          const lst = await res.json();
          setImages(lst);
          if (lst.length > 0) setSelectedImage(lst[0]);
        }
      } catch (e) {
        // ignore
      }
    };
    loadSamples();
  }, []);

  // Navigation handlers
  const showPrev = () => {
    if (!images.length) return;
    const idx = images.indexOf(selectedImage);
    const i = (idx - 1 + images.length) % images.length;
    setSelectedImage(images[i]);
  };

  const showNext = () => {
    if (!images.length) return;
    const idx = images.indexOf(selectedImage);
    const i = (idx + 1) % images.length;
    setSelectedImage(images[i]);
  };

  // Keyboard shortcuts
  useEffect(() => {
    const onKey = (e) => {
      if (e.key === 'ArrowLeft') showPrev();
      if (e.key === 'ArrowRight') showNext();
      if (e.key === 'h') setShowControls(prev => !prev);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [images, selectedImage]);

  return (
    <div className="relative h-screen w-full bg-black overflow-hidden flex flex-col">

      {/* 1. Main Content: The Image (Fullscreen) */}
      <div className="absolute inset-0 flex items-center justify-center z-0 bg-[#050505]">
        {selectedImage ? (
          <img
            src={`/samples/${getName(selectedImage)}`}
            alt={getName(selectedImage)}
            className="w-full h-full object-contain"
          />
        ) : (
          <div className="text-gray-500 flex flex-col items-center">
            <ImageIcon className="w-16 h-16 mb-4 opacity-50" />
            <p>No image loaded</p>
            <p className="text-sm">Upload or select a sample</p>
          </div>
        )}
      </div>

      {/* 2. Top Right: Fusion Decision Box (Small) */}
      <div className="absolute top-4 right-4 z-20">
        <div className="glass border border-white/10 rounded-lg p-3 w-64 shadow-2xl backdrop-blur-xl bg-black/40 transition-all duration-300 hover:bg-black/60">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] uppercase tracking-widest text-primary/80 font-bold">Fusion Engine</span>
            <div className={`w-2 h-2 rounded-full ${fusion?.status === 'APPROVED' ? 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]' : 'bg-yellow-500'}`} />
          </div>

          <div className="text-xl font-bold text-white tracking-wide truncate">
            {fusion?.action?.replace(/_/g, ' ') || 'IDLE'}
          </div>

          <div className="flex justify-between items-end mt-1">
            <p className="text-xs text-gray-400 truncate max-w-[70%]">{fusion?.reason || 'Waiting for input...'}</p>
            <span className="text-xs font-mono text-cyan-400">{(fusion?.score * 100)?.toFixed(0) || 0}%</span>
          </div>
        </div>
      </div>

      {/* 3. Top Left: Navigation & Branding */}
      <div className="absolute top-4 left-4 z-20 flex items-center gap-3">
        <button onClick={onBack} className="btn-icon glass hover:bg-white/10 text-white p-2 rounded-full transition-colors flex items-center gap-2 pr-4">
          <ArrowLeft size={20} />
          <span className="text-sm font-medium">Exit</span>
        </button>
        <div className="h-6 w-px bg-white/20 mx-1"></div>
        <button onClick={() => setShowHelp(true)} className="btn-icon text-white/70 hover:text-white transition-colors">
          <HelpCircle size={24} />
        </button>
      </div>

      {/* 4. Bottom Right: Live Preview (Picture-in-Picture) */}
      <div className="absolute bottom-4 right-4 z-20 w-48 rounded-lg overflow-hidden border border-white/10 shadow-lg bg-black/80">
        <div className="bg-black/50 px-2 py-1 text-[10px] text-gray-400 uppercase tracking-wider flex justify-between items-center">
          <span>Sensors</span>
          <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse"></span>
        </div>
        <div className="h-32 relative">
          <LivePreview />
        </div>
      </div>

      {/* 5. Bottom Center: Image Gallery Dock */}
      <div className={`absolute bottom-6 left-1/2 transform -translate-x-1/2 z-20 transition-all duration-300 ${showControls ? 'translate-y-0 opacity-100' : 'translate-y-24 opacity-0'}`}>
        <div className="glass px-4 py-3 rounded-2xl flex items-center gap-4 border border-white/10 bg-black/40 backdrop-blur-md shadow-2xl">
          <button onClick={showPrev} className="p-2 hover:bg-white/10 rounded-full text-white/70 hover:text-white transition-colors">
            <ChevronLeft size={20} />
          </button>

          <div className="flex gap-2 mx-2">
            <label className="cursor-pointer relative group w-16 h-16 rounded-xl border-2 border-dashed border-white/20 hover:border-primary/50 flex flex-col items-center justify-center transition-all bg-white/5 hover:bg-white/10">
              <Upload size={18} className="text-gray-400 group-hover:text-primary mb-1" />
              <span className="text-[9px] text-gray-500 uppercase">Upload</span>
              <input type="file" accept="image/png,image/jpeg" className="hidden" onChange={(e) => { if (e.target.files?.[0]) uploadFile(e.target.files[0]); }} />
            </label>

            <div className="h-16 w-px bg-white/10 mx-1"></div>

            <div className="flex gap-2 max-w-[400px] overflow-x-auto no-scrollbar scroll-smooth">
              {images.map((img, idx) => {
                const name = getName(img);
                const isActive = selectedImage === img;
                return (
                  <button
                    key={idx}
                    onClick={() => setSelectedImage(img)}
                    className={`relative w-16 h-16 rounded-xl overflow-hidden transition-all duration-200 border-2 flex-shrink-0 ${isActive ? 'border-primary scale-105 shadow-[0_0_15px_rgba(82,39,255,0.4)]' : 'border-transparent hover:border-white/30 opacity-70 hover:opacity-100'}`}
                  >
                    <img src={`/samples/${name}`} alt={name} className="w-full h-full object-cover" />
                  </button>
                )
              })}
            </div>
          </div>

          <button onClick={showNext} className="p-2 hover:bg-white/10 rounded-full text-white/70 hover:text-white transition-colors">
            <ChevronRight size={20} />
          </button>
        </div>
      </div>

      {/* Help Modal */}
      {showHelp && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
          <div className="glass border border-white/10 p-8 rounded-2xl max-w-2xl w-full shadow-2xl">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">System Controls</h2>
              <button onClick={() => setShowHelp(false)} className="px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10 text-sm font-medium transition-colors">Close</button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 text-sm">
              <div>
                <h3 className="text-primary font-semibold mb-3 flex items-center gap-2">
                  <span>🎙️</span> Voice Commands
                </h3>
                <ul className="space-y-2 text-gray-400">
                  <li>"Open patient file"</li>
                  <li>"Zoom in / Zoom out"</li>
                  <li>"Next image"</li>
                  <li>"Highlight abnormalities"</li>
                </ul>
              </div>

              <div>
                <h3 className="text-secondary font-semibold mb-3 flex items-center gap-2">
                  <span>👋</span> Gestures
                </h3>
                <ul className="space-y-2 text-gray-400">
                  <li>Pinch: Zoom</li>
                  <li>Swipe: Navigate</li>
                  <li>Point: Select Region</li>
                  <li>Palm: Pause</li>
                </ul>
              </div>
            </div>

            <div className="mt-8 pt-6 border-t border-white/10 text-center text-xs text-gray-500">
              Press 'H' to toggle UI controls • Arrow keys to navigate
            </div>
          </div>
        </div>
      )}

    </div>
  );
};

export default Dashboard;
