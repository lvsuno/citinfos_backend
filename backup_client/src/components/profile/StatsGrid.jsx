import React from 'react';
import PropTypes from 'prop-types';

/* StatsGrid
   Props: stats: Record<string, number>
*/
const StatsGrid = ({ stats }) => {
  if (!stats) return null;
  return (
    <dl className="grid grid-cols-2 gap-4">
      {Object.entries(stats).map(([k, v]) => (
        <div key={k} className="bg-gray-50 rounded-md p-3 border border-gray-100">
          <dt className="text-[10px] uppercase tracking-wide text-gray-500">{k.replace(/_/g, ' ')}</dt>
            <dd className="mt-1 text-sm font-semibold text-gray-900">{v}</dd>
        </div>
      ))}
    </dl>
  );
};

StatsGrid.propTypes = { stats: PropTypes.object };

export default StatsGrid;
