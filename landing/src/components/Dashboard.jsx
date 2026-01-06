import React, { useEffect, useState, useRef } from 'react';
import LivePreview from './LivePreview';
import { fetchFusion, mockFusion } from '../services/fusionClient';

const Dashboard = ({ onBack }) => {
  const [fusion, setFusion] = useState(null);

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

  const uploadFile = async (file) => {
    const fd = new FormData();
    fd.append('file', file);
    try {
      const res = await fetch('/upload', { method: 'POST', body: fd });
      if (!res.ok) throw new Error('Upload failed');
      const j = await res.json();
      setImages((s) => [j.saved, ...s]);
      // auto-load uploaded image into viewer
      setSelectedImage(j.saved);
    } catch (e) {
      console.error(e);
      alert('Upload failed: ' + e.message);
    }
  };

  useEffect(() => {
    // Optionally load existing samples on mount
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

  // Modal / fullscreen viewer state + accessibility helpers
  const [showModal, setShowModal] = useState(false);
  const [modalIndex, setModalIndex] = useState(0);
  const lastFocused = useRef(null);
  const closeButtonRef = useRef(null);

  const openModalAt = (index) => {
    lastFocused.current = document.activeElement;
    setModalIndex(index);
    setShowModal(true);
    setTimeout(() => closeButtonRef.current?.focus(), 0);
  };

  const closeModal = () => {
    setShowModal(false);
    setTimeout(() => lastFocused.current?.focus(), 0);
  };

  const showPrev = () => {
    if (!images.length) return;
    const i = (modalIndex - 1 + images.length) % images.length;
    setModalIndex(i);
    setSelectedImage(images[i]);
  };
  const showNext = () => {
    if (!images.length) return;
    const i = (modalIndex + 1) % images.length;
    setModalIndex(i);
    setSelectedImage(images[i]);
  };

  useEffect(() => {
    if (!showModal) return;

    // Lock body scroll while modal is open
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';

    // Focus trap: keep tab inside modal
    const onKey = (e) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        closeModal();
        return;
      }
      if (e.key === 'ArrowLeft') {
        e.preventDefault();
        showPrev();
        return;
      }
      if (e.key === 'ArrowRight') {
        e.preventDefault();
        showNext();
        return;
      }

      if (e.key === 'Tab') {
        const modal = document.querySelector('[role="dialog"]');
        if (!modal) return;
        const focusable = Array.from(modal.querySelectorAll('a[href], button:not([disabled]), textarea, input, select, [tabindex]:not([tabindex="-1"])')).filter(Boolean);
        if (focusable.length === 0) return;
        const idx = focusable.indexOf(document.activeElement);
        if (e.shiftKey && idx === 0) {
          e.preventDefault();
          focusable[focusable.length - 1].focus();
        } else if (!e.shiftKey && idx === focusable.length - 1) {
          e.preventDefault();
          focusable[0].focus();
        }
      }
    };

    window.addEventListener('keydown', onKey);
    return () => {
      window.removeEventListener('keydown', onKey);
      document.body.style.overflow = prevOverflow;
    };
  }, [showModal, modalIndex, images]);

  // Global F-key shortcut to open fullscreen viewer when images exist
  useEffect(() => {
    const onGlobalKey = (e) => {
      if (e.key === 'f' || e.key === 'F') {
        // ignore when typing in inputs
        const tag = document.activeElement?.tagName?.toLowerCase();
        if (tag === 'input' || tag === 'textarea' || document.activeElement?.isContentEditable) return;
        if (!showModal && images.length > 0) {
          const idx = images.indexOf(selectedImage || images[0]);
          openModalAt(idx < 0 ? 0 : idx);
        }
      }
    };
    window.addEventListener('keydown', onGlobalKey);
    return () => window.removeEventListener('keydown', onGlobalKey);
  }, [images, selectedImage, showModal]);

  return (
    <div className="h-screen p-6 overflow-hidden" aria-hidden={showModal}>
      <div className="max-w-6xl mx-auto h-full">
        <div className="flex items-center justify-between mb-4">
          <div>
            <button onClick={onBack} className="btn-secondary">← Back</button>
          </div>
          <div className="flex items-center gap-3">
            <button onClick={() => setShowHelp(true)} className="btn-secondary">Help</button>
            <button onClick={() => window.location.hash = '/samples'} className="btn-secondary">Samples</button>
            <button onClick={() => window.location.hash = '/viewer'} className="btn-secondary">Viewer</button>
          </div>
        </div>

        <h1 className="text-3xl font-bold mb-4">Surgical Interface (Mock)</h1>
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 h-full items-stretch">
          <div className="glass p-4 rounded-lg lg:col-span-3 h-full flex flex-col">
            <div className="flex-1 bg-black/20 rounded-md flex items-center justify-center relative overflow-hidden">
              {selectedImage ? (
                <button type="button" onClick={() => openModalAt(images.indexOf(selectedImage))} className="w-full h-full p-2 flex items-center justify-center focus:outline-none">
                  <img src={`/samples/${selectedImage}`} alt={`Selected: ${selectedImage}`} className="max-h-full max-w-full object-contain rounded" />
                </button>
              ) : (
                <div className="text-gray-300">Medical image / viewer placeholder</div>
              )}

              {images.length > 0 && (
                <div className="absolute top-3 right-3 flex gap-2">
                  <button type="button" onClick={() => openModalAt(images.indexOf(selectedImage || images[0]))} className="btn-primary">Open fullscreen</button>
                </div>
              )}
            </div>

            <div className="mt-4 text-sm text-gray-300" aria-live="polite">Fusion action: <strong className="text-primary" aria-atomic="true">{fusion?.action ?? '—'}</strong></div>

            <div className="mt-6">
              <div className="text-sm text-gray-300 mb-2">Upload images</div>
              <input type="file" accept="image/png,image/jpeg" onChange={(e) => { if (e.target.files && e.target.files[0]) uploadFile(e.target.files[0]); }} />

              {images.length > 0 && (
                <div className="mt-4 grid grid-cols-3 gap-2">
                  {images.map((img, idx) => (
                    <button key={img} type="button" onClick={() => { setSelectedImage(img); setModalIndex(idx); }} aria-label={`Open ${img}`} aria-pressed={selectedImage === img} className={`bg-black/10 p-1 rounded cursor-pointer focus:outline-none ${selectedImage === img ? 'ring-2 ring-primary' : ''}`}>
                      <img src={`/samples/${img}`} alt={img} className="w-full h-24 object-cover rounded" />
                      <div className="text-xs text-gray-400 mt-1 truncate">{img}</div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="glass p-4 rounded-lg h-full flex flex-col">
            <div className="text-sm text-gray-300 mb-2">Live Inputs</div>
            <div className="flex-1 overflow-hidden">
              <LivePreview />
            </div>
          </div>
        </div>

        {/* Fullscreen modal viewer */}
        {showModal && (
          <div role="dialog" aria-modal="true" aria-label="Image viewer" className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4 transition-opacity duration-200 ease-out">
            <div className="relative max-w-[95vw] max-h-[95vh] w-full transform transition-transform duration-200 ease-out scale-100">
              <button ref={closeButtonRef} type="button" onClick={closeModal} className="absolute top-2 right-2 btn-secondary">Close</button>
              <button type="button" onClick={showPrev} aria-label="Previous" className="absolute left-2 top-1/2 transform -translate-y-1/2 btn-secondary">◀</button>
              <button type="button" onClick={showNext} aria-label="Next" className="absolute right-2 top-1/2 transform -translate-y-1/2 btn-secondary">▶</button>
              <div className="bg-black/20 rounded overflow-hidden flex items-center justify-center h-[80vh] p-4">
                <img src={`/samples/${images[modalIndex]}`} alt={images[modalIndex]} className="max-h-full max-w-full object-contain transition-transform duration-300 ease-out" />
              </div>
            </div>
          </div>
        )}
      </div>

      {showHelp && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
          <div className="bg-[#0b0b0b] p-6 rounded-lg max-w-2xl w-full">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold">Supported Commands & Interactions</h2>
              <button onClick={() => setShowHelp(false)} className="btn-secondary">Close</button>
            </div>

            <div className="text-sm text-gray-300">
              <h3 className="font-semibold mt-2">Voice (Whisper + Intent)</h3>
              <ul className="list-disc pl-5 mt-1">
                <li>Open patient file</li>
                <li>Open pre-op MRI / Show CT scan</li>
                <li>Next image / Previous image</li>
                <li>Zoom in / Zoom out / Reset view</li>
                <li>Highlight abnormalities / Analyze this region</li>
                <li>Compare with pre-op scan</li>
              </ul>

              <h3 className="font-semibold mt-3">Gestures (MediaPipe Hands)</h3>
              <ul className="list-disc pl-5 mt-1">
                <li>Pinch-in / Pinch-out → Zoom</li>
                <li>Swipe left / right → Prev / Next</li>
                <li>Open palm → Pause / Freeze view</li>
                <li>Point → Select ROI</li>
              </ul>

              <h3 className="font-semibold mt-3">Gaze</h3>
              <ul className="list-disc pl-5 mt-1">
                <li>Look at region → Set ROI</li>
                <li>Hold gaze 1–2s → Confirm selection</li>
                <li>Shift gaze → Move focus cursor</li>
              </ul>

              <h3 className="font-semibold mt-3">Multimodal Examples</h3>
              <ul className="list-disc pl-5 mt-1">
                <li>"Zoom here" + Look at region → Zoom into region</li>
                <li>"Highlight this" + Point → Highlight exact ROI</li>
                <li>"Compare this area" + Region → Side-by-side comparison</li>
              </ul>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};

export default Dashboard;
