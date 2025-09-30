/**
 * Environment setup for development
 * This file handles React DevTools disabling and environment variable setup
 */

// Disable React DevTools in a safe way
if (typeof window !== 'undefined') {
  const mockHook = {
    isDisabled: true,
    supportsFiber: true,
    inject: () => {},
    onCommitFiberRoot: () => {},
    onCommitFiberUnmount: () => {},
    onScheduleWork: () => {},
    onCancelWork: () => {},
    onCompleteWork: () => {},
    onScheduleRefresh: () => {},
    onScheduleReplace: () => {}
  };

  // Check if the hook already exists (browser extension)
  const existingHook = window.__REACT_DEVTOOLS_GLOBAL_HOOK__;

  if (existingHook) {
    // If hook exists, patch it to be disabled
    try {
      if (typeof existingHook === 'object') {
        existingHook.isDisabled = true;
        // Override the inject method to prevent React DevTools from working
        existingHook.inject = () => {};
        existingHook.onCommitFiberRoot = () => {};
        existingHook.onCommitFiberUnmount = () => {};
      }
    } catch (e) {
      // Silently ignore - extension might have locked the properties
    }
  } else {
    // Try to set our mock hook only if none exists
    try {
      window.__REACT_DEVTOOLS_GLOBAL_HOOK__ = mockHook;
    } catch (e) {
      // Silently ignore - we can't control the extension
    }
  }
}

// Export empty object for ES module compatibility
export default {};
