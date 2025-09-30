// Cesium performance optimizations
export const CESIUM_CONFIG = {
  // Optimize for faster loading
  FAST_LOAD: {
    contextOptions: {
      webgl: {
        alpha: false,
        antialias: false,
        preserveDrawingBuffer: false,
        failIfMajorPerformanceCaveat: false,
        powerPreference: 'high-performance'
      }
    },
    // Disable heavy features initially
    shadows: false,
    terrainProvider: undefined,
    // Use simpler imagery for faster loading
    imageryProvider: 'OSM', // OpenStreetMap is faster than satellite
    // Reduce quality for performance
    maximumScreenSpaceError: 4, // Higher = lower quality but faster
    tileCacheSize: 50 // Smaller cache for faster startup
  },

  // High quality settings (can be applied after initial load)
  HIGH_QUALITY: {
    shadows: true,
    terrainProvider: 'WORLD_TERRAIN',
    imageryProvider: 'SATELLITE',
    maximumScreenSpaceError: 2,
    tileCacheSize: 100
  },

  // Ion access token
  ION_TOKEN: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiJlYWE1OWUxNy1mMWZiLTQzYjYtYTQ0OS1kMWFjYmFkNjc5YzciLCJpZCI6NTc3MzMsImlhdCI6MTYyNzg0NTE4Mn0.XcKpgANiY19MC4bdFUXMVEBToBmqS8kuYpUlxJHYZxk',

  // Timeout settings
  TIMEOUTS: {
    SCRIPT_LOAD: 15000, // 15 seconds to load Cesium script
    VIEWER_INIT: 10000, // 10 seconds to create viewer
    OVERALL: 30000      // 30 seconds total
  }
};

// Check if WebGL is supported
export const checkWebGLSupport = () => {
  try {
    const canvas = document.createElement('canvas');
    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
    return !!gl;
  } catch (e) {
    return false;
  }
};

// Check browser compatibility
export const checkBrowserCompatibility = () => {
  const userAgent = navigator.userAgent;
  const isChrome = /Chrome/.test(userAgent) && !/Edge/.test(userAgent);
  const isFirefox = /Firefox/.test(userAgent);
  const isSafari = /Safari/.test(userAgent) && !/Chrome/.test(userAgent);
  const isEdge = /Edge/.test(userAgent);

  return {
    isSupported: isChrome || isFirefox || isSafari || isEdge,
    browser: isChrome ? 'Chrome' : isFirefox ? 'Firefox' : isSafari ? 'Safari' : isEdge ? 'Edge' : 'Unknown',
    hasWebGL: checkWebGLSupport()
  };
};

// Preload check for Cesium assets
export const preloadCesiumAssets = () => {
  return new Promise((resolve, reject) => {
    const timeout = setTimeout(() => {
      reject(new Error('Cesium assets preload timeout'));
    }, CESIUM_CONFIG.TIMEOUTS.SCRIPT_LOAD);

    // Check if Cesium is already loaded
    if (window.Cesium) {
      clearTimeout(timeout);
      resolve(true);
      return;
    }

    // Check if Cesium script exists
    fetch('/cesium/Cesium.js', { method: 'HEAD' })
      .then(response => {
        if (response.ok) {
          // Try to access widgets.css as well
          return fetch('/cesium/Widgets/widgets.css', { method: 'HEAD' });
        }
        throw new Error('Cesium.js not found');
      })
      .then(response => {
        if (response.ok) {
          clearTimeout(timeout);
          resolve(true);
        } else {
          throw new Error('Cesium widgets.css not found');
        }
      })
      .catch(error => {
        clearTimeout(timeout);
        reject(error);
      });
  });
};