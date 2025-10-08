import React, { useState } from 'react';
import {
  GlobeAltIcon,
  UserGroupIcon,
  UserPlusIcon
} from '@heroicons/react/24/outline';
import CommunityIcon from './CommunityIcon';

/**
 * VisibilitySelector - Reusable visibility selector with custom field support
 *
 * Features:
 * - Icon-based visibility selector (Public, Followers, Custom)
 * - Custom visibility input field for usernames/communities
 * - Matches PostComposer styling and behavior exactly
 * - Validation for custom field when required
 *
 * @param {Object} props
 * @param {string} props.visibility - Current visibility setting ('public', 'followers', 'custom')
 * @param {Function} props.onVisibilityChange - Callback when visibility changes
 * @param {string} props.customFollowers - Custom followers list (comma-separated)
 * @param {Function} props.onCustomFollowersChange - Callback when custom followers change
 * @param {boolean} props.showValidation - Whether to show validation styling for invalid state
 * @param {string} props.className - Additional CSS classes
 */
const VisibilitySelector = ({
  visibility = 'public',
  onVisibilityChange,
  customFollowers = '',
  onCustomFollowersChange,
  showValidation = false,
  className = ''
}) => {
  const [showVisibilityMenu, setShowVisibilityMenu] = useState(false);

  // Visibility options matching PostComposer exactly
  const visibilityOptions = [
    { key: 'public', label: 'Public', icon: GlobeAltIcon, desc: 'Visible to everyone' },
    { key: 'followers', label: 'Followers', icon: UserGroupIcon, desc: 'Only your followers' },
    { key: 'custom', label: 'Custom', icon: UserPlusIcon, desc: 'Choose specific followers' },
  ];

  const currentVisibility = visibilityOptions.find(v => v.key === visibility) || visibilityOptions[0];

  const handleVisibilitySelect = (selectedKey) => {
    onVisibilityChange(selectedKey);
    setShowVisibilityMenu(false);
  };

  return (
    <>
      <div className={`flex items-center gap-3 ${className}`}>
        {/* Visibility Selector (icon + tooltip) */}
        <div className="relative">
            <button
            type="button"
            onClick={() => setShowVisibilityMenu(!showVisibilityMenu)}
            className={`composer-btn h-9 w-9 ${visibility==='public' ? 'ring-1 ring-green-300' : visibility==='followers' ? 'ring-1 ring-blue-300' : visibility==='custom' ? 'ring-1 ring-purple-300' : ''}`}
            aria-haspopup="listbox"
            aria-expanded={showVisibilityMenu}
            title={`${currentVisibility.label}: ${currentVisibility.desc}`}
          >
            <CommunityIcon Icon={currentVisibility.icon} size="md" className={`${visibility==='public' ? 'text-green-600' : visibility==='followers' ? 'text-blue-600' : 'text-purple-600'}`} />
          </button>

          {showVisibilityMenu && (
            <div className="absolute z-40 mt-2 left-0 w-48 bg-white border border-gray-200 rounded-lg shadow-lg py-1 text-[12px]" role="listbox">
              {visibilityOptions.map(opt => (
                <button
                  key={opt.key}
                  type="button"
                  role="option"
                  aria-selected={visibility===opt.key}
                  onClick={() => handleVisibilitySelect(opt.key)}
                  className={`w-full flex items-start gap-2 px-3 py-2 hover:bg-gray-50 text-left ${visibility===opt.key ? 'bg-gray-100 font-semibold' : ''}`}
                >
                  <CommunityIcon Icon={opt.icon} size="sm" className={`mt-0.5 ${opt.key==='public' ? 'text-green-600' : opt.key==='followers' ? 'text-blue-600' : 'text-purple-600'}`} />
                  <span>
                    <span className="block capitalize">{opt.label}</span>
                    <span className="block text-[10px] text-gray-500 leading-tight">{opt.desc}</span>
                  </span>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Custom visibility input field */}
        {visibility === 'custom' && (
          <div className="flex flex-col">
            <input
              type="text"
              value={customFollowers}
              onChange={e => onCustomFollowersChange(e.target.value)}
              placeholder="user1, user2"
              required
              className={`text-[11px] rounded-md px-2 py-1 ${
                showValidation && visibility === 'custom' && !customFollowers.trim()
                  ? 'border-red-300 focus:ring-red-500 focus:border-red-500'
                  : 'border-gray-300 focus:ring-indigo-500 focus:border-indigo-500'
              }`}
              style={{minWidth:'180px'}}
              title="Comma separated usernames"
              aria-describedby={showValidation && visibility === 'custom' && !customFollowers.trim() ? "custom-visibility-error" : undefined}
            />
            {showValidation && visibility === 'custom' && !customFollowers.trim() && (
              <span id="custom-visibility-error" className="text-red-500 text-[10px] mt-1">
                Please specify users or communities
              </span>
            )}
          </div>
        )}
      </div>
      <style>{`
        .composer-btn{display:inline-flex;align-items:center;justify-content:center;height:34px;width:34px;border-radius:8px;background:linear-gradient(135deg,#f8fafc,#f1f5f9);border:1px solid #e2e8f0;box-shadow:0 1px 2px rgba(0,0,0,.04);transition:.2s;}
        .composer-btn:hover{background:linear-gradient(135deg,#eef2ff,#e0e7ff);border-color:#c7d2fe;}
        .composer-btn:active{transform:translateY(1px);}
      `}</style>
    </>
  );
};

/**
 * Validates if custom visibility settings are valid
 * @param {string} visibility - The visibility setting
 * @param {string} customFollowers - The custom followers string
 * @returns {boolean} - True if valid, false if invalid
 */
export const validateCustomVisibility = (visibility, customFollowers) => {
  if (visibility === 'custom') {
    return customFollowers.trim().length > 0;
  }
  return true;
};

export default VisibilitySelector;
