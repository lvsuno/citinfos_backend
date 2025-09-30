import React from 'react';
import { ExclamationTriangleIcon, GlobeAmericasIcon, MapPinIcon } from '@heroicons/react/24/outline';
import { Link } from 'react-router-dom';

/**
 * GeoRestricted - Component to display when user is geo-restricted from accessing a community
 * This mirrors the functionality of communities/templates/communities/geo_restricted.html
 */
const GeoRestricted = ({
  error,
  onBrowseCommunities,
//   onUpdateLocation,
  className = ''
}) => {
  if (!error || error.error !== 'geo_restricted') {
    return null;
  }

  const {
    message = "This community has geographic restrictions.",
    community_name = "this community",
    current_location = "Unknown",
    profile_location = "Not set",
    user_traveling = false,
    actions = []
  } = error;

  return (
    <div className={`min-h-[60vh] bg-gray-50 flex items-center justify-center p-4 ${className}`}>
      <div className="max-w-2xl w-full">
        <div className="bg-white rounded-lg shadow-lg border-l-4 border-yellow-400">
          {/* Header */}
          <div className="bg-gradient-to-r from-yellow-500 to-orange-500 text-white p-6 rounded-t-lg">
            <div className="flex items-center">
              <GlobeAmericasIcon className="h-8 w-8 mr-3" />
              <h1 className="text-2xl font-semibold">Access Restricted</h1>
            </div>
          </div>

          {/* Main Content */}
          <div className="p-8">
            {/* Icon */}
            <div className="text-center mb-6">
              <MapPinIcon className="h-16 w-16 text-gray-400 mx-auto" />
            </div>

            {/* Main Message */}
            <h2 className="text-xl font-semibold text-center text-gray-900 mb-4">
              {message}
            </h2>

            <p className="text-gray-600 text-center mb-6">
              This community has geographic restrictions in place.
              Access is limited to users from specific regions or countries.
            </p>

            {/* Location Info */}
            <div className="bg-gray-50 rounded-lg p-4 mb-6">
              <h3 className="font-semibold text-gray-900 mb-3 flex items-center">
                <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500 mr-2" />
                Location Information
              </h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Community:</span>
                  <span className="font-medium text-gray-900">{community_name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Your Profile Location:</span>
                  <span className="font-medium text-gray-900">{profile_location}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Current Location:</span>
                  <span className="font-medium text-gray-900">{current_location}</span>
                </div>
                {user_traveling && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">Status:</span>
                    <span className="text-blue-600 font-medium">Traveling</span>
                  </div>
                )}
              </div>
            </div>

            {/* What can you do */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
              <h3 className="font-semibold text-blue-900 mb-3 flex items-center">
                <ExclamationTriangleIcon className="h-5 w-5 text-blue-600 mr-2" />
                What can you do?
              </h3>
              <ul className="space-y-2 text-sm text-blue-800">
                {actions.map((action, index) => (
                  <li key={index} className="flex items-start">
                    <span className="inline-block w-2 h-2 bg-blue-400 rounded-full mt-2 mr-3 flex-shrink-0"></span>
                    {action}
                  </li>
                ))}
                {actions.length === 0 && (
                  <>
                    <li className="flex items-start">
                      <span className="inline-block w-2 h-2 bg-blue-400 rounded-full mt-2 mr-3 flex-shrink-0"></span>
                      Check if your location information is correct in your profile settings
                    </li>
                    <li className="flex items-start">
                      <span className="inline-block w-2 h-2 bg-blue-400 rounded-full mt-2 mr-3 flex-shrink-0"></span>
                      Contact the community administrators if you believe this is an error
                    </li>
                    <li className="flex items-start">
                      <span className="inline-block w-2 h-2 bg-blue-400 rounded-full mt-2 mr-3 flex-shrink-0"></span>
                      Explore other communities that are available in your region
                    </li>
                  </>
                )}
              </ul>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button
                onClick={onBrowseCommunities}
                className="inline-flex items-center justify-center px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors"
              >
                <GlobeAmericasIcon className="h-5 w-5 mr-2" />
                Browse Communities
              </button>

              {/* <button
                onClick={onUpdateLocation}
                className="inline-flex items-center justify-center px-6 py-3 bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium rounded-lg transition-colors border border-gray-300"
              >
                <MapPinIcon className="h-5 w-5 mr-2" />
                Update Location
              </button> */}
            </div>
          </div>

          {/* Footer */}
          <div className="bg-gray-50 px-8 py-4 rounded-b-lg">
            <p className="text-sm text-gray-500 text-center">
              Geographic restrictions help communities maintain local focus and comply with regional regulations.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GeoRestricted;
