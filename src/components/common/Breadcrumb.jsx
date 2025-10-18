import React from 'react';
import { ChevronRightIcon, HomeIcon } from '@heroicons/react/24/outline';
import { useNavigate } from 'react-router-dom';

/**
 * Breadcrumb - Hierarchical navigation component
 *
 * Displays: Accueil > Division Name > Rubrique Name > Thread Title
 * Features:
 * - Handles null divisions gracefully
 * - Clickable breadcrumb items for navigation
 * - Context-aware display based on current location
 * - Responsive design with proper overflow handling
 */
const Breadcrumb = ({
  division = null,
  community = null,
  thread = null,
  post = null,
  onNavigate = null,  // Optional custom navigation handler
}) => {
  const navigate = useNavigate();
  const location = window.location;

  // Extract URL path components (e.g., /municipality/sherbrooke/thread/slug)
  const pathParts = location.pathname.split('/').filter(Boolean);
  const currentUrlPath = pathParts[0]; // municipality, commune, city, etc.
  const municipalitySlug = pathParts[1]; // sherbrooke, ganvie, etc.

  // Build breadcrumb items array
  const items = [];

  // Always start with Home
  items.push({
    label: 'Accueil',
    icon: HomeIcon,
    path: currentUrlPath && municipalitySlug
      ? `/${currentUrlPath}/${municipalitySlug}/accueil`
      : '/',
    type: 'home'
  });

  // Add Division Name (if available)
  if (division) {
    items.push({
      label: division.name || division.code,
      path: currentUrlPath && municipalitySlug
        ? `/${currentUrlPath}/${municipalitySlug}/accueil`
        : `/division/${division.id}`,
      type: 'division',
      data: division
    });
  }

  // Add Rubrique Name (if thread has section info)
  if (thread && thread.section_name) {
    items.push({
      label: thread.section_name,
      path: currentUrlPath && municipalitySlug && thread.section_slug
        ? `/${currentUrlPath}/${municipalitySlug}/${thread.section_slug}`
        : null,
      type: 'rubrique',
      data: { name: thread.section_name, slug: thread.section_slug }
    });
  }

  // Add Thread Title
  if (thread) {
    items.push({
      label: thread.title,
      path: null, // Current page, no link
      type: 'thread',
      data: thread
    });
  }

  // Add Post (if viewing a specific post within thread)
  if (post) {
    items.push({
      label: post.title || `Post #${post.id}`,
      path: null, // Current page
      type: 'post',
      data: post
    });
  }

  // Handle navigation click
  const handleClick = (item, index) => {
    // Don't navigate if it's the last item (current location) or no path
    if (index === items.length - 1 || !item.path) return;

    if (onNavigate) {
      // Use custom navigation handler if provided
      onNavigate(item);
    } else {
      // Default navigation using React Router
      navigate(item.path);
    }
  };

  // Don't render if only Home (no context)
  if (items.length <= 1) {
    return null;
  }

  return (
    <nav className="flex items-center space-x-2 text-sm text-gray-600 py-2 px-1 overflow-x-auto">
      {items.map((item, index) => {
        const isLast = index === items.length - 1;
        const Icon = item.icon;

        return (
          <React.Fragment key={`${item.type}-${index}`}>
            {/* Breadcrumb Item */}
            <div className="flex items-center flex-shrink-0">
              <button
                onClick={() => handleClick(item, index)}
                disabled={isLast || !item.path}
                className={`flex items-center gap-1.5 px-2 py-1 rounded transition-colors ${
                  isLast || !item.path
                    ? 'text-gray-900 font-medium cursor-default'
                    : 'text-gray-600 hover:text-blue-600 hover:bg-blue-50 cursor-pointer'
                }`}
                title={item.label}
              >
                {Icon && <Icon className="w-4 h-4 flex-shrink-0" />}
                <span className="truncate max-w-[200px]">{item.label}</span>
              </button>
            </div>

            {/* Separator (except for last item) */}
            {!isLast && (
              <ChevronRightIcon className="w-4 h-4 text-gray-400 flex-shrink-0" />
            )}
          </React.Fragment>
        );
      })}
    </nav>
  );
};

export default Breadcrumb;
