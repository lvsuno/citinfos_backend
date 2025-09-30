import React, { useState, useEffect } from 'react';

const ResiumGlobeSimple = ({ className = '', events = [] }) => {
  const [cesiumStatus, setCesiumStatus] = useState({ loading: true });

  useEffect(() => {
    const checkCesium = async () => {
      try {
        // Try to import Cesium
        const Cesium = await import('cesium');

        if (!Cesium || !Cesium.Viewer) {
          throw new Error('Cesium Viewer not available');
        }

        console.log('✅ Cesium available:', {
          Viewer: !!Cesium.Viewer,
          Cartesian3: !!Cesium.Cartesian3,
          Color: !!Cesium.Color,
          Ion: !!Cesium.Ion
        });

        setCesiumStatus({
          loading: false,
          success: true,
          cesium: Cesium,
          message: 'Cesium loaded successfully!'
        });
      } catch (error) {
        console.error('❌ Cesium check failed:', error);
        setCesiumStatus({
          loading: false,
          success: false,
          error: error.message
        });
      }
    };

    checkCesium();
  }, []);

  if (cesiumStatus.loading) {
    return (
      <div className={`flex items-center justify-center bg-gray-900 text-white ${className}`}>
        <div className="text-center">
          <div className="text-xl mb-2">🌍</div>
          <div>Testing Cesium...</div>
        </div>
      </div>
    );
  }

  if (!cesiumStatus.success) {
    return (
      <div className={`flex items-center justify-center bg-red-900 text-white ${className}`}>
        <div className="text-center">
          <div className="text-xl mb-2">❌</div>
          <div>Cesium Error</div>
          <div className="text-sm text-red-200 mt-2">
            {cesiumStatus.error}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-gray-800 text-white ${className}`}>
      <div className="p-4">
        <div className="text-center mb-4">
          <div className="text-xl mb-2">✅</div>
          <div>Cesium Ready!</div>
          <div className="text-sm text-gray-300">
            {cesiumStatus.message}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="bg-gray-700 p-2 rounded">
            <strong>Events:</strong> {events.length}
          </div>
          <div className="bg-gray-700 p-2 rounded">
            <strong>Cesium:</strong> Available
          </div>
        </div>

        <div className="mt-4 text-center text-sm text-gray-400">
          Next: Enable Resium Components
        </div>
      </div>
    </div>
  );
};

export default ResiumGlobeSimple;