// Source map suppression - runs early to intercept network requests
(function() {
  'use strict';

  // Aggressive source map URL patterns
  const sourceMapPatterns = [
    '.map',
    'installHook.js.map',
    'installhook.js.map', // case insensitive
    'react_devtools_backend',
    'devtools_backend',
    '%3Canonymous%20code%3E',
    '%3canonymous%20code%3e', // case variants
    '<anonymous code>',
    'devtools'
  ];

  // Valid complete source map structure with dummy content
  const validSourceMap = JSON.stringify({
    version: 3,
    file: "blocked.js",
    sourceRoot: "",
    sources: ["blocked.js"],
    names: [],
    mappings: "AAAA", // Base64 VLQ for a simple mapping
    sourcesContent: ["// Source map blocked by development server"]
  });

  function isSourceMapRequest(url) {
    if (!url) return false;
    const decodedUrl = decodeURIComponent(url).toLowerCase();
    return sourceMapPatterns.some(pattern =>
      decodedUrl.includes(pattern.toLowerCase())
    );
  }

  // Intercept fetch requests to block source map files
  const originalFetch = window.fetch;
  window.fetch = function(...args) {
    const [resource] = args;
    const url = typeof resource === 'string' ? resource : (resource && resource.url);

    if (isSourceMapRequest(url)) {
      // Return a resolved promise with complete valid source map
      return Promise.resolve(new Response(validSourceMap, {
        status: 200,
        statusText: 'OK',
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': 'no-cache'
        }
      }));
    }

    return originalFetch.apply(this, args);
  };

  // Enhanced XMLHttpRequest interception
  const originalOpen = XMLHttpRequest.prototype.open;
  XMLHttpRequest.prototype.open = function(method, url, ...rest) {
    if (isSourceMapRequest(url)) {
      // Mock successful response
      const mockXHR = this;

      // Override properties
      Object.defineProperty(mockXHR, 'status', {
        value: 200,
        writable: false
      });
      Object.defineProperty(mockXHR, 'statusText', {
        value: 'OK',
        writable: false
      });
      Object.defineProperty(mockXHR, 'responseText', {
        value: validSourceMap,
        writable: false
      });
      Object.defineProperty(mockXHR, 'readyState', {
        value: 4,
        writable: false
      });

      // Override methods to prevent actual network calls
      mockXHR.send = function() {
        setTimeout(() => {
          if (mockXHR.onreadystatechange) {
            mockXHR.onreadystatechange();
          }
          if (mockXHR.onload) {
            mockXHR.onload();
          }
        }, 0);
      };

      return;
    }

    return originalOpen.call(this, method, url, ...rest);
  };

  // Block dynamic script loading of source maps
  const originalCreateElement = document.createElement;
  document.createElement = function(tagName) {
    const element = originalCreateElement.call(this, tagName);

    if (tagName.toLowerCase() === 'script') {
      const originalSetAttribute = element.setAttribute;
      element.setAttribute = function(name, value) {
        if (name === 'src' && isSourceMapRequest(value)) {
          // Don't set the src attribute for source map files
          return;
        }
        return originalSetAttribute.call(this, name, value);
      };

      // Also override the src property
      let srcValue = '';
      Object.defineProperty(element, 'src', {
        get: function() { return srcValue; },
        set: function(value) {
          if (!isSourceMapRequest(value)) {
            srcValue = value;
            originalSetAttribute.call(this, 'src', value);
          }
        }
      });
    }

    return element;
  };

  console.log('🚫 Enhanced source map network interception active');
})();
