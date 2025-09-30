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

// Dynamic imports to handle potential import issues
let MapContainer, TileLayer, FeatureGroup, useMap, EditControl, L;

const loadLeafletComponents = async () => {
  try {
    const reactLeaflet = await import('react-leaflet');
    const leafletDraw = await import('react-leaflet-draw');
    const leaflet = await import('leaflet');

    MapContainer = reactLeaflet.MapContainer;
    TileLayer = reactLeaflet.TileLayer;
    FeatureGroup = reactLeaflet.FeatureGroup;
    useMap = reactLeaflet.useMap;
    EditControl = leafletDraw.EditControl;
    L = leaflet.default;

    // Fix for default markers in Leaflet
    delete L.Icon.Default.prototype._getIconUrl;
    L.Icon.Default.mergeOptions({
      iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
      iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
      shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
    });

    return true;
  } catch (error) {
    console.warn('Failed to load Leaflet components:', error);
    return false;
  }
};

// Map View Controller Component
const MapViewController = ({ onZoomIn, onZoomOut, onFitBounds }) => {
  const map = useMap ? useMap() : null;

  useEffect(() => {
    if (!map) return;

    const handleZoom = () => {
      // Can add zoom level tracking here if needed
    };

    map.on('zoom', handleZoom);
    return () => map.off('zoom', handleZoom);
  }, [map]);

  return null;
};

// Drawing Statistics Component
const DrawingStats = ({ drawnItems }) => {
  const getStats = () => {
    let markers = 0, polygons = 0, polylines = 0, circles = 0, rectangles = 0;

    if (L) {
      drawnItems.forEach(layer => {
        if (layer instanceof L.Marker) markers++;
        else if (layer instanceof L.Polygon) polygons++;
        else if (layer instanceof L.Polyline) polylines++;
        else if (layer instanceof L.Circle) circles++;
        else if (layer instanceof L.Rectangle) rectangles++;
      });
    }

    return { markers, polygons, polylines, circles, rectangles };
  };

  const stats = getStats();

  return (
    <div className="bg-white p-2 rounded shadow-lg border text-xs">
      <div className="font-semibold mb-1">Drawing Statistics</div>
      <div className="space-y-1">
        <div>📍 Markers: {stats.markers}</div>
        <div>▲ Polygons: {stats.polygons}</div>
        <div>📏 Lines: {stats.polylines}</div>
        <div>⭕ Circles: {stats.circles}</div>
        <div>⬛ Rectangles: {stats.rectangles}</div>
      </div>
    </div>
  );
};

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
  const [mapKey, setMapKey] = useState(0); // Force re-render when needed
  const [leafletLoaded, setLeafletLoaded] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  const featureGroupRef = useRef();
  const mapRef = useRef();

  // Load Leaflet components on mount
  useEffect(() => {
    const initLeaflet = async () => {
      setIsLoading(true);
      const loaded = await loadLeafletComponents();
      setLeafletLoaded(loaded);
      setIsLoading(false);
    };

    initLeaflet();
  }, []);

  // Load CSS files dynamically
  useEffect(() => {
    if (leafletLoaded) {
      // Load Leaflet CSS
      const leafletCss = document.createElement('link');
      leafletCss.rel = 'stylesheet';
      leafletCss.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
      leafletCss.integrity = 'sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=';
      leafletCss.crossOrigin = '';
      document.head.appendChild(leafletCss);

      // Load Leaflet Draw CSS
      const drawCss = document.createElement('link');
      drawCss.rel = 'stylesheet';
      drawCss.href = 'https://unpkg.com/leaflet-draw@1.0.4/dist/leaflet.draw.css';
      document.head.appendChild(drawCss);
    }
  }, [leafletLoaded]);

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
  const handleDrawCreated = useCallback((e) => {
    const { layer } = e;
    const newItems = [...drawnItems, layer];
    setDrawnItems(newItems);

    // Add custom properties to the layer
    layer.options.id = Date.now();
    layer.options.createdAt = new Date().toISOString();

    if (onDrawingChange) {
      onDrawingChange({
        type: 'created',
        layer: layer,
        allItems: newItems
      });
    }
  }, [drawnItems, onDrawingChange]);

  const handleDrawEdited = useCallback((e) => {
    const { layers } = e;
    layers.eachLayer((layer) => {
      layer.options.editedAt = new Date().toISOString();
    });

    if (onDrawingChange) {
      onDrawingChange({
        type: 'edited',
        layers: layers,
        allItems: drawnItems
      });
    }
  }, [drawnItems, onDrawingChange]);

  const handleDrawDeleted = useCallback((e) => {
    const { layers } = e;
    const deletedIds = [];
    layers.eachLayer((layer) => {
      deletedIds.push(layer.options.id);
    });

    const newItems = drawnItems.filter(item =>
      !deletedIds.includes(item.options.id)
    );
    setDrawnItems(newItems);

    if (onDrawingChange) {
      onDrawingChange({
        type: 'deleted',
        layers: layers,
        allItems: newItems
      });
    }
  }, [drawnItems, onDrawingChange]);

  // Mode switching
  const toggleMapMode = () => {
    const newMode = mapMode === '2D' ? '3D' : '2D';
    setMapMode(newMode);
    setMapKey(prev => prev + 1); // Force re-render
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

  // Map controls
  const zoomIn = () => {
    if (mapRef.current) {
      mapRef.current.zoomIn();
    }
  };

  const zoomOut = () => {
    if (mapRef.current) {
      mapRef.current.zoomOut();
    }
  };

  const fitBounds = () => {
    if (mapRef.current && featureGroupRef.current) {
      const bounds = featureGroupRef.current.getBounds();
      if (bounds.isValid()) {
        mapRef.current.fitBounds(bounds);
      }
    }
  };

  const clearAll = () => {
    if (featureGroupRef.current) {
      featureGroupRef.current.clearLayers();
      setDrawnItems([]);
      if (onDrawingChange) {
        onDrawingChange({
          type: 'cleared',
          allItems: []
        });
      }
    }
  };

  // Export functions
  const exportData = () => {
    if (!L) return { type: 'FeatureCollection', features: [] };

    const data = drawnItems.map(layer => {
      if (layer instanceof L.Marker) {
        return {
          type: 'marker',
          coordinates: [layer.getLatLng().lat, layer.getLatLng().lng],
          properties: layer.options
        };
      } else if (layer instanceof L.Polygon) {
        return {
          type: 'polygon',
          coordinates: layer.getLatLngs(),
          properties: layer.options
        };
      } else if (layer instanceof L.Polyline) {
        return {
          type: 'polyline',
          coordinates: layer.getLatLngs(),
          properties: layer.options
        };
      } else if (layer instanceof L.Circle) {
        return {
          type: 'circle',
          center: [layer.getLatLng().lat, layer.getLatLng().lng],
          radius: layer.getRadius(),
          properties: layer.options
        };
      }
      return null;
    }).filter(Boolean);

    return {
      type: 'FeatureCollection',
      features: data,
      metadata: {
        center: initialCenter,
        zoom: initialZoom,
        tileLayer: selectedTileLayer,
        exportedAt: new Date().toISOString()
      }
    };
  };

  // 3D Mode placeholder (for Cesium integration later)
  const render3DMode = () => (
    <div className="relative w-full h-full bg-gradient-to-b from-blue-400 to-blue-600 flex items-center justify-center">
      <div className="text-center text-white">
        <GlobeAltIcon className="h-16 w-16 mx-auto mb-4 opacity-70" />
        <h3 className="text-xl font-semibold mb-2">3D Globe Mode</h3>
        <p className="text-sm opacity-90 mb-4">Cesium 3D integration coming soon</p>
        <button
          onClick={toggleMapMode}
          className="bg-white text-blue-600 px-4 py-2 rounded-lg hover:bg-gray-100 transition-colors"
        >
          Switch to 2D Map
        </button>
      </div>
    </div>
  );

  // Loading state
  const renderLoading = () => (
    <div className="relative w-full h-full bg-gray-100 flex items-center justify-center">
      <div className="text-center text-gray-600">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
        <h3 className="text-lg font-semibold mb-2">Loading Map Components</h3>
        <p className="text-sm">Please wait while we initialize the mapping system...</p>
      </div>
    </div>
  );

  // Fallback 2D mode when Leaflet fails to load
  const renderFallback2D = () => (
    <div className="relative w-full h-full bg-gradient-to-b from-green-400 to-blue-500 flex items-center justify-center">
      <div className="text-center text-white">
        <MapIcon className="h-16 w-16 mx-auto mb-4 opacity-70" />
        <h3 className="text-xl font-semibold mb-2">Map Unavailable</h3>
        <p className="text-sm opacity-90 mb-4">
          The mapping library couldn't be loaded. This could be due to network issues or package configuration.
        </p>
        <div className="bg-white bg-opacity-20 rounded-lg p-4 text-sm">
          <p className="mb-2">Historical Events Available:</p>
          <div className="text-left">
            {historicalEvents.slice(0, 3).map((event, index) => (
              <div key={index} className="mb-1">
                {event.icon} {event.title} ({event.year} {event.isBC ? 'BC' : 'AD'})
              </div>
            ))}
            {historicalEvents.length > 3 && (
              <div>...and {historicalEvents.length - 3} more events</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );

  // Render the appropriate map content
  const renderMapContent = () => {
    if (isLoading) {
      return renderLoading();
    }

    if (mapMode === '3D') {
      return render3DMode();
    }

    if (!leafletLoaded || !MapContainer) {
      return renderFallback2D();
    }

    return (
      <MapContainer
        key={`map-${mapKey}-${selectedTileLayer}`}
        center={initialCenter}
        zoom={initialZoom}
        className="w-full h-full"
        ref={mapRef}
      >
        <TileLayer
          attribution={tileLayerOptions[selectedTileLayer].attribution}
          url={tileLayerOptions[selectedTileLayer].url}
        />

        {editorMode && L && EditControl && (
          <FeatureGroup ref={featureGroupRef}>
            <EditControl
              position="topright"
              onCreated={handleDrawCreated}
              onEdited={handleDrawEdited}
              onDeleted={handleDrawDeleted}
              draw={{
                rectangle: {
                  shapeOptions: {
                    color: '#ff7800',
                    weight: 2,
                    opacity: 0.8,
                    fillOpacity: 0.2
                  }
                },
                polygon: {
                  allowIntersection: false,
                  shapeOptions: {
                    color: '#ff7800',
                    weight: 2,
                    opacity: 0.8,
                    fillOpacity: 0.2
                  }
                },
                circle: {
                  shapeOptions: {
                    color: '#ff7800',
                    weight: 2,
                    opacity: 0.8,
                    fillOpacity: 0.2
                  }
                },
                polyline: {
                  shapeOptions: {
                    color: '#ff7800',
                    weight: 3,
                    opacity: 0.8
                  }
                },
                marker: true,
                circlemarker: false
              }}
              edit={{
                featureGroup: featureGroupRef.current,
                remove: true,
                edit: true
              }}
            />
          </FeatureGroup>
        )}

        {MapViewController && (
          <MapViewController
            onZoomIn={zoomIn}
            onZoomOut={zoomOut}
            onFitBounds={fitBounds}
          />
        )}
      </MapContainer>
    );
  };

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

        {/* Map Controls */}
        {mapMode === '2D' && (
          <div className="bg-white rounded-lg shadow-lg p-2 flex flex-col space-y-1">
            <button
              onClick={zoomIn}
              className="flex items-center justify-center p-2 text-gray-700 hover:bg-gray-100 rounded"
              title="Zoom In"
            >
              <PlusIcon className="h-4 w-4" />
            </button>
            <button
              onClick={zoomOut}
              className="flex items-center justify-center p-2 text-gray-700 hover:bg-gray-100 rounded"
              title="Zoom Out"
            >
              <MinusIcon className="h-4 w-4" />
            </button>
            <button
              onClick={fitBounds}
              className="flex items-center justify-center p-2 text-gray-700 hover:bg-gray-100 rounded"
              title="Fit to Drawings"
            >
              <ArrowsPointingOutIcon className="h-4 w-4" />
            </button>
            {editorMode && (
              <button
                onClick={clearAll}
                className="flex items-center justify-center p-2 text-red-600 hover:bg-red-50 rounded"
                title="Clear All"
              >
                <TrashIcon className="h-4 w-4" />
              </button>
            )}
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
          <DrawingStats drawnItems={drawnItems} />
        </div>
      )}

      {/* Export Button */}
      {editorMode && drawnItems.length > 0 && mapMode === '2D' && (
        <div className="absolute bottom-4 right-4 z-[1000]">
          <button
            onClick={() => {
              const data = exportData();
              console.log('Exported map data:', data);
              // You can implement actual export functionality here
            }}
            className="bg-blue-500 text-white px-4 py-2 rounded-lg shadow-lg hover:bg-blue-600 transition-colors text-sm"
          >
            Export Data
          </button>
        </div>
      )}

      {/* Map Content */}
      {renderMapContent()}
    </div>
  );
};

export default MapEditor;