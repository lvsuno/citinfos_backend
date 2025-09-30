/**
 * Password Security Utilities
 *
 * This module provides utilities for handling passwords securely on the client side
 */

/**
 * Securely clear a password field and its value from memory
 * @param {HTMLInputElement} passwordInput - The password input element
 */
export const clearPasswordField = (passwordInput) => {
  if (passwordInput) {
    // Clear the input value
    passwordInput.value = '';

    // Clear the React state value by triggering onChange with empty value
    const event = new Event('input', { bubbles: true });
    Object.defineProperty(event, 'target', { value: passwordInput });
    passwordInput.dispatchEvent(event);

    // Force blur to remove focus
    passwordInput.blur();
  }
};

/**
 * Clear password from React state
 * @param {Function} setPassword - React setState function for password
 */
export const clearPasswordState = (setPassword) => {
  if (typeof setPassword === 'function') {
    setPassword('');
  }
};

/**
 * Securely handle form submission with password clearing
 * @param {Event} event - Form submit event
 * @param {Object} credentials - Login credentials
 * @param {Function} loginFunction - Login function to call
 * @param {Function} setPassword - Password state setter
 * @param {HTMLInputElement} passwordInputRef - Password input reference
 */
export const secureLoginSubmit = async (
  event,
  credentials,
  loginFunction,
  setPassword,
  passwordInputRef
) => {
  event.preventDefault();

  try {
    // Store password temporarily for login
    const { username, password } = credentials;

    // Clear password from state immediately
    clearPasswordState(setPassword);
    clearPasswordField(passwordInputRef);

    // Perform login with temporary password variable
    const result = await loginFunction(username, password);

    // Clear the temporary password variable
    // (JavaScript will garbage collect, but we can help)
    credentials.password = '';

    return result;
  } catch (error) {
    // Clear any remaining password traces
    clearPasswordState(setPassword);
    clearPasswordField(passwordInputRef);
    throw error;
  }
};

/**
 * Disable browser password saving for sensitive forms
 * @param {HTMLFormElement} formElement - The form element
 */
export const disableBrowserPasswordSaving = (formElement) => {
  if (formElement) {
    // Disable autocomplete for the form
    formElement.setAttribute('autocomplete', 'off');

    // Find password inputs and disable autocomplete
    const passwordInputs = formElement.querySelectorAll('input[type="password"]');
    passwordInputs.forEach(input => {
      input.setAttribute('autocomplete', 'new-password');
      input.setAttribute('data-lpignore', 'true'); // LastPass ignore
    });
  }
};

/**
 * Create a secure password input with memory clearing
 * @param {HTMLInputElement} input - Password input element
 */
export const makePasswordInputSecure = (input) => {
  if (input) {
    // Disable autocomplete
    input.setAttribute('autocomplete', 'new-password');
    input.setAttribute('data-lpignore', 'true');

    // Function to continuously remove value attribute
    const removeValueAttribute = () => {
      if (input.hasAttribute('value')) {
        input.removeAttribute('value');
      }
    };

    // Set up mutation observer to watch for value attribute changes
    if (window.MutationObserver) {
      const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
          if (mutation.type === 'attributes' && mutation.attributeName === 'value') {
            removeValueAttribute();
          }
        });
      });

      observer.observe(input, {
        attributes: true,
        attributeFilter: ['value']
      });

      // Store observer reference for cleanup
      input._securityObserver = observer;
    }

    // Remove value attribute on various events
    const events = ['input', 'change', 'keyup', 'keydown', 'blur', 'focus'];
    events.forEach(eventType => {
      input.addEventListener(eventType, removeValueAttribute);
    });

    // Periodic cleanup every 50ms while field is active
    const intervalCleanup = setInterval(() => {
      removeValueAttribute();
    }, 50);

    // Prevent right-click context menu
    input.addEventListener('contextmenu', (e) => e.preventDefault());

    // Clear on page unload
    const handlePageUnload = () => {
      clearPasswordField(input);
      clearInterval(intervalCleanup);
      if (input._securityObserver) {
        input._securityObserver.disconnect();
      }
    };

    window.addEventListener('beforeunload', handlePageUnload);

    // Clear on visibility change (tab switch)
    const handleVisibilityChange = () => {
      if (document.hidden) {
        clearPasswordField(input);
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);

    // Store cleanup functions for manual cleanup
    input._securityCleanup = () => {
      clearInterval(intervalCleanup);
      if (input._securityObserver) {
        input._securityObserver.disconnect();
      }
      window.removeEventListener('beforeunload', handlePageUnload);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }
};

/**
 * Safe DOM inspection protection for password fields (React-compatible)
 * @param {HTMLInputElement} passwordInput - The password input element
 */
export const protectFromDOMInspection = (passwordInput) => {
  if (!passwordInput) return;

  // Less aggressive approach that doesn't break React form handling
  // Focus on preventing casual inspection without overriding core functionality

  // Add data attributes that obscure the field's purpose
  passwordInput.setAttribute('data-type', 'secure-input');
  passwordInput.setAttribute('data-lpignore', 'true');

  // Remove value attribute from DOM when not focused (but keep React functionality)
  const handleBlur = () => {
    // Only remove DOM attribute, don't touch React's value property
    passwordInput.removeAttribute('value');
  };

  const handleFocus = () => {
    // Ensure autocomplete is disabled
    passwordInput.setAttribute('autocomplete', 'new-password');
  };

  passwordInput.addEventListener('blur', handleBlur);
  passwordInput.addEventListener('focus', handleFocus);

  // Periodically clean DOM attribute (but preserve React functionality)
  const cleanupInterval = setInterval(() => {
    if (passwordInput && passwordInput.parentNode) {
      // Only remove the DOM attribute, not the React property
      if (document.activeElement !== passwordInput) {
        passwordInput.removeAttribute('value');
      }
    } else {
      clearInterval(cleanupInterval);
    }
  }, 1000);

  // Store cleanup function
  passwordInput._securityCleanup = () => {
    clearInterval(cleanupInterval);
    passwordInput.removeEventListener('blur', handleBlur);
    passwordInput.removeEventListener('focus', handleFocus);
  };
};

/**
 * Remove sensitive data from browser dev tools
 */
export const preventDevToolsPasswordExposure = () => {
  // Clear console history that might contain sensitive data
  if (typeof console !== 'undefined') {
    // Override console methods temporarily during login
    const originalLog = console.log;
    const originalError = console.error;
    const originalWarn = console.warn;

    const sanitizeArgs = (args) => {
      return args.map(arg => {
        if (typeof arg === 'string') {
          // Remove potential passwords from strings
          return arg.replace(/password[=:]\s*[^\s,}]*/gi, 'password=***');
        } else if (typeof arg === 'object' && arg !== null) {
          // Deep clone and sanitize objects
          const sanitized = JSON.parse(JSON.stringify(arg));
          if (sanitized.password) sanitized.password = '***';
          if (sanitized.Password) sanitized.Password = '***';
          return sanitized;
        }
        return arg;
      });
    };

    console.log = (...args) => originalLog(...sanitizeArgs(args));
    console.error = (...args) => originalError(...sanitizeArgs(args));
    console.warn = (...args) => originalWarn(...sanitizeArgs(args));

    // Restore after a short delay
    setTimeout(() => {
      console.log = originalLog;
      console.error = originalError;
      console.warn = originalWarn;
    }, 5000);
  }
};

/**
 * Detect if DevTools is open and warn user
 */
export const detectDevToolsAndWarn = () => {
  let devtools = { open: false, orientation: null };

  const threshold = 160;
  const setDevToolsStatus = (isOpen) => {
    if (isOpen && !devtools.open) {
      console.warn('⚠️ Developer Tools detected! Please close for security.');
      // You could also show a modal warning here
    }
    devtools.open = isOpen;
  };

  setInterval(() => {
    if (window.outerHeight - window.innerHeight > threshold ||
        window.outerWidth - window.innerWidth > threshold) {
      setDevToolsStatus(true);
    } else {
      setDevToolsStatus(false);
    }
  }, 500);
};
