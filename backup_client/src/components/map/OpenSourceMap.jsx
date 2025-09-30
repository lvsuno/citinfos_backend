import React, { useEffect, useRef, useState } from 'react';

const OpenSourceMap = ({
  center = [46.2044, 6.1432],
  zoom = 6,
  height = '400px',
  historicalEvents = [],
  isEditorMode = false
}) => {
  const mapRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const [isLoaded, setIsLoaded] = useState(false);
  const [error, setError] = useState(null);
  const [markers, setMarkers] = useState([]);

  useEffect(() => {
    // Clean up previous map
    if (mapInstanceRef.current) {
      mapInstanceRef.current.remove();
      mapInstanceRef.current = null;
    }

    const initializeMap = async () => {
      try {
        // Load Leaflet CSS if not already loaded
        if (!document.querySelector('link[href*="leaflet.css"]')) {
          const link = document.createElement('link');
          link.rel = 'stylesheet';
          link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
          link.integrity = 'sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=';
          link.crossOrigin = '';
          document.head.appendChild(link);
        }

        // Load Leaflet JS if not already loaded
        if (!window.L) {
          await new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
            script.integrity = 'sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=';
            script.crossOrigin = '';
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
          });
        }

        // Wait a bit for DOM to be ready
        await new Promise(resolve => setTimeout(resolve, 100));

        if (!mapRef.current) {
          throw new Error('Map container not found');
        }

        // Initialize map
        const map = window.L.map(mapRef.current, {
          center: center,
          zoom: zoom,
          zoomControl: true,
          attributionControl: true
        });

        // Add tile layer with multiple fallback options
        const tileLayer = window.L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
          attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
          maxZoom: 19,
          subdomains: ['a', 'b', 'c']
        });

        tileLayer.addTo(map);

        // Fix default marker icons
        delete window.L.Icon.Default.prototype._getIconUrl;
        window.L.Icon.Default.mergeOptions({
          iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
          iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
          shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
        });

        // Add historical events as markers
        const newMarkers = [];
        historicalEvents.forEach(event => {
          if (event.lat && event.lon) {
            const marker = window.L.marker([event.lat, event.lon]);

            const popupContent = `
              <div style="min-width: 200px;">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                  <span style="font-size: 18px;">${event.icon || '📍'}</span>
                  <strong>${event.title}</strong>
                </div>
                <p style="margin: 4px 0; color: #666; font-size: 12px;">
                  ${event.year} ${event.isBC ? 'BC' : 'AD'}
                </p>
                <p style="margin: 4px 0; font-size: 14px;">${event.description}</p>
                <p style="margin: 4px 0 0 0; color: #999; font-size: 11px;">
                  Category: ${event.category}
                </p>
              </div>
            `;

            marker.bindPopup(popupContent);
            marker.addTo(map);
            newMarkers.push(marker);
          }
        });

        setMarkers(newMarkers);

        // Add click handler for editor mode
        if (isEditorMode) {
          map.on('click', (e) => {
            const marker = window.L.marker([e.latlng.lat, e.latlng.lng]);
            marker.bindPopup(`
              <div>
                <strong>New Marker</strong><br/>
                Lat: ${e.latlng.lat.toFixed(6)}<br/>
                Lng: ${e.latlng.lng.toFixed(6)}
              </div>
            `);
            marker.addTo(map);
            setMarkers(prev => [...prev, marker]);
          });
        }

        mapInstanceRef.current = map;
        setIsLoaded(true);
        setError(null);

        // Handle tile loading errors
        tileLayer.on('tileerror', (e) => {
          console.warn('Tile loading error:', e);
        });

        console.log('OpenStreetMap initialized successfully');

      } catch (err) {
        console.error('Map initialization error:', err);
        setError(err.message);
        setIsLoaded(false);
      }
    };

    initializeMap();

    // Cleanup on unmount
    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, [center, zoom, historicalEvents, isEditorMode]);

  if (error) {
    return (
      <div
        className="flex items-center justify-center bg-red-50 border border-red-200 rounded-lg"
        style={{ height }}
      >
        <div className="text-center text-red-600 p-4">
          <div className="text-4xl mb-2">🗺️</div>
          <div className="font-semibold mb-1">Map Error</div>
          <div className="text-sm">{error}</div>
          <div className="text-xs mt-2 text-gray-500">
            Using OpenStreetMap tiles
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="relative w-full" style={{ height }}>
      <div
        ref={mapRef}
        className="w-full h-full rounded-lg"
        style={{ minHeight: '300px' }}
      />

      {/* Loading indicator */}
      {!isLoaded && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-100 rounded-lg">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-2"></div>
            <div className="text-sm text-gray-600">Loading OpenStreetMap...</div>
          </div>
        </div>
      )}

      {/* Map info overlay */}
      {isLoaded && (
        <div className="absolute top-2 right-2 bg-white bg-opacity-90 rounded px-2 py-1 text-xs text-gray-600 shadow">
          OSM • {markers.length} markers
        </div>
      )}
    </div>
  );
};

export default OpenSourceMap;