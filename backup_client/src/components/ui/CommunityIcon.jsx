import React from 'react';

// Lightweight wrapper to render Heroicon components with a consistent style
// Map semantic color names to appropriate Tailwind color classes (vibrant, like VisibilitySelector).
const COLOR_MAP = {
  gray: 'text-gray-500',
  blue: 'text-blue-600',
  purple: 'text-purple-600',
  green: 'text-green-600',
  yellow: 'text-yellow-500',
  red: 'text-red-500',
  indigo: 'text-indigo-600',
  orange: 'text-orange-500',
  teal: 'text-teal-600',
  pink: 'text-pink-500'
};

const SIZE_MAP = {
  sm: 'h-4 w-4',
  md: 'h-5 w-5',
  lg: 'h-7 w-7'
};

export default function CommunityIcon({ Icon, color = 'gray', size = 'md', className = '' }) {
  if (!Icon) return null;
  // allow passing a raw tailwind class like 'text-indigo-500'
  const colorClass = typeof color === 'string' && color.startsWith('text-') ? color : (COLOR_MAP[color] || COLOR_MAP.gray);
  const sizeClass = SIZE_MAP[size] || SIZE_MAP.md;
  return React.createElement(Icon, { className: `${sizeClass} ${colorClass} ${className}` });
}
