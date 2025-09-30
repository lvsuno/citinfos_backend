import PropTypes from 'prop-types';

const CommunityDashboard = ({ ...props }) => {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
      <div className="flex items-center mb-4">
        <div className="h-8 w-8 bg-blue-100 rounded-lg flex items-center justify-center mr-3">
          <span className="text-blue-600 text-sm">🔧</span>
        </div>
        <div>
          <h3 className="text-lg font-medium text-gray-900">CommunityDashboard</h3>
          <p className="text-sm text-gray-500">CommunityDashboard component - ready for implementation</p>
        </div>
      </div>
      <div className="border-t border-gray-200 pt-4">
        <div className="text-center py-8">
          <div className="text-gray-400 text-4xl mb-2">⚙️</div>
          <p className="text-gray-600 text-sm">Component ready for development</p>
        </div>
      </div>
    </div>
  );
};

CommunityDashboard.propTypes = {
  // Add specific PropTypes as needed
};

export default CommunityDashboard;
