import React, { useEffect, useState, useRef, useCallback } from 'react';
import LivePreview from './LivePreview';
import { Upload, ChevronLeft, ChevronRight, Image as ImageIcon, HelpCircle, ArrowLeft, Maximize2, RotateCcw, ZoomIn, ZoomOut } from 'lucide-react';

const Dashboard = ({ onBack }) => {
  const [visionData, setVisionData] = useState(null);
  const [voiceData, setVoiceData] = useState(null);
  const [images, setImages] = useState([]);
  const [selectedImage, setSelectedImage] = useState(null);
  const [showHelp, setShowHelp] = useState(false);
  const [showControls, setShowControls] = useState(true);

  // Transform State for Image Viewer
  const [transform, setTransform] = useState({ scale: 1, x: 0, y: 0 });
  const [statusMessage, setStatusMessage] = useState({ text: 'SYSTEM READY', type: 'info' });
  const wsRef = useRef(null);
  const messageTimeoutRef = useRef(null);

  const displayMessage = useCallback((text, type = 'info') => {
    setStatusMessage({ text: text.toUpperCase(), type });
    if (messageTimeoutRef.current) clearTimeout(messageTimeoutRef.current);
    messageTimeoutRef.current = setTimeout(() => {
      setStatusMessage(null);
    }, 4000);
  }, []);

  // Helper to handle both string filenames and object metadata
  const getName = (img) => (typeof img === 'string' ? img : img.filename || img.name || 'unknown');

  // Navigation handlers
  const showPrev = useCallback(() => {
    if (!images.length) return;
    setImages(prevImages => {
      const idx = prevImages.findIndex(img => getName(img) === getName(selectedImage));
      const i = (idx - 1 + prevImages.length) % prevImages.length;
      setSelectedImage(prevImages[i]);
      setTransform({ scale: 1, x: 0, y: 0 }); // Reset zoom on nav
      displayMessage(`PREVIOUS IMAGE: ${getName(prevImages[idx])}`, 'action');
      return prevImages;
    });
  }, [images, selectedImage, displayMessage]);

  const showNext = useCallback(() => {
    if (!images.length) return;
    setImages(prevImages => {
      const idx = prevImages.findIndex(img => getName(img) === getName(selectedImage));
      const i = (idx + 1) % prevImages.length;
      setSelectedImage(prevImages[i]);
      setTransform({ scale: 1, x: 0, y: 0 }); // Reset zoom on nav
      displayMessage(`NEXT IMAGE: ${getName(prevImages[idx])}`, 'action');
      return prevImages;
    });
  }, [images, selectedImage, displayMessage]);

  const handleAction = useCallback((action) => {
    const { intent, parameters } = action;
    console.log("Executing Action:", intent, parameters);
    displayMessage(`${intent.replace(/_/g, ' ')}`, 'action');

    switch (intent) {
      case 'ZOOM_IN':
        setTransform(prev => {
          const factor = parameters?.factor || 1.3;
          let newX = prev.x;
          let newY = prev.y;

          // Spatial Targeting
          if (parameters?.region === 'LEFT_REGION') {
            newX = 200; // Shift right to focus left
          } else if (parameters?.region === 'RIGHT_REGION') {
            newX = -200;
          }

          return { ...prev, scale: Math.min(prev.scale * factor, 5), x: newX, y: newY };
        });
        break;
      case 'ZOOM_OUT':
        setTransform(prev => ({ ...prev, scale: Math.max(prev.scale / (parameters?.factor || 1.3), 1), x: 0, y: 0 }));
        break;
      case 'NEXT_IMAGE':
        showNext();
        break;
      case 'PREV_IMAGE':
        showPrev();
        break;
      case 'RESET_VIEW':
        setTransform({ scale: 1, x: 0, y: 0 });
        break;
      case 'HIGHLIGHT_REGION':
        // Show a temporary highlight at parameters.coordinates
        break;
      default:
        console.warn("Unhandled Intent:", intent);
    }
  }, [showNext, showPrev, displayMessage]);

  // WebSocket Connection
  useEffect(() => {
    const connectWS = () => {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.hostname}:8000/ws`;
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => console.log("Connected to Assistant WebSocket");
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'ACTION') {
            handleAction(data);
          } else if (data.type === 'MESSAGE') {
            displayMessage(data.text, 'chat');
          }
        } catch (e) {
          console.error("WS Parse Error:", e);
        }
      };

      ws.onerror = (e) => console.error("WS Error:", e);
      ws.onclose = () => {
        console.log("WS Closed. Retrying in 3s...");
        setTimeout(connectWS, 3000);
      };
      wsRef.current = ws;
    };

    connectWS();
    return () => {
      if (wsRef.current) wsRef.current.close();
    };
  }, [handleAction]);

  // Telemetry Polling (Optional fallback for display)
  useEffect(() => {
    let mounted = true;
    const loadVision = async () => {
      try {
        const res = await fetch('/vision');
        if (res.ok) {
          const data = await res.json();
          if (mounted) setVisionData(data);
        }
      } catch (e) { }
    };
    const loadVoice = async () => {
      try {
        const res = await fetch('/voice');
        if (res.ok) {
          const data = await res.json();
          if (mounted) setVoiceData(data);
        }
      } catch (e) { }
    };
    const id = setInterval(() => {
      loadVision();
      loadVoice();
    }, 1000);
    return () => {
      mounted = false;
      clearInterval(id);
    };
  }, []);

  // Initial Load
  useEffect(() => {
    const loadSamples = async () => {
      try {
        const res = await fetch('/samples');
        if (res.ok) {
          const lst = await res.json();
          setImages(lst);
          if (lst.length > 0) setSelectedImage(lst[0]);
        }
      } catch (e) { }
    };
    loadSamples();
  }, []);

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
    }
  };

  return (
    <div className="relative h-screen w-full bg-[#050505] overflow-hidden flex flex-col font-sans text-gray-200">

      {/* 1. Main Content: The Image (Fullscreen with CSS Transforms) */}
      <div className="absolute inset-0 flex items-center justify-center z-0 overflow-hidden cursor-crosshair">
        {selectedImage ? (
          <div
            className="transition-transform duration-500 ease-out will-change-transform"
            style={{
              transform: `translate(${transform.x}px, ${transform.y}px) scale(${transform.scale})`
            }}
          >
            <img
              src={`/samples/${getName(selectedImage)}`}
              alt={getName(selectedImage)}
              className="max-w-[90vw] max-h-[85vh] object-contain shadow-[0_0_50px_rgba(0,0,0,0.5)] rounded-sm"
              draggable="false"
            />
          </div>
        ) : (
          <div className="text-gray-500 flex flex-col items-center">
            <ImageIcon className="w-16 h-16 mb-4 opacity-30 animate-pulse" />
            <p className="text-lg font-light tracking-widest uppercase">No stream available</p>
          </div>
        )}
      </div>

      {/* Grid Overlay for FUI effect */}
      <div className="absolute inset-0 pointer-events-none opacity-[0.03] z-[1]"
        style={{ backgroundImage: 'radial-gradient(circle, white 1px, transparent 1px)', backgroundSize: '40px 40px' }} />

      {/* 2. Top Right: System Status Box (Transparent Glass) */}
      <div className="absolute top-6 right-6 z-20">
        <div className="glass-morphism border border-white/5 rounded-xl p-4 w-72 shadow-2xl backdrop-blur-3xl bg-black/30">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] uppercase tracking-[0.2em] text-cyan-400/80 font-bold">Protocol Active</span>
            <div className="flex gap-1">
              <div className="w-1 h-3 bg-cyan-500/50 animate-pulse"></div>
              <div className="w-1 h-3 bg-cyan-500/80 animate-pulse" style={{ animationDelay: '0.2s' }}></div>
              <div className="w-1 h-3 bg-cyan-500 animate-pulse" style={{ animationDelay: '0.4s' }}></div>
            </div>
          </div>

          <div className="text-2xl font-light text-white tracking-widest uppercase mb-1">
            {voiceData?.intent !== 'UNKNOWN' ? voiceData?.intent?.replace(/_/g, ' ') : 'STANDBY'}
          </div>

          <div className="h-0.5 w-full bg-gradient-to-r from-cyan-500/50 to-transparent mb-3"></div>

          <div className="grid grid-cols-2 gap-2 text-[10px] font-mono text-gray-400 capitalize">
            <div>Vision: <span className="text-white">{visionData?.raw?.gaze?.eye || 'None'}</span></div>
            <div className="text-right">Scale: <span className="text-cyan-400">{transform.scale.toFixed(2)}x</span></div>
            <div>Gesture: <span className="text-white">{visionData?.raw?.hand?.pose?.replace('_', ' ') || 'Idle'}</span></div>
            <div className="text-right text-green-400">98.2% ACC</div>
          </div>
        </div>
      </div>

      {/* 3. Top Left: Navigation & Branding */}
      <div className="absolute top-6 left-6 z-20 flex items-center gap-4">
        <button onClick={onBack} className="group flex items-center gap-3 glass-morphism py-2 px-6 rounded-full border border-white/10 hover:border-cyan-500/50 transition-all duration-300">
          <ArrowLeft size={18} className="group-hover:-translate-x-1 transition-transform" />
          <span className="text-sm font-light tracking-widest uppercase">Terminate</span>
        </button>
        <button onClick={() => setShowHelp(true)} className="p-2 glass-morphism rounded-full border border-white/10 hover:text-cyan-400 transition-all">
          <HelpCircle size={22} />
        </button>
      </div>

      {/* 4. Bottom Right: Live Sensor Telemetry (PIP) */}
      <div className="absolute bottom-6 right-6 z-20 w-56 rounded-2xl overflow-hidden border border-white/5 shadow-2xl bg-black/60 backdrop-blur-md">
        <div className="bg-white/5 px-3 py-1.5 text-[9px] text-gray-400 uppercase tracking-widest flex justify-between items-center border-b border-white/5">
          <span>Live Telemetry</span>
          <span className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-500 animate-ping"></span>
            Sync
          </span>
        </div>
        <div className="h-40 relative bg-black/40">
          <LivePreview />
        </div>
      </div>

      {/* 5. Bottom Center: Minimal Dock */}
      <div className={`absolute bottom-8 left-1/2 -translate-x-1/2 z-20 flex flex-col items-center gap-4 transition-all duration-500 ${showControls ? 'translate-y-0 opacity-100' : 'translate-y-32 opacity-0'}`}>

        {/* Real-time Status Message Bar */}
        <div className={`transition-all duration-500 transform ${statusMessage ? 'translate-y-0 opacity-100 scale-100' : 'translate-y-4 opacity-0 scale-95'}`}>
          {statusMessage && (
            <div className={`px-8 py-3 rounded-full glass-morphism border border-white/10 shadow-[0_0_30px_rgba(0,0,0,0.5)] flex items-center gap-4 min-w-[300px] justify-center`}>
              <div className={`w-2 h-2 rounded-full animate-pulse ${statusMessage.type === 'action' ? 'bg-cyan-400' : statusMessage.type === 'chat' ? 'bg-purple-400' : 'bg-green-400'}`}></div>
              <span className="text-sm font-light tracking-[0.2em] text-white uppercase whitespace-nowrap">
                {statusMessage.text}
              </span>
              <div className="flex gap-0.5">
                <div className="w-1 h-1 bg-white/20"></div>
                <div className="w-1 h-3 bg-white/40"></div>
              </div>
            </div>
          )}
        </div>

        {/* Quick Actions Tooltip-style bar */}
        <div className="flex gap-2 mb-2 p-1 bg-black/60 rounded-full border border-white/5 backdrop-blur-sm shadow-lg">
          <button onClick={() => handleAction({ intent: 'ZOOM_IN' })} className="p-2 hover:text-cyan-400 transition-colors"><ZoomIn size={16} /></button>
          <button onClick={() => handleAction({ intent: 'ZOOM_OUT' })} className="p-2 hover:text-cyan-400 transition-colors"><ZoomOut size={16} /></button>
          <button onClick={() => handleAction({ intent: 'RESET_VIEW' })} className="p-2 hover:text-cyan-400 transition-colors"><RotateCcw size={16} /></button>
          <button onClick={() => { }} className="p-2 hover:text-cyan-400 transition-colors"><Maximize2 size={16} /></button>
        </div>

        <div className="glass-morphism px-6 py-4 rounded-3xl flex items-center gap-6 border border-white/10 bg-black/20 backdrop-blur-3xl shadow-[0_20px_50px_rgba(0,0,0,0.5)]">
          <button onClick={showPrev} className="p-3 hover:bg-white/5 rounded-full text-white/40 hover:text-cyan-400 transition-all">
            <ChevronLeft size={24} />
          </button>

          <div className="flex gap-3 px-2">
            <label className="cursor-pointer relative group w-14 h-14 rounded-2xl border border-white/10 hover:border-cyan-500/50 flex flex-col items-center justify-center transition-all bg-white/5 hover:bg-cyan-500/5">
              <Upload size={18} className="text-gray-500 group-hover:text-cyan-400" />
              <input type="file" accept="image/png,image/jpeg" className="hidden" onChange={(e) => { if (e.target.files?.[0]) uploadFile(e.target.files[0]); }} />
            </label>

            <div className="w-px h-14 bg-white/5 mx-2"></div>

            <div className="flex gap-3 max-w-[500px] overflow-x-auto no-scrollbar scroll-smooth">
              {images.map((img, idx) => {
                const name = getName(img);
                const isActive = selectedImage === img;
                return (
                  <button
                    key={idx}
                    onClick={() => { setSelectedImage(img); setTransform({ scale: 1, x: 0, y: 0 }); }}
                    className={`relative w-14 h-14 rounded-2xl overflow-hidden transition-all duration-300 border ${isActive ? 'border-cyan-500 scale-110 shadow-[0_0_20px_rgba(34,211,238,0.3)] z-10' : 'border-white/5 opacity-40 hover:opacity-100'}`}
                  >
                    <img src={`/samples/${name}`} alt={name} className="w-full h-full object-cover" />
                  </button>
                )
              })}
            </div>
          </div>

          <button onClick={showNext} className="p-3 hover:bg-white/5 rounded-full text-white/40 hover:text-cyan-400 transition-all">
            <ChevronRight size={24} />
          </button>
        </div>
      </div>

      {/* Help Modal */}
      {showHelp && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 backdrop-blur-xl p-4">
          <div className="glass-morphism border border-white/10 p-10 rounded-[2rem] max-w-2xl w-full shadow-[0_0_100px_rgba(34,211,238,0.1)]">
            <div className="flex items-center justify-between mb-8">
              <h2 className="text-3xl font-light tracking-[0.3em] uppercase text-white">System Commands</h2>
              <button onClick={() => setShowHelp(false)} className="px-6 py-2 rounded-full border border-white/10 hover:bg-white/5 text-sm transition-all">Dismiss</button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-12 text-sm">
              <div className="space-y-6">
                <h3 className="text-cyan-400 font-bold uppercase tracking-widest flex items-center gap-3">
                  <span className="w-8 h-px bg-cyan-400"></span> Voice
                </h3>
                <ul className="space-y-4 text-gray-400 font-light">
                  <li className="flex justify-between"><span>"Zoom in here"</span> <span className="text-[10px] text-cyan-500/50">Eyes + Voice</span></li>
                  <li className="flex justify-between"><span>"Open patient file"</span> <span className="text-[10px] text-cyan-500/50">Context Selection</span></li>
                  <li className="flex justify-between"><span>"Next scan"</span> <span className="text-[10px] text-cyan-500/50">Navigation</span></li>
                </ul>
              </div>

              <div className="space-y-6">
                <h3 className="text-cyan-400 font-bold uppercase tracking-widest flex items-center gap-3">
                  <span className="w-8 h-px bg-cyan-400"></span> Gestures
                </h3>
                <ul className="space-y-4 text-gray-400 font-light">
                  <li className="flex justify-between"><span>Pinch Fingers</span> <span className="text-[10px] text-cyan-500/50">Dynamic Zoom</span></li>
                  <li className="flex justify-between"><span>Air Swipe</span> <span className="text-[10px] text-cyan-500/50">File Flip</span></li>
                  <li className="flex justify-between"><span>Hold Palm</span> <span className="text-[10px] text-cyan-500/50">Freeze View</span></li>
                </ul>
              </div>
            </div>

            <div className="mt-12 pt-8 border-t border-white/5 text-center text-[10px] text-gray-600 tracking-[0.4em] uppercase">
              Operational Interface v2.0.4 • Touchless Protocol v4
            </div>
          </div>
        </div>
      )}

      {/* Styles for glassmorphism */}
      <style dangerouslySetInnerHTML={{
        __html: `
        .glass-morphism {
          background: rgba(255, 255, 255, 0.03);
          backdrop-filter: blur(20px);
        }
        .no-scrollbar::-webkit-scrollbar { display: none; }
        .no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
      `}} />
    </div>
  );
};

export default Dashboard;
