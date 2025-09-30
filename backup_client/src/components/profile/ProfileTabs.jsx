import React from 'react';
import PropTypes from 'prop-types';

/* ProfileTabs
   Props: tabs: {key:string,label:string}[]
          active: string
          onChange: (key)=>void
*/
const ProfileTabs = ({ tabs, active, onChange }) => {
  return (
    <div className="flex gap-6 border-b border-gray-200 px-4 sm:px-6">
      {tabs.map(t => (
        <button key={t.key} onClick={()=>onChange(t.key)} className={`py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${active===t.key ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}`}>{t.label}</button>
      ))}
    </div>
  );
};

ProfileTabs.propTypes = { tabs: PropTypes.array, active: PropTypes.string, onChange: PropTypes.func };

export default ProfileTabs;
