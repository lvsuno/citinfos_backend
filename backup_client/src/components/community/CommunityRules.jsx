import React, { useState } from 'react';
import { BookOpenIcon, ExclamationTriangleIcon, ChevronDownIcon, ChevronUpIcon } from '@heroicons/react/24/outline';

/**
 * CommunityRules - Displays community rules in a formatted card
 * Rules are stored as key-value pairs in the community.rules field
 */
const CommunityRules = ({ rules, community, className = '', collapsible = false, defaultCollapsed = false }) => {
  const [isCollapsed, setIsCollapsed] = useState(defaultCollapsed);

  const handleToggle = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsCollapsed(!isCollapsed);
  };

  // Handle different rule formats from the backend
  const formatRules = (rulesData) => {
    if (!rulesData) return [];

    // If rules is an array of objects with name/description
    if (Array.isArray(rulesData)) {
      return rulesData.filter(rule => rule && (rule.name || rule.title)).map(rule => ({
        key: rule.name || rule.title,
        value: rule.description || rule.content || ''
      }));
    }

    // If rules is an object (key-value pairs)
    if (typeof rulesData === 'object') {
      return Object.entries(rulesData).map(([key, value]) => ({
        key,
        value: value || ''
      }));
    }

    return [];
  };

  const formattedRules = formatRules(rules);

  if (formattedRules.length === 0) {
    return (
      <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <BookOpenIcon className="h-5 w-5 text-gray-400" />
            <h3 className="text-lg font-semibold text-gray-900">Community Rules</h3>
          </div>
          {collapsible && (
            <button
              type="button"
              onClick={handleToggle}
              className="flex items-center space-x-2 px-3 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-all duration-200 border border-gray-200 hover:border-gray-300"
              title={isCollapsed ? 'Show community rules' : 'Hide community rules'}
            >
              <span>{isCollapsed ? 'Show Rules' : 'Hide Rules'}</span>
              {isCollapsed ? (
                <ChevronDownIcon className="h-4 w-4" />
              ) : (
                <ChevronUpIcon className="h-4 w-4" />
              )}
            </button>
          )}
        </div>
        {!isCollapsed && (
          <div className="text-center py-6">
            <ExclamationTriangleIcon className="h-8 w-8 text-gray-300 mx-auto mb-2" />
            <p className="text-sm text-gray-500">No specific rules have been set for this community.</p>
            <p className="text-xs text-gray-400 mt-1">Please follow general community guidelines.</p>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <BookOpenIcon className="h-5 w-5 text-blue-600" />
          <h3 className="text-lg font-semibold text-gray-900">Community Rules</h3>
          <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full font-medium">
            {formattedRules.length}
          </span>
        </div>
        {collapsible && (
          <button
            type="button"
            onClick={handleToggle}
            className="flex items-center space-x-2 px-3 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-all duration-200 border border-gray-200 hover:border-gray-300"
            title={isCollapsed ? 'Show community rules' : 'Hide community rules'}
          >
            <span>{isCollapsed ? 'Show Rules' : 'Hide Rules'}</span>
            {isCollapsed ? (
              <ChevronDownIcon className="h-4 w-4" />
            ) : (
              <ChevronUpIcon className="h-4 w-4" />
            )}
          </button>
        )}
      </div>

      {!isCollapsed && (
        <>
          <div className="space-y-4">
            {formattedRules.map((rule, index) => (
              <div key={index} className="border-l-4 border-blue-500 bg-blue-50 p-4 rounded-r-lg">
                <div className="flex items-start">
                  <span className="flex-shrink-0 w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-xs font-bold mr-3 mt-0.5">
                    {index + 1}
                  </span>
                  <div className="flex-1 min-w-0">
                    <h4 className="text-sm font-semibold text-blue-900 mb-1">
                      {rule.key}
                    </h4>
                    {rule.value && (
                      <p className="text-sm text-blue-800 leading-relaxed">
                        {rule.value}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Footer reminder */}
          <div className="mt-6 pt-4 border-t border-gray-200">
            <div className="flex items-start space-x-2">
              <ExclamationTriangleIcon className="h-4 w-4 text-amber-500 mt-0.5 flex-shrink-0" />
              <p className="text-xs text-gray-600">
                Please follow these rules to maintain a positive community environment.
                Violations may result in warnings or removal from the community.
              </p>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default CommunityRules;
