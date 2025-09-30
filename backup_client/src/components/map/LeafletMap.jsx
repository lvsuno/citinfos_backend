import React, { useEffect, useRef, useState, useImperativeHandle, forwardRef } from 'react';

// Load Leaflet CSS and JS dynamically from CDN
const loadLeaflet = async () => {
  // Load CSS
  if (!document.querySelector('link[href*="leaflet.css"]')) {
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
    link.integrity = 'sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=';
    link.crossOrigin = '';
    document.head.appendChild(link);
  }

  // Load JS if not already loaded
  if (!window.L) {
    return new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
      script.integrity = 'sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=';
      script.crossOrigin = '';
      script.onload = () => {
        // Fix default marker icons
        delete window.L.Icon.Default.prototype._getIconUrl;
        window.L.Icon.Default.mergeOptions({
          iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
          iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
          shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
        });
        resolve();
      };
      script.onerror = reject;
      document.head.appendChild(script);
    });
  }

  return Promise.resolve();
};

const LeafletMap = forwardRef(({
  center = [46.2044, 6.1432],
  zoom = 6,
  height = '400px',
  historicalEvents = [],
  isEditorMode = false,
  onDrawingChange = null
}, ref) => {
  const mapRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const [isLoaded, setIsLoaded] = useState(false);
  const [error, setError] = useState(null);
  const [markers, setMarkers] = useState([]);
  const [tileLayer, setTileLayer] = useState('osm');

  // Expose methods to parent component via ref
  useImperativeHandle(ref, () => ({
    flyTo: (lat, lon, zoomLevel = 10) => {
      if (mapInstanceRef.current && window.L) {
        console.log(`LeafletMap: Flying to ${lat}, ${lon} at zoom ${zoomLevel}`);
        mapInstanceRef.current.flyTo([lat, lon], zoomLevel, {
          duration: 2.0,
          easeLinearity: 0.5
        });
        return true;
      } else {
        console.warn('LeafletMap: Cannot fly to location - map not initialized');
        return false;
      }
    },
    setView: (lat, lon, zoomLevel = 10) => {
      if (mapInstanceRef.current && window.L) {
        mapInstanceRef.current.setView([lat, lon], zoomLevel);
        return true;
      }
      return false;
    },
    invalidateSize: () => {
      if (mapInstanceRef.current && window.L) {
        mapInstanceRef.current.invalidateSize();
        console.log('LeafletMap: Size invalidated');
        return true;
      }
      return false;
    },
    getMap: () => mapInstanceRef.current,
    isReady: () => isLoaded && mapInstanceRef.current !== null
  }), [isLoaded]);

  const tileProviders = {
    osm: {
      url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
      attribution: '© OpenStreetMap contributors',
      name: 'OpenStreetMap'
    },
    cartodb: {
      url: 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
      attribution: '© OpenStreetMap © CartoDB',
      name: 'CartoDB Light'
    },
    satellite: {
      url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      attribution: '© Esri',
      name: 'Satellite'
    }
  };

  useEffect(() => {
    if (!mapRef.current) return;

    const initializeMap = async () => {
      try {
        setIsLoaded(false);
        setError(null);

        // Load Leaflet dynamically
        await loadLeaflet();

        // Wait for DOM to be fully ready
        await new Promise(resolve => setTimeout(resolve, 100));

        // Double-check container exists and has dimensions
        if (!mapRef.current) {
          throw new Error('Map container not found');
        }

        const rect = mapRef.current.getBoundingClientRect();
        if (rect.width === 0 || rect.height === 0) {
          throw new Error('Map container has no dimensions');
        }

        // Clean up previous map
        if (mapInstanceRef.current) {
          try {
            mapInstanceRef.current.remove();
          } catch (e) {
            console.warn('Error removing previous map:', e);
          }
          mapInstanceRef.current = null;
        }

        // Clear any existing map state
        if (mapRef.current._leaflet_id) {
          delete mapRef.current._leaflet_id;
        }

        // Create map using window.L with error handling
        const map = window.L.map(mapRef.current, {
          center: center,
          zoom: zoom,
          zoomControl: true,
          attributionControl: true,
          scrollWheelZoom: true,
          doubleClickZoom: true,
          dragging: true,
          fadeAnimation: false,
          zoomAnimation: false,
          markerZoomAnimation: false
        });

        // Add tile layer
        const currentProvider = tileProviders[tileLayer];
        const tiles = window.L.tileLayer(currentProvider.url, {
          attribution: currentProvider.attribution,
          maxZoom: 18,
          minZoom: 2,
          errorTileUrl: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=='
        });

        tiles.addTo(map);

        // Add historical events as markers
        const newMarkers = [];
        if (historicalEvents && historicalEvents.length > 0) {
          historicalEvents.forEach(event => {
            if (event.lat && event.lon) {
              try {
                const marker = window.L.marker([event.lat, event.lon]);

                const popupContent = `
                  <div style="min-width: 200px; font-family: system-ui;">
                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                      <span style="font-size: 18px;">${event.icon || '📍'}</span>
                      <strong style="color: #1f2937;">${event.title}</strong>
                    </div>
                    <p style="margin: 4px 0; color: #6b7280; font-size: 12px;">
                      ${event.year} ${event.isBC ? 'BC' : 'AD'}
                    </p>
                    <p style="margin: 4px 0; color: #374151; font-size: 14px;">${event.description}</p>
                    <p style="margin: 8px 0 0 0; color: #9ca3af; font-size: 11px; padding: 4px; background: #f3f4f6; border-radius: 4px;">
                      Category: ${event.category}
                    </p>
                  </div>
                `;

                marker.bindPopup(popupContent, {
                  maxWidth: 300,
                  className: 'custom-popup'
                });
                marker.addTo(map);
                newMarkers.push(marker);
              } catch (markerError) {
                console.warn('Error adding marker for event:', event.title, markerError);
              }
            }
          });
        }

        // Add click handler for editor mode
        if (isEditorMode) {
          map.on('click', (e) => {
            try {
              const marker = window.L.marker([e.latlng.lat, e.latlng.lng]);
              const popupContent = `
                <div style="font-family: system-ui;">
                  <strong>New Marker</strong><br/>
                  <small>Lat: ${e.latlng.lat.toFixed(6)}<br/>
                  Lng: ${e.latlng.lng.toFixed(6)}</small>
                </div>
              `;
              marker.bindPopup(popupContent);
              marker.addTo(map);

              const newItem = {
                id: Date.now(),
                type: 'marker',
                lat: e.latlng.lat,
                lng: e.latlng.lng
              };

              setMarkers(prev => [...prev, marker]);

              if (onDrawingChange) {
                onDrawingChange({
                  type: 'created',
                  data: newItem
                });
              }
            } catch (clickError) {
              console.warn('Error handling map click:', clickError);
            }
          });
        }

        setMarkers(newMarkers);
        mapInstanceRef.current = map;
        setIsLoaded(true);

        console.log('Leaflet map initialized successfully from CDN with', newMarkers.length, 'markers');

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
        try {
          mapInstanceRef.current.remove();
        } catch (e) {
          console.warn('Error during map cleanup:', e);
        } finally {
          mapInstanceRef.current = null;
        }
      }

      // Clear any remaining Leaflet state
      if (mapRef.current && mapRef.current._leaflet_id) {
        delete mapRef.current._leaflet_id;
      }
    };
  }, []); // Only run once on mount

  // Handle center/zoom updates separately without re-initializing the entire map
  useEffect(() => {
    if (mapInstanceRef.current && window.L && isLoaded) {
      mapInstanceRef.current.setView(center, zoom);
    }
  }, [center, zoom, isLoaded]);

  // Handle historical events updates separately
  useEffect(() => {
    if (mapInstanceRef.current && window.L && isLoaded) {
      // Clear existing markers
      markers.forEach(marker => {
        if (marker && marker.remove) {
          marker.remove();
        }
      });

      // Add new markers
      const newMarkers = historicalEvents.map(event => {
        const marker = window.L.marker([event.lat, event.lon])
          .addTo(mapInstanceRef.current);

        if (event.title) {
          marker.bindPopup(`
            <div class="text-sm">
              <strong>${event.icon} ${event.title}</strong><br>
              <span class="text-gray-600">${event.year} ${event.isBC ? 'BC' : 'AD'}</span>
            </div>
          `);
        }

        return marker;
      });

      setMarkers(newMarkers);
    }
  }, [historicalEvents, isLoaded]);

  // Handle editor mode changes separately
  useEffect(() => {
    // Editor mode changes don't require full re-initialization
    // Just update click handlers if needed
  }, [isEditorMode]);

  // Handle tile layer changes separately
  useEffect(() => {
    if (mapInstanceRef.current && window.L && isLoaded) {
      // Remove existing tile layers and add new one
      mapInstanceRef.current.eachLayer((layer) => {
        if (layer instanceof window.L.TileLayer) {
          mapInstanceRef.current.removeLayer(layer);
        }
      });

      // Add new tile layer
      const provider = tileProviders[tileLayer];
      if (provider) {
        const newTileLayer = window.L.tileLayer(provider.url, {
          attribution: provider.attribution,
          maxZoom: 18,
          tileSize: 256
        });
        newTileLayer.addTo(mapInstanceRef.current);
      }
    }
  }, [tileLayer, isLoaded]);

  // Handle tile layer change
  const handleTileLayerChange = (newLayer) => {
    setTileLayer(newLayer);
  };

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
            Using Leaflet from CDN
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="relative w-full" style={{ height }}>
      {/* Map container */}
      <div
        ref={mapRef}
        className="w-full h-full rounded-lg"
        style={{ minHeight: '300px' }}
      />

      {/* Loading overlay */}
      {!isLoaded && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-100 rounded-lg z-[1000]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-2"></div>
            <div className="text-sm text-gray-600">Loading Leaflet from CDN...</div>
          </div>
        </div>
      )}

      {/* Controls */}
      {isLoaded && (
        <div className="absolute top-2 left-2 z-[1000] space-y-2">
          {/* Tile Layer Selector */}
          <div className="bg-white rounded shadow-lg p-2">
            <select
              value={tileLayer}
              onChange={(e) => handleTileLayerChange(e.target.value)}
              className="text-xs border rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {Object.entries(tileProviders).map(([key, provider]) => (
                <option key={key} value={key}>{provider.name}</option>
              ))}
            </select>
          </div>

          {/* Map Info */}
          <div className="bg-white bg-opacity-90 rounded px-2 py-1 text-xs text-gray-600 shadow">
            Leaflet CDN • {markers.length} markers
            {isEditorMode && <div className="text-green-600">✏️ Editor Mode</div>}
          </div>
        </div>
      )}

      {/* Editor Instructions */}
      {isEditorMode && isLoaded && (
        <div className="absolute bottom-2 left-2 z-[1000]">
          <div className="bg-blue-50 border border-blue-200 rounded px-3 py-2 text-xs text-blue-700">
            💡 Click anywhere on the map to add markers
          </div>
        </div>
      )}
    </div>
  );
});

LeafletMap.displayName = 'LeafletMap';

export default LeafletMap;