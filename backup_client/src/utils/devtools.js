/**
 * Development utilities to handle console warnings and source map issues
 */

// Only run in development
if (import.meta.env.DEV) {
  // Store original console methods
  const originalConsoleWarn = console.warn;
  const originalConsoleError = console.error;

  // List of patterns to suppress
  const suppressPatterns = [
    'installHook.js.map',
    'react_devtools_backend',
    'No sources are declared in this source map',
    'JSON.parse: unexpected character',
    'can\'t access property "sources", map is undefined',
    'Erreur dans les liens source',
    'Source Map Error'
  ];

  // Enhanced console.warn override
  console.warn = function(...args) {
    const message = args.join(' ');

    // Check if this warning should be suppressed
    const shouldSuppress = suppressPatterns.some(pattern =>
      message.toLowerCase().includes(pattern.toLowerCase())
    );

    if (!shouldSuppress) {
      originalConsoleWarn.apply(console, args);
    }
  };

  // Enhanced console.error override for source map errors
  console.error = function(...args) {
    const message = args.join(' ');

    // Check if this error should be suppressed
    const shouldSuppress = suppressPatterns.some(pattern =>
      message.toLowerCase().includes(pattern.toLowerCase())
    );

    if (!shouldSuppress) {
      originalConsoleError.apply(console, args);
    }
  };

  // Handle global error events
  window.addEventListener('error', function(event) {
    if (event.filename && suppressPatterns.some(pattern =>
      event.filename.includes(pattern) ||
      (event.message && event.message.includes(pattern))
    )) {
      event.stopPropagation();
      event.preventDefault();
      return false;
    }
  }, true);

  // Handle unhandled promise rejections that might be source map related
  window.addEventListener('unhandledrejection', function(event) {
    if (event.reason && typeof event.reason === 'string') {
      const shouldSuppress = suppressPatterns.some(pattern =>
        event.reason.toLowerCase().includes(pattern.toLowerCase())
      );

      if (shouldSuppress) {
        event.preventDefault();
        return false;
      }
    }
  });

  console.log('🛠️ Development console filtering enabled - source map warnings suppressed');
}

export default {};
