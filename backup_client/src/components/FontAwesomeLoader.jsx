import React, { useEffect, useState } from 'react';

// FontAwesome CDN loader with proper error handling
const FontAwesomeLoader = ({ children }) => {
  const [fontAwesomeLoaded, setFontAwesomeLoaded] = useState(false);

  useEffect(() => {
    // Check if FontAwesome is already loaded
    const checkFontAwesome = () => {
      const testElement = document.createElement('div');
      testElement.className = 'fas fa-home';
      testElement.style.position = 'absolute';
      testElement.style.visibility = 'hidden';
      testElement.style.fontSize = '0px';
      document.body.appendChild(testElement);

      const computedStyle = window.getComputedStyle(testElement, '::before');
      const isLoaded = computedStyle.content !== 'none' && computedStyle.content !== '';

      document.body.removeChild(testElement);
      return isLoaded;
    };

    // Check if already loaded
    if (checkFontAwesome()) {
      setFontAwesomeLoaded(true);
      return;
    }

    // Load FontAwesome from CDN
    let linkElement = document.querySelector('link[href*="font-awesome"]');

    if (!linkElement) {
      linkElement = document.createElement('link');
      linkElement.rel = 'stylesheet';
      linkElement.href = 'https://use.fontawesome.com/releases/v7.0.0/css/all.css';
      linkElement.integrity = 'sha512-DxV+EoADOkOygM4IR9yXP8Sb2qwgidEmeqAEmDKIOfPRQZOWbXCzLC6vjbZyy0vPisbH2SyW27+ddLVCN+OMzQ==';
      linkElement.crossOrigin = 'anonymous';
      linkElement.referrerPolicy = 'no-referrer';
      document.head.appendChild(linkElement);
    }

    // Check for loading completion
    let attempts = 0;
    const checkInterval = setInterval(() => {
      attempts++;
      if (checkFontAwesome() || attempts > 50) { // Max 5 seconds
        setFontAwesomeLoaded(true);
        clearInterval(checkInterval);
      }
    }, 100);

    // Also listen for the load event
    const handleLoad = () => {
      setTimeout(() => {
        setFontAwesomeLoaded(true);
      }, 50);
    };

    linkElement.addEventListener('load', handleLoad);

    // Cleanup
    return () => {
      clearInterval(checkInterval);
      linkElement.removeEventListener('load', handleLoad);
    };
  }, []);

  return (
    <>
      {children}
      {!fontAwesomeLoaded && (
        <div className="fixed top-4 right-4 bg-green-100 border border-green-300 text-green-800 px-3 py-2 rounded text-xs z-50">
          Loading FontAwesome...
        </div>
      )}
    </>
  );
};

export default FontAwesomeLoader;
