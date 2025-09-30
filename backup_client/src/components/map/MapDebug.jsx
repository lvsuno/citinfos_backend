import React, { useEffect, useRef, useState } from 'react';

const MapDebug = () => {
  const mapRef = useRef(null);
  const [logs, setLogs] = useState([]);
  const [leafletLoaded, setLeafletLoaded] = useState(false);

  const addLog = (message) => {
    const timestamp = new Date().toLocaleTimeString();
    setLogs(prev => [...prev, `${timestamp}: ${message}`]);
    console.log(`MapDebug: ${message}`);
  };

  useEffect(() => {
    addLog('Starting map initialization...');

    const initMap = async () => {
      try {
        // Check if container exists
        if (!mapRef.current) {
          addLog('ERROR: Map container not found');
          return;
        }
        addLog('✓ Map container found');

        // Check container dimensions
        const rect = mapRef.current.getBoundingClientRect();
        addLog(`Container size: ${rect.width}x${rect.height}`);

        if (rect.width === 0 || rect.height === 0) {
          addLog('ERROR: Container has zero dimensions');
          return;
        }

        // Load Leaflet CSS
        addLog('Loading Leaflet CSS...');
        if (!document.querySelector('link[href*="leaflet.css"]')) {
          const link = document.createElement('link');
          link.rel = 'stylesheet';
          link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
          document.head.appendChild(link);
          addLog('✓ Leaflet CSS added');
        } else {
          addLog('✓ Leaflet CSS already loaded');
        }

        // Load Leaflet JS
        addLog('Loading Leaflet JS...');
        if (!window.L) {
          await new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
            script.onload = () => {
              addLog('✓ Leaflet JS loaded successfully');
              resolve();
            };
            script.onerror = () => {
              addLog('ERROR: Failed to load Leaflet JS');
              reject(new Error('Leaflet script failed to load'));
            };
            document.head.appendChild(script);
          });
        } else {
          addLog('✓ Leaflet JS already available');
        }

        setLeafletLoaded(true);

        // Wait a bit for everything to be ready
        addLog('Waiting for DOM ready...');
        await new Promise(resolve => setTimeout(resolve, 200));

        // Check if Leaflet is actually available
        if (!window.L || !window.L.map) {
          addLog('ERROR: Leaflet L.map not available');
          return;
        }
        addLog('✓ Leaflet L.map available');

        // Try to create map
        addLog('Creating Leaflet map instance...');
        const map = window.L.map(mapRef.current, {
          center: [46.2044, 6.1432],
          zoom: 8,
          zoomControl: true
        });
        addLog('✓ Map instance created');

        // Add tile layer
        addLog('Adding tile layer...');
        const tileLayer = window.L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
          attribution: '© OpenStreetMap contributors',
          maxZoom: 18
        });

        tileLayer.on('loading', () => {
          addLog('Tiles loading...');
        });

        tileLayer.on('load', () => {
          addLog('✓ Tiles loaded successfully');
        });

        tileLayer.on('tileerror', (e) => {
          addLog(`ERROR: Tile load failed - ${e.error}`);
        });

        tileLayer.addTo(map);
        addLog('✓ Tile layer added to map');

        // Add a test marker
        const marker = window.L.marker([46.2044, 6.1432]).addTo(map);
        marker.bindPopup('Test marker - if you see this, the map is working!').openPopup();
        addLog('✓ Test marker added');

        addLog('🎉 Map initialization complete!');

      } catch (error) {
        addLog(`ERROR: ${error.message}`);
        console.error('Map initialization error:', error);
      }
    };

    initMap();
  }, []);

  return (
    <div className="w-full h-full flex">
      {/* Map container */}
      <div className="flex-1 relative">
        <div
          ref={mapRef}
          className="w-full h-full bg-gray-200"
          style={{ minHeight: '400px' }}
        />

        {/* Status overlay on map */}
        <div className="absolute top-2 left-2 bg-white p-2 rounded shadow text-xs max-w-xs">
          <div className="font-bold mb-1">Map Status:</div>
          <div className={leafletLoaded ? 'text-green-600' : 'text-orange-600'}>
            {leafletLoaded ? '✓ Leaflet Loaded' : '⏳ Loading Leaflet...'}
          </div>
        </div>
      </div>

      {/* Debug log panel */}
      <div className="w-80 bg-gray-900 text-green-400 p-4 font-mono text-xs overflow-y-auto">
        <div className="font-bold text-white mb-2">Debug Log:</div>
        {logs.map((log, index) => (
          <div
            key={index}
            className={log.includes('ERROR') ? 'text-red-400' :
                     log.includes('✓') ? 'text-green-400' :
                     log.includes('🎉') ? 'text-yellow-400' : 'text-gray-300'}
          >
            {log}
          </div>
        ))}
        {logs.length === 0 && (
          <div className="text-gray-500">No logs yet...</div>
        )}
      </div>
    </div>
  );
};

export default MapDebug;