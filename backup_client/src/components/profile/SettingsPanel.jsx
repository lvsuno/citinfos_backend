import React from 'react';

/* SettingsPanel placeholder */
const SettingsPanel = () => {
  return (
    <div className="space-y-6">
      <section>
        <h3 className="text-sm font-semibold text-gray-700 mb-2">Account</h3>
        <p className="text-xs text-gray-500">Email / password management coming soon.</p>
      </section>
      <section>
        <h3 className="text-sm font-semibold text-gray-700 mb-2">Privacy</h3>
        <p className="text-xs text-gray-500">Visibility and data controls will appear here.</p>
      </section>
      <section>
        <h3 className="text-sm font-semibold text-gray-700 mb-2">Notifications</h3>
        <p className="text-xs text-gray-500">Fine-grained notification settings planned.</p>
      </section>
    </div>
  );
};

export default SettingsPanel;
