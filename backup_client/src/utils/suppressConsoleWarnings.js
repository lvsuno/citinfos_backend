// Comprehensive development console warning suppressor
export const suppressConsoleWarnings = () => {
  if (process.env.NODE_ENV === 'development') {
    // Store original console methods
    const originalError = console.error;
    const originalWarn = console.warn;
    const originalInfo = console.info;
    const originalLog = console.log;

    // Override console methods to filter source map and React DevTools warnings
    console.error = (...args) => {
      const message = args.join(' ');

      // Skip source map related errors
      if (message.includes('source map')) return;
      if (message.includes('installHook.js.map')) return;
      if (message.includes('react_devtools_backend')) return;
      if (message.includes('No sources are declared')) return;
      if (message.includes('JSON.parse: unexpected character')) return;
      if (message.includes('can\'t access property "sources"')) return;
      if (message.includes('%3Canonymous%20code%3E')) return;
      if (message.includes('__REACT_DEVTOOLS_GLOBAL_HOOK__')) return;
      if (message.includes('getter-only property')) return;
      if (message.includes('Erreur dans les liens source')) return;

      // Call original console.error for other messages
      originalError.apply(console, args);
    };

    console.warn = (...args) => {
      const message = args.join(' ');

      // Skip source map related warnings
      if (message.includes('source map')) return;
      if (message.includes('SOURCEMAP_ERROR')) return;
      if (message.includes('installHook.js.map')) return;

      // Call original console.warn for other messages
      originalWarn.apply(console, args);
    };

    console.info = (...args) => {
      const message = args.join(' ');

      // Skip source map related info messages
      if (message.includes('source map')) return;
      if (message.includes('installHook.js.map')) return;

      // Call original console.info for other messages
      originalInfo.apply(console, args);
    };

    // Intercept browser's native source map error reporting
    const originalDevToolsError = window.console.error;
    if (originalDevToolsError && originalDevToolsError !== console.error) {
      window.console.error = (...args) => {
        const message = args.join(' ');
        if (message.includes('source map') ||
            message.includes('installHook.js.map') ||
            message.includes('JSON.parse: unexpected character') ||
            message.includes('Erreur dans les liens source')) {
          return;
        }
        originalDevToolsError.apply(window.console, args);
      };
    }

    // Suppress window errors related to source maps and React DevTools
    const originalWindowError = window.onerror;
    window.onerror = (message, source, lineno, colno, error) => {
      // Skip source map related errors
      if (message && message.includes && message.includes('source map')) return true;
      if (source && source.includes && source.includes('.map')) return true;
      if (message && message.includes && message.includes('__REACT_DEVTOOLS_GLOBAL_HOOK__')) return true;
      if (message && message.includes && message.includes('getter-only property')) return true;
      if (message && message.includes && message.includes('installHook.js.map')) return true;
      if (message && message.includes && message.includes('JSON.parse: unexpected character')) return true;

      // Call original error handler for other errors
      if (originalWindowError) {
        return originalWindowError(message, source, lineno, colno, error);
      }
      return false;
    };

    // Handle unhandled promise rejections related to React DevTools
    const originalUnhandledRejection = window.onunhandledrejection;
    window.onunhandledrejection = (event) => {
      const message = event.reason?.message || '';

      // Skip React DevTools related rejections
      if (message.includes('__REACT_DEVTOOLS_GLOBAL_HOOK__')) {
        event.preventDefault();
        return true;
      }
      if (message.includes('getter-only property')) {
        event.preventDefault();
        return true;
      }
      if (message.includes('source map')) {
        event.preventDefault();
        return true;
      }

      // Call original handler for other rejections
      if (originalUnhandledRejection) {
        return originalUnhandledRejection(event);
      }
      return false;
    };

    // Override navigator.sendBeacon to prevent telemetry related to source maps
    const originalSendBeacon = navigator.sendBeacon;
    navigator.sendBeacon = function(url, data) {
      // Skip source map related telemetry
      if (url && (url.includes('sourcemap') || url.includes('.map'))) {
        return true; // Pretend it was sent successfully
      }
      return originalSendBeacon.call(this, url, data);
    };

    // Disable source map debugging in development tools if possible
    try {
      if (window.chrome && window.chrome.runtime) {
        // Chrome DevTools specific suppression
        const style = document.createElement('style');
        style.innerHTML = `
          .console-error-level .console-message-text:has-text("source map"),
          .console-error-level .console-message-text:has-text("installHook.js.map") {
            display: none !important;
          }
        `;
        document.head.appendChild(style);
      }
    } catch (e) {
      // Silently ignore if we can't access chrome APIs
    }

    console.log('🛠️ Enhanced development console filtering enabled - comprehensive source map suppression active');
  }
};
