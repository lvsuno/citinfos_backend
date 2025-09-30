import React, { useState } from 'react';

export const Tabs = ({ children, defaultValue, className = '' }) => {
  const [activeTab, setActiveTab] = useState(defaultValue);

  return (
    <div className={`tabs ${className}`} data-active-tab={activeTab}>
      {React.Children.map(children, child =>
        React.cloneElement(child, { activeTab, setActiveTab })
      )}
    </div>
  );
};

export const TabsList = ({ children, className = '', activeTab, setActiveTab }) => (
  <div className={`flex space-x-1 bg-gray-100 p-1 rounded-lg ${className}`}>
    {React.Children.map(children, child =>
      React.cloneElement(child, { activeTab, setActiveTab })
    )}
  </div>
);

export const TabsTrigger = ({ children, value, className = '', activeTab, setActiveTab }) => (
  <button
    className={`flex-1 py-2 px-4 text-sm font-medium rounded-md transition-colors ${
      activeTab === value
        ? 'bg-white text-blue-600 shadow-sm'
        : 'text-gray-600 hover:text-gray-900'
    } ${className}`}
    onClick={() => setActiveTab(value)}
  >
    {children}
  </button>
);

export const TabsContent = ({ children, value, className = '', activeTab }) => {
  if (activeTab !== value) return null;

  return (
    <div className={`mt-4 ${className}`}>
      {children}
    </div>
  );
};
