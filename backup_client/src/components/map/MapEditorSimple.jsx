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

const MapEditor = ({
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

  // Drawing event handlers
  const handleDrawCreated = useCallback((drawingData) => {
    const newItems = [...drawnItems, drawingData];
    setDrawnItems(newItems);

    if (onDrawingChange) {
      onDrawingChange({
        type: 'created',
        data: drawingData,
        allItems: newItems
      });
    }
  }, [drawnItems, onDrawingChange]);

  // Mode switching
  const toggleMapMode = () => {
    const newMode = mapMode === '2D' ? '3D' : '2D';
    setMapMode(newMode);
    setMapKey(prev => prev + 1);
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

  // Mock drawing functions for demo
  const addMarker = () => {
    const newMarker = {
      id: Date.now(),
      type: 'marker',
      lat: initialCenter[0] + (Math.random() - 0.5) * 2,
      lng: initialCenter[1] + (Math.random() - 0.5) * 2,
      title: 'New Marker'
    };
    handleDrawCreated(newMarker);
  };

  const clearAll = () => {
    setDrawnItems([]);
    if (onDrawingChange) {
      onDrawingChange({
        type: 'cleared',
        allItems: []
      });
    }
  };

  // 3D Mode placeholder
  const render3DMode = () => (
    <div className="relative w-full h-full bg-gradient-to-b from-blue-400 to-blue-600 flex items-center justify-center">
      <div className="text-center text-white">
        <GlobeAltIcon className="h-16 w-16 mx-auto mb-4 opacity-70" />
        <h3 className="text-xl font-semibold mb-2">3D Globe Mode</h3>
        <p className="text-sm opacity-90 mb-4">Cesium 3D integration ready to implement</p>
        <button
          onClick={toggleMapMode}
          className="bg-white text-blue-600 px-4 py-2 rounded-lg hover:bg-gray-100 transition-colors"
        >
          Switch to 2D Map
        </button>
      </div>
    </div>
  );

  // 2D Map Placeholder with interactive elements
  const render2DMode = () => (
    <div
      className="relative w-full h-full bg-gradient-to-br from-blue-100 to-green-100 overflow-hidden"
      style={{
        backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%234ade80' fill-opacity='0.1'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`
      }}
    >
      {/* Map Background */}
      <div className="absolute inset-0 bg-gradient-to-br from-blue-200 to-green-200 opacity-50"></div>

      {/* Coordinate Grid */}
      <div className="absolute inset-0 opacity-10">
        {Array.from({ length: 10 }).map((_, i) => (
          <div key={`h-${i}`} className="absolute w-full h-px bg-gray-600" style={{ top: `${i * 10}%` }}></div>
        ))}
        {Array.from({ length: 10 }).map((_, i) => (
          <div key={`v-${i}`} className="absolute h-full w-px bg-gray-600" style={{ left: `${i * 10}%` }}></div>
        ))}
      </div>

      {/* Center Crosshair */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        <div className="w-8 h-8 border-2 border-blue-500 border-dashed rounded-full opacity-50"></div>
      </div>

      {/* Historical Events */}
      {historicalEvents.map((event, index) => (
        <div
          key={event.id || index}
          className="absolute transform -translate-x-1/2 -translate-y-1/2 cursor-pointer z-10"
          style={{
            left: `${30 + (index % 3) * 15}%`,
            top: `${30 + Math.floor(index / 3) * 15}%`
          }}
          title={`${event.title} (${event.year} ${event.isBC ? 'BC' : 'AD'})`}
        >
          <div className="bg-white rounded-full p-2 shadow-lg hover:shadow-xl transition-shadow border-2 border-blue-300">
            <span className="text-lg">{event.icon || '📍'}</span>
          </div>
        </div>
      ))}

      {/* Drawn Items */}
      {drawnItems.map((item, index) => (
        <div
          key={item.id || index}
          className="absolute transform -translate-x-1/2 -translate-y-1/2 z-20"
          style={{
            left: `${50 + (index % 4 - 2) * 10}%`,
            top: `${50 + (Math.floor(index / 4) % 4 - 2) * 10}%`
          }}
        >
          <div className="bg-orange-500 text-white rounded-full p-2 shadow-lg border-2 border-orange-600">
            <span className="text-xs font-bold">
              {item.type === 'marker' ? '📍' : '✏️'}
            </span>
          </div>
        </div>
      ))}

      {/* Interactive Overlay */}
      {editorMode && (
        <div
          className="absolute inset-0 cursor-crosshair"
          onClick={(e) => {
            const rect = e.currentTarget.getBoundingClientRect();
            const x = ((e.clientX - rect.left) / rect.width) * 100;
            const y = ((e.clientY - rect.top) / rect.height) * 100;

            const newItem = {
              id: Date.now(),
              type: 'marker',
              x: x,
              y: y,
              title: `Marker at ${x.toFixed(1)}%, ${y.toFixed(1)}%`
            };
            handleDrawCreated(newItem);
          }}
        />
      )}

      {/* Map Info Overlay */}
      <div className="absolute bottom-2 left-2 bg-white bg-opacity-90 rounded px-2 py-1 text-xs text-gray-700">
        <div>📍 {initialCenter[0].toFixed(4)}°N, {initialCenter[1].toFixed(4)}°E</div>
        <div>🔍 Zoom: {initialZoom}</div>
        <div>🗺️ Layer: {selectedTileLayer}</div>
      </div>
    </div>
  );

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
        <div className="bg-white rounded-lg shadow-lg p-2 flex space-x-2">
          <button
            onClick={toggleEditorMode}
            className={`flex items-center px-3 py-2 rounded text-sm font-medium transition-colors ${
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
        {editorMode && mapMode === '2D' && (
          <div className="bg-white rounded-lg shadow-lg p-2 flex flex-col space-y-1">
            <button
              onClick={addMarker}
              className="flex items-center px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded transition-colors"
            >
              <PlusIcon className="h-4 w-4 mr-2" />
              Add Marker
            </button>
            <button
              onClick={clearAll}
              className="flex items-center px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded transition-colors"
            >
              <TrashIcon className="h-4 w-4 mr-2" />
              Clear All
            </button>
          </div>
        )}

        {/* Tile Layer Selector */}
        {mapMode === '2D' && (
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
        )}
      </div>

      {/* Statistics Panel */}
      {showStats && drawnItems.length > 0 && mapMode === '2D' && (
        <div className="absolute bottom-4 left-4 z-[1000]">
          <div className="bg-white p-2 rounded shadow-lg border text-xs">
            <div className="font-semibold mb-1">Drawing Statistics</div>
            <div>📍 Total Items: {drawnItems.length}</div>
          </div>
        </div>
      )}

      {/* Instructions */}
      {editorMode && mapMode === '2D' && (
        <div className="absolute top-4 right-4 z-[1000]">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm max-w-xs">
            <div className="font-semibold text-blue-800 mb-1">How to Use:</div>
            <ul className="text-blue-700 space-y-1">
              <li>• Click anywhere on the map to add markers</li>
              <li>• Use "Add Marker" button for random placement</li>
              <li>• Switch between 2D/3D modes</li>
              <li>• Toggle Editor/Read-only mode</li>
            </ul>
          </div>
        </div>
      )}

      {/* Export Button */}
      {editorMode && drawnItems.length > 0 && (
        <div className="absolute bottom-4 right-4 z-[1000]">
          <button
            onClick={() => {
              console.log('Exported data:', { drawnItems, historicalEvents, settings: { mapMode, editorMode, selectedTileLayer } });
              alert(`Exported ${drawnItems.length} items! Check console for details.`);
            }}
            className="bg-blue-500 text-white px-4 py-2 rounded-lg shadow-lg hover:bg-blue-600 transition-colors text-sm"
          >
            Export Data ({drawnItems.length})
          </button>
        </div>
      )}

      {/* Map Content */}
      {mapMode === '3D' ? render3DMode() : render2DMode()}
    </div>
  );
};

export default MapEditor;