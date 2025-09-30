import React, { useState, useCallback, useMemo, useEffect } from 'react';

const ResiumGlobe = ({
  events = [],
  selectedEvent,
  onEventSelect,
  terrainEnabled = true,
  lighting = true,
  onCameraChange,
  navigationTarget = null,
  className = ''
}) => {
  const [cesiumLoaded, setCesiumLoaded] = useState(false);
  const [resiumLoaded, setResiumLoaded] = useState(false);
  const [viewer, setViewer] = useState(null);
  const [isReady, setIsReady] = useState(false);
  const [error, setError] = useState(null);
  const [Resium, setResium] = useState(null);
  const [Cesium, setCesium] = useState(null);

  // Load Cesium and Resium dynamically to avoid ES module conflicts
  useEffect(() => {
    const loadLibraries = async () => {
      try {
        console.log('📦 Loading Cesium dynamically...');

        // Load Cesium script
        if (!window.Cesium) {
          const cesiumScript = document.createElement('script');
          cesiumScript.src = '/cesium/Cesium.js';
          cesiumScript.onload = async () => {
            console.log('✅ Cesium loaded globally');
            setCesiumLoaded(true);
            setCesium(window.Cesium);

            try {
              // Now load Resium
              console.log('📦 Loading Resium dynamically...');
              const resiumModule = await import('resium');
              console.log('✅ Resium loaded:', resiumModule);
              setResium(resiumModule);
              setResiumLoaded(true);
            } catch (resiumError) {
              console.error('❌ Failed to load Resium:', resiumError);
              setError(`Failed to load Resium: ${resiumError.message}`);
            }
          };
          cesiumScript.onerror = (err) => {
            console.error('❌ Failed to load Cesium script:', err);
            setError('Failed to load Cesium library');
          };
          document.head.appendChild(cesiumScript);
        } else {
          console.log('✅ Cesium already available');
          setCesiumLoaded(true);
          setCesium(window.Cesium);

          try {
            const resiumModule = await import('resium');
            console.log('✅ Resium loaded:', resiumModule);
            setResium(resiumModule);
            setResiumLoaded(true);
          } catch (resiumError) {
            console.error('❌ Failed to load Resium:', resiumError);
            setError(`Failed to load Resium: ${resiumError.message}`);
          }
        }
      } catch (err) {
        console.error('❌ Library loading error:', err);
        setError(`Library loading failed: ${err.message}`);
      }
    };

    loadLibraries();
  }, []);

  // Handle viewer ready
  const handleViewerReady = useCallback((cesiumViewer) => {
    console.log('🌍 Resium Viewer ready!', cesiumViewer);
    try {
      setViewer(cesiumViewer.cesiumElement);
      setIsReady(true);
      console.log('✅ Resium Globe ready!');
    } catch (err) {
      console.error('❌ Viewer setup error:', err);
      setError(`Viewer setup failed: ${err.message}`);
    }
  }, []);

  // Handle entity click
  const handleEntityClick = useCallback((entity, entityPickInfo) => {
    console.log('🎯 Entity clicked:', entity);
    if (entity?.properties?.eventData?.getValue && onEventSelect) {
      const eventData = entity.properties.eventData.getValue();
      onEventSelect(eventData);
    }
  }, [onEventSelect]);

  // Navigation to event
  const handleCameraFlyTo = useCallback((targetEvent) => {
    if (!viewer || !targetEvent || !targetEvent.lat || !targetEvent.lon || !Cesium) return;

    console.log(`🚁 Flying to ${targetEvent.title}`);

    const destination = Cesium.Cartesian3.fromDegrees(targetEvent.lon, targetEvent.lat, 15000000);

    viewer.camera.flyTo({
      destination,
      orientation: {
        heading: 0.0,
        pitch: -1.57,
        roll: 0.0
      },
      duration: 3.0
    });
  }, [viewer, Cesium]);

  // Effect to handle navigation target changes
  useEffect(() => {
    if (navigationTarget && isReady) {
      handleCameraFlyTo(navigationTarget);
    }
  }, [navigationTarget, isReady, handleCameraFlyTo]);

  // Create entities for events
  const eventEntities = useMemo(() => {
    if (!events.length || !Resium || !Cesium) return [];

    const { Entity, PointGraphics, LabelGraphics } = Resium;

    return events.map((event) => {
      if (!event.lat || !event.lon) return null;

      const position = Cesium.Cartesian3.fromDegrees(event.lon, event.lat, 0);
      const isSelected = selectedEvent?.id === event.id;

      return React.createElement(Entity, {
        key: event.id,
        position: position,
        onClick: handleEntityClick,
        properties: {
          eventData: event
        }
      }, [
        React.createElement(PointGraphics, {
          key: 'point',
          pixelSize: isSelected ? 12 : 8,
          color: isSelected ? Cesium.Color.YELLOW : Cesium.Color.fromCssColorString(event.color || '#ff6b6b'),
          outlineColor: Cesium.Color.BLACK,
          outlineWidth: 2,
          heightReference: Cesium.HeightReference?.CLAMP_TO_GROUND
        }),
        isSelected && React.createElement(LabelGraphics, {
          key: 'label',
          text: event.title,
          font: '12pt sans-serif',
          pixelOffset: new Cesium.Cartesian3(0, -50, 0),
          fillColor: Cesium.Color.WHITE,
          outlineColor: Cesium.Color.BLACK,
          outlineWidth: 2,
          style: Cesium.LabelStyle?.FILL_AND_OUTLINE,
          verticalOrigin: Cesium.VerticalOrigin?.BOTTOM
        })
      ].filter(Boolean));
    }).filter(Boolean);
  }, [events, selectedEvent, handleEntityClick, Resium, Cesium]);

  // Loading state
  if (!cesiumLoaded || !resiumLoaded) {
    return (
      <div className={`flex items-center justify-center bg-gray-900 text-white ${className}`}>
        <div className="text-center">
          <div className="text-xl mb-2">🌍</div>
          <div>Loading 3D Globe...</div>
          <div className="text-sm text-blue-400 mt-1">
            {!cesiumLoaded ? 'Loading Cesium...' : 'Loading Resium...'}
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className={`flex items-center justify-center bg-gray-900 text-white ${className}`}>
        <div className="text-center">
          <div className="text-xl mb-2">❌</div>
          <div>Failed to load 3D Globe</div>
          <div className="text-sm text-red-400 mt-1">
            {error}
          </div>
          <div className="text-xs text-gray-400 mt-2">
            Please refresh the page
          </div>
        </div>
      </div>
    );
  }

  console.log('🔄 Rendering Resium Viewer...');

  const { Viewer } = Resium;

  return (
    <div className={className}>
      {React.createElement(Viewer, {
        full: true,
        onMount: handleViewerReady,
        terrainProvider: terrainEnabled ? undefined : false,
        baseLayerPicker: false,
        geocoder: false,
        homeButton: false,
        sceneModePicker: false,
        navigationHelpButton: false,
        animation: false,
        timeline: false,
        fullscreenButton: false,
        vrButton: false,
        infoBox: false,
        selectionIndicator: true,
        onError: (error) => {
          console.error('❌ Resium Viewer error:', error);
          setError(`Resium error: ${error.message}`);
        }
      }, eventEntities)}
    </div>
  );
};

export default ResiumGlobe;