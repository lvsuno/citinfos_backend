import React, { useState } from 'react';
import { SparklesIcon, ArrowPathIcon, ClipboardIcon } from '@heroicons/react/24/outline';
import api from '../services/axiosConfig.js'; // Use configured axios instance

const PasswordGenerator = ({ onPasswordSelect }) => {
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showGenerator, setShowGenerator] = useState(false);

  const generatePasswords = async () => {
    setLoading(true);
    try {
      const response = await api.get('/auth/generate-passwords/?count=3');

      if (response.status === 200) {
        const data = response.data;
        setSuggestions(data.suggestions || []);
      }
    } catch (error) {
      console.error('Error generating passwords:', error);
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = async (password) => {
    try {
      await navigator.clipboard.writeText(password);
      // You could add a toast notification here
    } catch (error) {
      console.error('Failed to copy password:', error);
    }
  };

  const selectPassword = (password) => {
    onPasswordSelect(password);
    setShowGenerator(false);
  };

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => {
          setShowGenerator(!showGenerator);
          if (!showGenerator && suggestions.length === 0) {
            generatePasswords();
          }
        }}
        className="text-blue-500 hover:text-blue-700 p-1 rounded-md hover:bg-blue-50 transition-colors"
        title="Generate strong password"
      >
        <SparklesIcon className="h-4 w-4" />
      </button>

      {showGenerator && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-black bg-opacity-25 z-40"
            onClick={() => setShowGenerator(false)}
          ></div>

          {/* Modal */}
          <div className="fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-80 bg-white border border-gray-200 rounded-lg shadow-xl p-4 z-50 max-h-96 overflow-y-auto">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-gray-800">Password Suggestions</h3>
              <button
                type="button"
                onClick={generatePasswords}
                disabled={loading}
                className="text-blue-500 hover:text-blue-700 p-1 rounded-md hover:bg-blue-50 transition-colors disabled:opacity-50"
                title="Generate new passwords"
              >
                <ArrowPathIcon className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
              </button>
            </div>

            {loading ? (
              <div className="text-center py-4">
                <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
                <p className="text-sm text-gray-600 mt-2">Generating passwords...</p>
              </div>
            ) : suggestions.length > 0 ? (
              <div className="space-y-2">
                {suggestions.map((password, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-2 bg-gray-50 rounded-md hover:bg-gray-100 transition-colors"
                  >
                    <code className="text-sm font-mono text-gray-800 flex-1 mr-2 break-all">
                      {password}
                    </code>
                    <div className="flex gap-1">
                      <button
                        type="button"
                        onClick={() => copyToClipboard(password)}
                        className="text-gray-500 hover:text-gray-700 p-1 rounded-md hover:bg-gray-200 transition-colors"
                        title="Copy to clipboard"
                      >
                        <ClipboardIcon className="h-3 w-3" />
                      </button>
                      <button
                        type="button"
                        onClick={() => selectPassword(password)}
                        className="text-xs bg-blue-500 hover:bg-blue-600 text-white px-2 py-1 rounded-md transition-colors"
                      >
                        Use
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-600 text-center py-4">
                Click refresh to generate strong passwords
              </p>
            )}

            <div className="mt-3 pt-3 border-t border-gray-200">
              <p className="text-xs text-gray-500">
                <strong>Requirements:</strong> 8+ chars, uppercase, lowercase, numbers, and special characters (!@#$%^&*)
              </p>
            </div>

            <button
              type="button"
              onClick={() => setShowGenerator(false)}
              className="absolute top-2 right-2 text-gray-400 hover:text-gray-600 p-1 rounded hover:bg-gray-100"
              title="Close"
            >
              ×
            </button>
          </div>
        </>
      )}
    </div>
  );
};

export default PasswordGenerator;