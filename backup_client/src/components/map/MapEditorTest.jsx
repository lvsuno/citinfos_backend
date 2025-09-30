import React, { useEffect, useRef, useState } from 'react';

const MapEditorTest = () => {
  const mapRef = useRef(null);
  const [status, setStatus] = useState('Initializing...');
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadMap = async () => {
      try {
        setStatus('Loading Leaflet CSS...');

        // Load Leaflet CSS
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
        document.head.appendChild(link);

        setStatus('Loading Leaflet JS...');

        // Load Leaflet JS
        const script = document.createElement('script');
        script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';

        script.onload = () => {
          setStatus('Initializing map...');

          try {
            // Create map
            const map = window.L.map(mapRef.current, {
              center: [46.2044, 6.1432], // Geneva
              zoom: 6
            });

            setStatus('Adding tile layer...');

            // Add OpenStreetMap tiles
            window.L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
              attribution: '© OpenStreetMap contributors',
              maxZoom: 19
            }).addTo(map);

            // Add a test marker
            window.L.marker([46.2044, 6.1432])
              .addTo(map)
              .bindPopup('Test marker in Geneva')
              .openPopup();

            setStatus('Map loaded successfully!');
          } catch (mapError) {
            console.error('Map initialization error:', mapError);
            setError(`Map error: ${mapError.message}`);
            setStatus('Map initialization failed');
          }
        };

        script.onerror = () => {
          setError('Failed to load Leaflet library');
          setStatus('Library load failed');
        };

        document.head.appendChild(script);

      } catch (err) {
        console.error('Setup error:', err);
        setError(`Setup error: ${err.message}`);
        setStatus('Setup failed');
      }
    };

    loadMap();
  }, []);

  return (
    <div className="w-full h-96 bg-gray-100 relative">
      <div
        ref={mapRef}
        className="w-full h-full"
        style={{ minHeight: '400px' }}
      />

      {/* Status overlay */}
      <div className="absolute top-4 left-4 bg-white p-3 rounded shadow-lg border z-[1000]">
        <div className="text-sm">
          <div className="font-semibold mb-1">Map Status:</div>
          <div className={error ? 'text-red-600' : 'text-blue-600'}>
            {status}
          </div>
          {error && (
            <div className="text-red-600 text-xs mt-1">
              Error: {error}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MapEditorTest;