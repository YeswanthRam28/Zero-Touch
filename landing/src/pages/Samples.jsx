import React from 'react';
import { useEffect, useState } from 'react';

const Samples = () => {
  const [samples, setSamples] = useState([]);

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch('/samples');
        if (res.ok) setSamples(await res.json());
      } catch (e) {
        // ignore
      }
    })();
  }, []);

  return (
    <div className="min-h-screen p-6">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-2xl font-bold mb-4">Uploaded Samples</h1>
        {samples.length === 0 ? (
          <div className="text-gray-400">No samples uploaded yet.</div>
        ) : (
          <div className="grid grid-cols-3 gap-4">
            {samples.map((s) => (
              <div key={s.filename} className="bg-black/10 p-2 rounded">
                <img src={`/samples/${s.filename}`} alt={s.filename} className="w-full h-40 object-cover rounded" />
                <div className="mt-2 text-xs text-gray-300 truncate">{s.filename}</div>
                <div className="mt-1 text-xs text-gray-400">{s.uploaded_at} • {s.size ? Math.round(s.size/1024) + ' KB' : ''}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Samples;
