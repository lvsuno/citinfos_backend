import React, { useState, useCallback, useMemo, useEffect } from 'react';
import { Viewer, Entity, PointGraphics, LabelGraphics } from 'resium';
import { Cartesian3, Color } from 'cesium';

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
  const [viewer, setViewer] = useState(null);
  const [isReady, setIsReady] = useState(false);
  const [error, setError] = useState(null);

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
    if (!viewer || !targetEvent || !targetEvent.lat || !targetEvent.lon) return;

    console.log(`🚁 Flying to ${targetEvent.title}`);

    const destination = Cartesian3.fromDegrees(targetEvent.lon, targetEvent.lat, 15000000);

    viewer.camera.flyTo({
      destination,
      orientation: {
        heading: 0.0,
        pitch: -1.57,
        roll: 0.0
      },
      duration: 3.0
    });
  }, [viewer]);

  // Effect to handle navigation target changes
  React.useEffect(() => {
    if (navigationTarget && isReady) {
      handleCameraFlyTo(navigationTarget);
    }
  }, [navigationTarget, isReady, handleCameraFlyTo]);

  // Create entities for events
  const eventEntities = useMemo(() => {
    if (!events.length) return [];

    return events.map((event) => {
      if (!event.lat || !event.lon) return null;

      const position = Cartesian3.fromDegrees(event.lon, event.lat, 0);
      const isSelected = selectedEvent?.id === event.id;

      return (
        <Entity
          key={event.id}
          position={position}
          onClick={handleEntityClick}
          properties={{
            eventData: event
          }}
        >
          <PointGraphics
            pixelSize={isSelected ? 12 : 8}
            color={isSelected ? Color.YELLOW : Color.fromCssColorString(event.color || '#ff6b6b')}
            outlineColor={Color.BLACK}
            outlineWidth={2}
            heightReference="CLAMP_TO_GROUND"
          />
          {isSelected && (
            <LabelGraphics
              text={event.title}
              font="12pt sans-serif"
              pixelOffset={new Cartesian3(0, -50, 0)}
              fillColor={Color.WHITE}
              outlineColor={Color.BLACK}
              outlineWidth={2}
              style="FILL_AND_OUTLINE"
              verticalOrigin="BOTTOM"
            />
          )}
        </Entity>
      );
    }).filter(Boolean);
  }, [events, selectedEvent, handleEntityClick]);

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

  return (
    <div className={className}>
      <Viewer
        full
        onMount={handleViewerReady}
        terrainProvider={terrainEnabled ? undefined : false}
        baseLayerPicker={false}
        geocoder={false}
        homeButton={false}
        sceneModePicker={false}
        navigationHelpButton={false}
        animation={false}
        timeline={false}
        fullscreenButton={false}
        vrButton={false}
        infoBox={false}
        selectionIndicator={true}
        onError={(error) => {
          console.error('❌ Resium Viewer error:', error);
          setError(`Resium error: ${error.message}`);
        }}
      >
        {eventEntities}
      </Viewer>
    </div>
  );
};

export default ResiumGlobe;