import React, { useState, useEffect, useRef } from 'react';
import { XMarkIcon, PlusIcon } from '@heroicons/react/24/outline';

/**
 * ReactionPicker Component
 *
 * Two-level reaction picker:
 * 1. Quick reactions bar: Shows 5 most common reactions + "more" button
 * 2. Full grid: Shows all 22 reactions organized by sentiment
 *
 * 22 emoji reactions organized by sentiment:
 * - POSITIVE (14): like, love, care, haha, wow, yay, clap, fire, star, party, heart_eyes, pray, strong, celebrate
 * - NEGATIVE (4): sad, angry, worried, disappointed
 * - NEUTRAL (4): thinking, curious, shock, confused
 *
 * Props:
 *   onReact(reactionType): Callback when user selects a reaction
 *   onClose(): Callback to close the picker
 *   currentReaction?: Currently active reaction type
 *   position?: { top, left } for absolute positioning
 *   mode?: 'quick' | 'full' - Display mode (default: 'quick')
 *   onShowMore?(): Callback when "more" button clicked
 */

// Reaction definitions with emoji and display names
const REACTIONS = {
  POSITIVE: [
    { type: 'like', emoji: '👍', label: 'Like' },
    { type: 'love', emoji: '❤️', label: 'Love' },
    { type: 'care', emoji: '🤗', label: 'Care' },
    { type: 'haha', emoji: '😂', label: 'Haha' },
    { type: 'wow', emoji: '😮', label: 'Wow' },
    { type: 'yay', emoji: '🎉', label: 'Yay' },
    { type: 'clap', emoji: '👏', label: 'Clap' },
    { type: 'fire', emoji: '🔥', label: 'Fire' },
    { type: 'star', emoji: '⭐', label: 'Star' },
    { type: 'party', emoji: '🥳', label: 'Party' },
    { type: 'heart_eyes', emoji: '😍', label: 'Heart Eyes' },
    { type: 'pray', emoji: '🙏', label: 'Pray' },
    { type: 'strong', emoji: '💪', label: 'Strong' },
    { type: 'celebrate', emoji: '🎊', label: 'Celebrate' },
  ],
  NEGATIVE: [
    { type: 'sad', emoji: '😢', label: 'Sad' },
    { type: 'angry', emoji: '😠', label: 'Angry' },
    { type: 'worried', emoji: '😟', label: 'Worried' },
    { type: 'disappointed', emoji: '😞', label: 'Disappointed' },
  ],
  NEUTRAL: [
    { type: 'thinking', emoji: '🤔', label: 'Thinking' },
    { type: 'curious', emoji: '🧐', label: 'Curious' },
    { type: 'shock', emoji: '😲', label: 'Shock' },
    { type: 'confused', emoji: '😕', label: 'Confused' },
  ]
};

// Get all reactions as a flat array
export const getAllReactions = () => [
  ...REACTIONS.POSITIVE,
  ...REACTIONS.NEGATIVE,
  ...REACTIONS.NEUTRAL
];

// Get emoji for a reaction type
export const getReactionEmoji = (reactionType) => {
  const allReactions = getAllReactions();
  const reaction = allReactions.find(r => r.type === reactionType);
  return reaction ? reaction.emoji : '👍';
};

// Get 5 most popular quick reactions
export const getQuickReactions = () => [
  { type: 'like', emoji: '👍', label: 'Like' },
  { type: 'love', emoji: '❤️', label: 'Love' },
  { type: 'haha', emoji: '😂', label: 'Haha' },
  { type: 'wow', emoji: '😮', label: 'Wow' },
  { type: 'sad', emoji: '😢', label: 'Sad' },
];

const ReactionPicker = ({ onReact, onClose, currentReaction, position, mode = 'quick', onShowMore }) => {
  const [selectedTab, setSelectedTab] = useState('POSITIVE');
  const [displayMode, setDisplayMode] = useState(mode);
  const pickerRef = useRef(null);

  // Close picker when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (pickerRef.current && !pickerRef.current.contains(event.target)) {
        onClose();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [onClose]);

  // Update display mode when prop changes
  useEffect(() => {
    setDisplayMode(mode);
  }, [mode]);

  const handleReactionClick = (reactionType) => {
    // If clicking the same reaction, remove it (unreact)
    if (currentReaction === reactionType) {
      onReact(null);
    } else {
      onReact(reactionType);
    }
    onClose();
  };

  const handleShowMore = () => {
    setDisplayMode('full');
    if (onShowMore) onShowMore();
  };

  const positionStyle = position
    ? { position: 'fixed', top: `${position.top}px`, left: `${position.left}px`, zIndex: 300 }
    : {};

  // Quick reactions bar (horizontal row of 5 + more button)
  if (displayMode === 'quick') {
    const quickReactions = getQuickReactions();

    return (
      <div
        ref={pickerRef}
        className="bg-white rounded-full shadow-xl border border-gray-200 px-2 py-2 flex items-center gap-1 animate-in fade-in zoom-in-95 duration-200"
        style={positionStyle}
        onClick={(e) => e.stopPropagation()}
      >
        {quickReactions.map((reaction) => {
          const isSelected = currentReaction === reaction.type;
          return (
            <button
              key={reaction.type}
              onClick={() => handleReactionClick(reaction.type)}
              className={`
                flex items-center justify-center w-10 h-10 rounded-full transition-all
                hover:bg-gray-100 hover:scale-125 active:scale-95
                ${isSelected ? 'bg-indigo-100 ring-2 ring-indigo-500' : ''}
              `}
              title={reaction.label}
            >
              <span className="text-2xl">{reaction.emoji}</span>
            </button>
          );
        })}

        {/* More button */}
        <button
          onClick={handleShowMore}
          className="flex items-center justify-center w-10 h-10 rounded-full bg-gray-100 hover:bg-gray-200 transition-all hover:scale-110 active:scale-95"
          title="More reactions"
        >
          <PlusIcon className="h-5 w-5 text-gray-600" />
        </button>
      </div>
    );
  }

  // Full grid view (all 22 reactions)
  const tabStyle = (tab) => `
    px-3 py-1.5 rounded-t-lg text-xs font-medium transition-colors
    ${selectedTab === tab
      ? 'bg-white text-indigo-600 border-b-2 border-indigo-600'
      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
    }
  `;

  return (
    <div
      ref={pickerRef}
      className="bg-white rounded-lg shadow-xl border border-gray-200 w-80 animate-in fade-in slide-in-from-bottom-2 duration-200"
      style={positionStyle}
      onClick={(e) => e.stopPropagation()}
    >
      {/* Header with tabs */}
      <div className="flex items-center justify-between p-2 border-b border-gray-200">
        <div className="flex gap-1">
          <button
            onClick={() => setSelectedTab('POSITIVE')}
            className={tabStyle('POSITIVE')}
          >
            😊 Positive
          </button>
          <button
            onClick={() => setSelectedTab('NEGATIVE')}
            className={tabStyle('NEGATIVE')}
          >
            😔 Negative
          </button>
          <button
            onClick={() => setSelectedTab('NEUTRAL')}
            className={tabStyle('NEUTRAL')}
          >
            🤷 Neutral
          </button>
        </div>
        <button
          onClick={onClose}
          className="p-1 hover:bg-gray-100 rounded-full transition-colors"
          aria-label="Close"
        >
          <XMarkIcon className="h-4 w-4 text-gray-500" />
        </button>
      </div>

      {/* Reaction grid */}
      <div className="p-3">
        <div className="grid grid-cols-5 gap-2">
          {REACTIONS[selectedTab].map((reaction) => {
            const isSelected = currentReaction === reaction.type;
            return (
              <button
                key={reaction.type}
                onClick={() => handleReactionClick(reaction.type)}
                className={`
                  flex flex-col items-center gap-1 p-2 rounded-lg transition-all
                  hover:bg-indigo-50 hover:scale-110 active:scale-95
                  ${isSelected ? 'bg-indigo-100 ring-2 ring-indigo-500' : 'bg-gray-50'}
                `}
                title={reaction.label}
              >
                <span className="text-2xl">{reaction.emoji}</span>
                <span className={`text-[9px] font-medium truncate w-full text-center ${
                  isSelected ? 'text-indigo-600' : 'text-gray-600'
                }`}>
                  {reaction.label}
                </span>
              </button>
            );
          })}
        </div>

        {/* Remove reaction button if user has already reacted */}
        {currentReaction && (
          <div className="mt-3 pt-3 border-t border-gray-200">
            <button
              onClick={() => {
                onReact(null);
                onClose();
              }}
              className="w-full py-2 text-xs font-medium text-red-600 hover:bg-red-50 rounded-lg transition-colors"
            >
              Remove Reaction
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default ReactionPicker;
