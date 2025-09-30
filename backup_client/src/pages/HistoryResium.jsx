import React, { useState, useCallback, useRef, useEffect } from 'react';
import {
  PlayIcon,
  PauseIcon,
  BackwardIcon,
  ForwardIcon,
  MagnifyingGlassIcon,
  CalendarIcon,
  GlobeAltIcon,
  ClockIcon,
  MapPinIcon,
  AdjustmentsHorizontalIcon,
  EyeIcon,
  InformationCircleIcon,
  StarIcon,
  CogIcon,
} from '@heroicons/react/24/outline';
import MapEditorSimple from '../components/map/MapEditorSimple';
import MapEditorReal from '../components/map/MapEditorReal';
import MapEditorTest from '../components/map/MapEditorTest';
import OpenSourceMap from '../components/map/OpenSourceMap';
import LeafletMap from '../components/map/LeafletMap';
import ResiumGlobe from '../components/ResiumGlobe';

const HistoryResium = () => {
  const leafletMapRef = useRef();
  const leafletContainerRef = useRef();

  const [selectedDate, setSelectedDate] = useState(new Date().getFullYear());
  const [granularity, setGranularity] = useState('year');
  const [isPlaying, setIsPlaying] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [isBC, setIsBC] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [showSettings, setShowSettings] = useState(false);
  const [terrainEnabled, setTerrainEnabled] = useState(true);
  const [lighting, setLighting] = useState(true);
  const [mousePosition, setMousePosition] = useState({ lat: 0, lon: 0, alt: 0 });
  const [cameraHeight, setCameraHeight] = useState(0);

  // 2D/3D mode toggle state
  const [mapViewMode, setMapViewMode] = useState('3D');
  const [isMapEditor, setIsMapEditor] = useState(true);
  const [drawnItems, setDrawnItems] = useState([]);

  // Resium-specific state
  const [navigationTarget, setNavigationTarget] = useState(null);
  const [isTransitioning, setIsTransitioning] = useState(false);

  // Stable map state for 2D mode
  const [stableMapCenter, setStableMapCenter] = useState([46.2044, 6.1432]);
  const [stableMapZoom, setStableMapZoom] = useState(6);
  const [leafletReady, setLeafletReady] = useState(false);

  // Event notification
  const [eventNotification, setEventNotification] = useState(null);

  // Enhanced historical events data
  const [historicalEvents] = useState([
    {
      id: 1,
      title: "Fall of the Roman Empire",
      year: 476,
      isBC: false,
      lat: 41.9028,
      lon: 12.4964,
      description: "The Western Roman Empire falls to Germanic tribes, marking the end of ancient Rome.",
      category: "Political",
      importance: 5,
      icon: "🏛️",
    },
    {
      id: 2,
      title: "Great Wall of China Construction",
      year: 221,
      isBC: true,
      lat: 40.4319,
      lon: 116.5704,
      description: "Emperor Qin Shi Huang begins construction of the Great Wall to defend against northern invasions.",
      category: "Architecture",
      importance: 5,
      icon: "🏯",
    },
    {
      id: 3,
      title: "Birth of Jesus Christ",
      year: 1,
      isBC: true,
      lat: 31.7683,
      lon: 35.2137,
      description: "Traditional date for the birth of Jesus Christ in Bethlehem.",
      category: "Religious",
      importance: 5,
      icon: "✝️",
    },
    {
      id: 4,
      title: "Discovery of America",
      year: 1492,
      isBC: false,
      lat: 25.0343,
      lon: -77.3963,
      description: "Christopher Columbus reaches the Americas, connecting two worlds.",
      category: "Exploration",
      importance: 5,
      icon: "⛵",
    },
    {
      id: 5,
      title: "World War II Ends",
      year: 1945,
      isBC: false,
      lat: 35.6762,
      lon: 139.6503,
      description: "World War II officially ends with Japan's surrender.",
      category: "Military",
      importance: 5,
      icon: "🕊️",
    },
    {
      id: 6,
      title: "Pyramids of Giza Built",
      year: 2580,
      isBC: true,
      lat: 29.9792,
      lon: 31.1342,
      description: "The Great Pyramid of Giza is constructed, one of the Seven Wonders of the Ancient World.",
      category: "Architecture",
      importance: 4,
      icon: "🔺",
    },
    {
      id: 7,
      title: "First Moon Landing",
      year: 1969,
      isBC: false,
      lat: 28.5721,
      lon: -80.648,
      description: "Apollo 11 launches from Kennedy Space Center, leading to the first human moon landing.",
      category: "Science",
      importance: 5,
      icon: "🚀",
    },
    {
      id: 8,
      title: "Renaissance Begins in Florence",
      year: 1400,
      isBC: false,
      lat: 43.7696,
      lon: 11.2558,
      description: "The Renaissance movement begins in Florence, marking a rebirth of art, science, and culture.",
      category: "Cultural",
      importance: 4,
      icon: "🎨",
    }
  ]);

  // Timeline configuration
  const timelineRange = { start: -3000, end: 2025 };
  const [timelinePosition, setTimelinePosition] = useState(85);

  // Convert year to timeline position percentage
  const yearToPercentage = useCallback((year, isBCYear) => {
    const actualYear = isBCYear ? -Math.abs(year) : year;
    const range = timelineRange.end - timelineRange.start;
    return ((actualYear - timelineRange.start) / range) * 100;
  }, [timelineRange]);

  // Convert percentage to year
  const percentageToYear = useCallback((percentage) => {
    const range = timelineRange.end - timelineRange.start;
    const year = timelineRange.start + (percentage / 100) * range;
    return {
      year: Math.abs(Math.round(year)),
      isBC: year < 0
    };
  }, [timelineRange]);

  // Filter events based on selected date and granularity
  const filteredEvents = historicalEvents.filter(event => {
    const eventYear = event.isBC ? -event.year : event.year;
    const selectedYear = isBC ? -selectedDate : selectedDate;

    switch (granularity) {
      case 'year':
        return Math.abs(eventYear - selectedYear) <= 50;
      case 'month':
        return Math.abs(eventYear - selectedYear) <= 10;
      case 'day':
        return Math.abs(eventYear - selectedYear) <= 1;
      default:
        return true;
    }
  });

  // Handle event selection with Resium navigation
  const handleEventSelect = useCallback((event) => {
    console.log(`🚨 Resium: handleEventSelect called with: ${event.title}`);

    setSelectedEvent(event);
    setSelectedDate(event.year);
    setIsBC(event.isBC);
    setTimelinePosition(yearToPercentage(event.year, event.isBC));

    console.log(`🎯 Event selection: ${event.title} (Mode: ${mapViewMode})`);

    // Handle navigation based on current mode
    if (mapViewMode === '3D') {
      console.log('🌍 Using Resium 3D navigation');
      setNavigationTarget(event);

      // Show event notification
      setEventNotification(`🎬 Navigating to: ${event.title}`);
      setTimeout(() => setEventNotification(null), 3000);

      // After navigation completes, optionally switch to 2D
      setTimeout(() => {
        console.log('🔄 Switching to 2D view after Resium navigation');
        setStableMapCenter([event.lat, event.lon]);
        setStableMapZoom(15);
        setMapViewMode('2D');
      }, 8000); // Allow time for 3D animation

    } else if (mapViewMode === '2D' && leafletMapRef.current) {
      console.log('🗺️ Using 2D Leaflet navigation');
      if (leafletMapRef.current && leafletMapRef.current.flyTo) {
        leafletMapRef.current.flyTo(event.lat, event.lon, 12);
        console.log(`✅ 2D map navigated to: ${event.title}`);
      }
    }
  }, [yearToPercentage, mapViewMode]);

  // Handle camera changes from Resium
  const handleCameraChange = useCallback((cameraInfo) => {
    setCameraHeight(cameraInfo.height || 0);
    setMousePosition({
      lat: cameraInfo.lat || 0,
      lon: cameraInfo.lon || 0,
      alt: cameraInfo.height || 0
    });
  }, []);

  // Handle timeline change
  const handleTimelineChange = useCallback((e) => {
    const percentage = parseFloat(e.target.value);
    setTimelinePosition(percentage);
    const { year, isBC: yearIsBC } = percentageToYear(percentage);
    setSelectedDate(year);
    setIsBC(yearIsBC);
  }, [percentageToYear]);

  // Handle play/pause
  const handlePlayPause = useCallback(() => {
    setIsPlaying(!isPlaying);
  }, [isPlaying]);

  // Auto-advance timeline when playing
  useEffect(() => {
    if (isPlaying && !isTransitioning) {
      const interval = setInterval(() => {
        setTimelinePosition(prev => {
          const newPos = prev + 0.1;
          if (newPos >= 100) {
            setIsPlaying(false);
            return 100;
          }
          const { year, isBC: yearIsBC } = percentageToYear(newPos);
          setSelectedDate(year);
          setIsBC(yearIsBC);
          return newPos;
        });
      }, 100);
      return () => clearInterval(interval);
    }
  }, [isPlaying, isTransitioning, percentageToYear]);

  // Find the closest event to the current timeline position
  const findClosestEventToTimeline = useCallback((currentYear, currentIsBC) => {
    const currentActualYear = currentIsBC ? -currentYear : currentYear;

    let closest = null;
    let minDistance = Infinity;

    historicalEvents.forEach(event => {
      const eventActualYear = event.isBC ? -event.year : event.year;
      const distance = Math.abs(eventActualYear - currentActualYear);
      if (distance < minDistance) {
        minDistance = distance;
        closest = event;
      }
    });

    return closest;
  }, [historicalEvents]);

  // Container dimension checking for 2D mode
  useEffect(() => {
    if (mapViewMode === '2D') {
      setLeafletReady(false);

      let attempts = 0;
      const maxAttempts = 30;

      const checkContainerDimensions = () => {
        attempts++;

        if (leafletContainerRef.current) {
          const rect = leafletContainerRef.current.getBoundingClientRect();
          console.log(`🔍 Attempt ${attempts}: Checking leaflet container dimensions:`, {
            width: rect.width,
            height: rect.height,
            display: window.getComputedStyle(leafletContainerRef.current).display,
            visibility: window.getComputedStyle(leafletContainerRef.current).visibility
          });

          if (rect.width > 0 && rect.height > 0) {
            console.log('✅ Leaflet container has proper dimensions, setting leafletReady = true');
            setLeafletReady(true);
            return;
          }
        }

        if (attempts < maxAttempts) {
          setTimeout(checkContainerDimensions, 100);
        } else {
          console.warn('❌ Leaflet container never got proper dimensions, forcing leafletReady = true');
          setLeafletReady(true);
        }
      };

      // Small initial delay
      setTimeout(checkContainerDimensions, 100);
    } else {
      setLeafletReady(false);
    }
  }, [mapViewMode]);

  return (
    <div className="flex flex-col h-screen bg-gray-900 text-white">
      {/* Header */}
      <div className="bg-gray-800 border-b border-gray-700 px-6 py-4 flex items-center justify-between flex-shrink-0">
        <div className="flex items-center space-x-4">
          <h1 className="text-xl font-bold text-blue-400 flex items-center">
            <ClockIcon className="h-6 w-6 mr-2" />
            Historical Timeline (Resium)
          </h1>
          <div className="flex items-center space-x-2 text-sm text-gray-400">
            <span>{selectedDate} {isBC ? 'BC' : 'AD'}</span>
            <span>•</span>
            <span className="capitalize">{granularity} view</span>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          {/* View Mode Toggle */}
          <div className="flex bg-gray-700 rounded-lg p-1">
            <button
              onClick={() => setMapViewMode('3D')}
              className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                mapViewMode === '3D'
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-300 hover:text-white'
              }`}
            >
              <GlobeAltIcon className="h-4 w-4 inline mr-1" />
              3D Globe
            </button>
            <button
              onClick={() => setMapViewMode('2D')}
              className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                mapViewMode === '2D'
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-300 hover:text-white'
              }`}
            >
              <MapPinIcon className="h-4 w-4 inline mr-1" />
              2D Map
            </button>
          </div>

          <button
            onClick={() => setShowSettings(!showSettings)}
            className="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-lg transition-colors"
          >
            <CogIcon className="h-5 w-5" />
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex flex-1 min-h-0">
        {/* Sidebar */}
        <div className="w-80 bg-gray-800 border-r border-gray-700 flex flex-col">
          {/* Search */}
          <div className="p-4 border-b border-gray-700">
            <div className="relative">
              <MagnifyingGlassIcon className="h-5 w-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Search historical events..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>

          {/* Events List */}
          <div className="flex-1 overflow-y-auto">
            <div className="p-4">
              <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">
                Historical Events ({filteredEvents.length})
              </h3>
              <div className="space-y-2">
                {filteredEvents
                  .filter(event =>
                    searchQuery === '' ||
                    event.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                    event.description.toLowerCase().includes(searchQuery.toLowerCase())
                  )
                  .sort((a, b) => {
                    const aYear = a.isBC ? -a.year : a.year;
                    const bYear = b.isBC ? -b.year : b.year;
                    return aYear - bYear;
                  })
                  .map(event => (
                    <div
                      key={event.id}
                      onClick={() => handleEventSelect(event)}
                      className={`p-3 rounded-lg cursor-pointer transition-colors ${
                        selectedEvent?.id === event.id
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-700 hover:bg-gray-600 text-gray-200'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-medium text-sm">
                          {event.icon} {event.title}
                        </span>
                        <span className="text-xs opacity-75">
                          {event.year} {event.isBC ? 'BC' : 'AD'}
                        </span>
                      </div>
                      <p className="text-xs opacity-75 line-clamp-2">
                        {event.description}
                      </p>
                      <div className="flex items-center justify-between mt-2">
                        <span className="text-xs px-2 py-1 bg-gray-600 rounded">
                          {event.category}
                        </span>
                        <div className="flex">
                          {Array.from({ length: event.importance }).map((_, i) => (
                            <StarIcon key={i} className="h-3 w-3 text-yellow-400 fill-current" />
                          ))}
                        </div>
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          </div>
        </div>

        {/* Map Container */}
        <div className="flex-1 relative">
          {/* Event Notification */}
          {eventNotification && (
            <div className="absolute top-4 left-1/2 transform -translate-x-1/2 z-50 bg-blue-600 text-white px-6 py-3 rounded-lg shadow-lg">
              {eventNotification}
            </div>
          )}

          {/* 3D Globe - Resium */}
          {mapViewMode === '3D' && (
            <div className="w-full h-full">
              <ResiumGlobe
                events={historicalEvents}
                selectedEvent={selectedEvent}
                onEventSelect={handleEventSelect}
                terrainEnabled={terrainEnabled}
                lighting={lighting}
                onCameraChange={handleCameraChange}
                navigationTarget={navigationTarget}
                className="w-full h-full"
              />
            </div>
          )}

          {/* 2D Map - Leaflet */}
          {mapViewMode === '2D' && (
            <div
              ref={leafletContainerRef}
              className="w-full h-full"
            >
              {leafletReady && (
                <LeafletMap
                  ref={leafletMapRef}
                  center={stableMapCenter}
                  zoom={stableMapZoom}
                  events={historicalEvents}
                  selectedEvent={selectedEvent}
                  onEventSelect={handleEventSelect}
                  drawnItems={drawnItems}
                  setDrawnItems={setDrawnItems}
                  isMapEditor={isMapEditor}
                  className="w-full h-full"
                />
              )}
            </div>
          )}

          {/* Timeline Controls */}
          <div className="absolute bottom-4 left-4 right-4 bg-gray-800 bg-opacity-90 backdrop-blur-sm rounded-lg p-4 border border-gray-700">
            <div className="flex items-center space-x-4">
              <button
                onClick={handlePlayPause}
                className="p-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
              >
                {isPlaying ? (
                  <PauseIcon className="h-5 w-5" />
                ) : (
                  <PlayIcon className="h-5 w-5" />
                )}
              </button>

              <div className="flex-1">
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={timelinePosition}
                  onChange={handleTimelineChange}
                  className="w-full h-2 bg-gray-600 rounded-lg appearance-none cursor-pointer"
                  style={{
                    background: `linear-gradient(to right, #3B82F6 0%, #3B82F6 ${timelinePosition}%, #4B5563 ${timelinePosition}%, #4B5563 100%)`
                  }}
                />
                <div className="flex justify-between text-xs text-gray-400 mt-1">
                  <span>3000 BC</span>
                  <span className="font-medium text-blue-400">
                    {selectedDate} {isBC ? 'BC' : 'AD'}
                  </span>
                  <span>2025 AD</span>
                </div>
              </div>

              <div className="text-right text-sm text-gray-400">
                <div>Alt: {Math.round(cameraHeight)}m</div>
                <div>
                  {mousePosition.lat.toFixed(2)}°, {mousePosition.lon.toFixed(2)}°
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Settings Panel */}
      {showSettings && (
        <div className="absolute top-16 right-4 w-80 bg-gray-800 border border-gray-700 rounded-lg shadow-xl z-50">
          <div className="p-4 border-b border-gray-700">
            <h3 className="font-semibold text-white">Globe Settings</h3>
          </div>
          <div className="p-4 space-y-4">
            <div className="flex items-center justify-between">
              <label className="text-sm text-gray-300">Terrain</label>
              <input
                type="checkbox"
                checked={terrainEnabled}
                onChange={(e) => setTerrainEnabled(e.target.checked)}
                className="rounded"
              />
            </div>
            <div className="flex items-center justify-between">
              <label className="text-sm text-gray-300">Lighting</label>
              <input
                type="checkbox"
                checked={lighting}
                onChange={(e) => setLighting(e.target.checked)}
                className="rounded"
              />
            </div>
            <div className="flex items-center justify-between">
              <label className="text-sm text-gray-300">Map Editor</label>
              <input
                type="checkbox"
                checked={isMapEditor}
                onChange={(e) => setIsMapEditor(e.target.checked)}
                className="rounded"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default HistoryResium;