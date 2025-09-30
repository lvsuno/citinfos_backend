import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
  GlobeAltIcon,
  MapIcon,
  PencilIcon,
  EyeIcon,
  TrashIcon,
  PlusIcon,
  MinusIcon,
  ArrowsPointingOutIcon,
  CogIcon,
} from '@heroicons/react/24/outline';

const MapEditorReal = ({
  isEditorMode = true,
  is3DMode = false,
  onModeChange,
  onDrawingChange,
  initialCenter = [46.2044, 6.1432], // Geneva coordinates
  initialZoom = 6,
  className = '',
  height = '500px',
  historicalEvents = []
}) => {
  const [mapMode, setMapMode] = useState(is3DMode ? '3D' : '2D');
  const [editorMode, setEditorMode] = useState(isEditorMode);
  const [drawnItems, setDrawnItems] = useState([]);
  const [selectedTileLayer, setSelectedTileLayer] = useState('openstreetmap');
  const [showStats, setShowStats] = useState(true);
  const [mapKey, setMapKey] = useState(0);
  const [leafletLoaded, setLeafletLoaded] = useState(false);
  const [leafletError, setLeafletError] = useState(null);
  const [mapInstance, setMapInstance] = useState(null);

  const mapContainerRef = useRef();

  // Tile layer options
  const tileLayerOptions = {
    openstreetmap: {
      url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
      attribution: '© OpenStreetMap contributors'
    },
    satellite: {
      url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      attribution: '© Esri'
    },
    terrain: {
      url: 'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
      attribution: '© OpenTopoMap'
    },
    dark: {
      url: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
      attribution: '© CartoDB'
    }
  };

  // Load Leaflet from CDN
  useEffect(() => {
    const loadLeafletFromCDN = async () => {
      try {
        // Load CSS
        if (!document.getElementById('leaflet-css')) {
          const css = document.createElement('link');
          css.id = 'leaflet-css';
          css.rel = 'stylesheet';
          css.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
          css.integrity = 'sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=';
          css.crossOrigin = '';
          document.head.appendChild(css);
        }

        // Load JavaScript
        if (!window.L) {
          const script = document.createElement('script');
          script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
          script.integrity = 'sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=';
          script.crossOrigin = '';

          await new Promise((resolve, reject) => {
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
          });
        }

        // Fix marker icons
        if (window.L) {
          delete window.L.Icon.Default.prototype._getIconUrl;
          window.L.Icon.Default.mergeOptions({
            iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
            iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
            shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
          });
        }

        setLeafletLoaded(true);
        setLeafletError(null);
      } catch (error) {
        console.error('Failed to load Leaflet:', error);
        setLeafletError(error.message);
        setLeafletLoaded(false);
      }
    };

    loadLeafletFromCDN();
  }, []);

  // Initialize map when Leaflet is loaded
  useEffect(() => {
    if (!leafletLoaded || !window.L || !mapContainerRef.current || mapInstance) {
      return;
    }

    try {
      // Create map
      const map = window.L.map(mapContainerRef.current).setView(initialCenter, initialZoom);

      // Add tile layer
      const tileLayer = window.L.tileLayer(
        tileLayerOptions[selectedTileLayer].url,
        {
          attribution: tileLayerOptions[selectedTileLayer].attribution,
          maxZoom: 18
        }
      ).addTo(map);

      // Add historical events as markers
      historicalEvents.forEach(event => {
        const marker = window.L.marker([event.lat, event.lon])
          .bindPopup(`
            <div class="p-2">
              <div class="flex items-center gap-2 mb-2">
                <span class="text-lg">${event.icon}</span>
                <strong>${event.title}</strong>
              </div>
              <p class="text-sm text-gray-600 mb-1">
                ${event.year} ${event.isBC ? 'BC' : 'AD'}
              </p>
              <p class="text-sm">${event.description}</p>
              <p class="text-xs text-gray-500 mt-1">
                Category: ${event.category}
              </p>
            </div>
          `)
          .addTo(map);
      });

      // Add click handler for drawing
      if (editorMode) {
        map.on('click', (e) => {
          const marker = window.L.marker([e.latlng.lat, e.latlng.lng])
            .bindPopup(`New marker at ${e.latlng.lat.toFixed(4)}, ${e.latlng.lng.toFixed(4)}`)
            .addTo(map);

          const newItem = {
            id: Date.now(),
            type: 'marker',
            lat: e.latlng.lat,
            lng: e.latlng.lng,
            marker: marker
          };

          const newItems = [...drawnItems, newItem];
          setDrawnItems(newItems);

          if (onDrawingChange) {
            onDrawingChange({
              type: 'created',
              data: newItem,
              allItems: newItems
            });
          }
        });
      }

      setMapInstance(map);

    } catch (error) {
      console.error('Error initializing map:', error);
      setLeafletError(error.message);
    }
  }, [leafletLoaded, selectedTileLayer, historicalEvents, editorMode]);

  // Update tile layer when selection changes
  useEffect(() => {
    if (mapInstance && window.L) {
      // Remove all tile layers
      mapInstance.eachLayer((layer) => {
        if (layer instanceof window.L.TileLayer) {
          mapInstance.removeLayer(layer);
        }
      });

      // Add new tile layer
      const tileLayer = window.L.tileLayer(
        tileLayerOptions[selectedTileLayer].url,
        {
          attribution: tileLayerOptions[selectedTileLayer].attribution,
          maxZoom: 18
        }
      ).addTo(mapInstance);
    }
  }, [selectedTileLayer, mapInstance]);

  // Mode switching
  const toggleMapMode = () => {
    const newMode = mapMode === '2D' ? '3D' : '2D';
    setMapMode(newMode);
    if (onModeChange) {
      onModeChange({ mapMode: newMode, editorMode });
    }
  };

  const toggleEditorMode = () => {
    const newEditorMode = !editorMode;
    setEditorMode(newEditorMode);
    if (onModeChange) {
      onModeChange({ mapMode, editorMode: newEditorMode });
    }
  };

  const clearAll = () => {
    if (mapInstance) {
      drawnItems.forEach(item => {
        if (item.marker) {
          mapInstance.removeLayer(item.marker);
        }
      });
    }
    setDrawnItems([]);
    if (onDrawingChange) {
      onDrawingChange({
        type: 'cleared',
        allItems: []
      });
    }
  };

  // Loading state
  if (!leafletLoaded && !leafletError) {
    return (
      <div className={`relative ${className}`} style={{ height }}>
        <div className="flex items-center justify-center h-full bg-gray-100">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading map...</p>
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (leafletError) {
    return (
      <div className={`relative ${className}`} style={{ height }}>
        <div className="flex items-center justify-center h-full bg-red-50">
          <div className="text-center text-red-600">
            <MapIcon className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p className="font-medium mb-2">Map failed to load</p>
            <p className="text-sm">{leafletError}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`relative ${className}`} style={{ height }}>
      {/* Control Panel */}
      <div className="absolute top-4 left-4 z-[1000] space-y-2">
        {/* Mode Controls */}
        <div className="bg-white rounded-lg shadow-lg p-2 flex space-x-2">
          <button
            onClick={toggleMapMode}
            className={`flex items-center px-3 py-2 rounded text-sm font-medium transition-colors ${
              mapMode === '2D'
                ? 'bg-blue-500 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            <MapIcon className="h-4 w-4 mr-2" />
            2D
          </button>
          <button
            onClick={toggleMapMode}
            className={`flex items-center px-3 py-2 rounded text-sm font-medium transition-colors ${
              mapMode === '3D'
                ? 'bg-blue-500 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            <GlobeAltIcon className="h-4 w-4 mr-2" />
            3D
          </button>
        </div>

        {/* Editor Mode Toggle */}
        <div className="bg-white rounded-lg shadow-lg p-2">
          <button
            onClick={toggleEditorMode}
            className={`flex items-center px-3 py-2 rounded text-sm font-medium transition-colors w-full ${
              editorMode
                ? 'bg-green-500 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {editorMode ? (
              <>
                <PencilIcon className="h-4 w-4 mr-2" />
                Editor Mode
              </>
            ) : (
              <>
                <EyeIcon className="h-4 w-4 mr-2" />
                Read Only
              </>
            )}
          </button>
        </div>

        {/* Drawing Tools */}
        {editorMode && (
          <div className="bg-white rounded-lg shadow-lg p-2">
            <button
              onClick={clearAll}
              className="flex items-center px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded transition-colors w-full"
            >
              <TrashIcon className="h-4 w-4 mr-2" />
              Clear All ({drawnItems.length})
            </button>
          </div>
        )}

        {/* Tile Layer Selector */}
        <div className="bg-white rounded-lg shadow-lg p-2">
          <select
            value={selectedTileLayer}
            onChange={(e) => setSelectedTileLayer(e.target.value)}
            className="w-full text-sm border rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="openstreetmap">Street Map</option>
            <option value="satellite">Satellite</option>
            <option value="terrain">Terrain</option>
            <option value="dark">Dark Mode</option>
          </select>
        </div>
      </div>

      {/* Statistics Panel */}
      {showStats && drawnItems.length > 0 && (
        <div className="absolute bottom-4 left-4 z-[1000]">
          <div className="bg-white p-2 rounded shadow-lg border text-xs">
            <div className="font-semibold mb-1">Drawing Statistics</div>
            <div>📍 Markers: {drawnItems.length}</div>
          </div>
        </div>
      )}

      {/* Instructions */}
      {editorMode && (
        <div className="absolute top-4 right-4 z-[1000]">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm max-w-xs">
            <div className="font-semibold text-blue-800 mb-1">How to Use:</div>
            <ul className="text-blue-700 space-y-1">
              <li>• Click anywhere on the map to add markers</li>
              <li>• Click on markers to see event details</li>
              <li>• Use "Clear All" to remove drawn items</li>
              <li>• Change map layers in the dropdown</li>
            </ul>
          </div>
        </div>
      )}

      {/* Map Container */}
      <div
        ref={mapContainerRef}
        className="w-full h-full"
        style={{ minHeight: '400px' }}
      />
    </div>
  );
};

export default MapEditorReal;