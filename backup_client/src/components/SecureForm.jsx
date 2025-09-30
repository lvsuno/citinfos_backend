/**
 * Security Form Wrapper Component
 *
 * This component wraps forms containing sensitive data to provide additional security
 */

import React, { useEffect, useRef } from 'react';
import { preventDevToolsPasswordExposure } from '../utils/passwordSecurity';

export const SecureForm = ({ children, onSubmit, ...props }) => {
  const formRef = useRef(null);

  useEffect(() => {
    // Set up security measures when form mounts
    preventDevToolsPasswordExposure();

    // Add form security attributes
    if (formRef.current) {
      formRef.current.setAttribute('autocomplete', 'off');
      formRef.current.setAttribute('data-secure', 'true');
    }
  }, []);

  const handleSecureSubmit = async (e) => {
    e.preventDefault();

    if (onSubmit) {
      try {
        // Wait for the onSubmit handler to complete
        // The parent handler (Login.jsx) will handle password clearing
        await onSubmit(e);
      } catch (error) {
        console.error('Form submission error:', error);
        // Only clear passwords if there's an error in the form handler itself
        setTimeout(() => {
          if (formRef.current) {
            const passwordFields = formRef.current.querySelectorAll('input[type="password"]');
            passwordFields.forEach(field => {
              field.value = '';
              field.removeAttribute('value');
            });
          }
        }, 100);
      }
    }
  };

  return (
    <form
      ref={formRef}
      onSubmit={handleSecureSubmit}
      autoComplete="off"
      data-secure="true"
      {...props}
    >
      {children}
    </form>
  );
};