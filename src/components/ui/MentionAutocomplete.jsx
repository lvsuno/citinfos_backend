import React, { useState, useEffect, useRef } from 'react';
import { socialAPI } from '../../services/social-api';

const MentionAutocomplete = ({
  text,
  cursorPosition,
  onMentionSelect,
  communityId = null,
  postId = null, // For comment context to prioritize post author
  className = ''
}) => {
  const [suggestions, setSuggestions] = useState([]);
  const [isVisible, setIsVisible] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [mentionQuery, setMentionQuery] = useState('');
  const [mentionStartPos, setMentionStartPos] = useState(null);
  const suggestionListRef = useRef(null);

  // Check if cursor is after an @ symbol and extract mention query
  useEffect(() => {
    const checkForMention = () => {
      if (cursorPosition === null || cursorPosition === undefined) {        setIsVisible(false);
        return;
      }

      const textBeforeCursor = text.slice(0, cursorPosition);
      const lastAtIndex = textBeforeCursor.lastIndexOf('@');

      if (lastAtIndex === -1) {        setIsVisible(false);
        return;
      }

      // Check if there's a space between @ and cursor (invalid mention)
      const textAfterAt = textBeforeCursor.slice(lastAtIndex + 1);
      if (textAfterAt.includes(' ') || textAfterAt.includes('\n')) {        setIsVisible(false);
        return;
      }

      // Check if @ is at start or preceded by whitespace
      const charBeforeAt = lastAtIndex > 0 ? textBeforeCursor[lastAtIndex - 1] : ' ';
      if (charBeforeAt !== ' ' && charBeforeAt !== '\n' && lastAtIndex !== 0) {        setIsVisible(false);
        return;
      }

      // Valid mention context      setMentionQuery(textAfterAt);
      setMentionStartPos(lastAtIndex);
      setIsVisible(true);
      setSelectedIndex(0);
    };

    checkForMention();
  }, [text, cursorPosition]);

  // Search for users when mention query changes
  useEffect(() => {
    const searchUsers = async () => {
      if (!isVisible || mentionQuery.length < 1) {        setSuggestions([]);
        return;
      }      try {
        const results = await socialAPI.searchMentionableUsers(
          mentionQuery,
          communityId,
          postId
        );        setSuggestions(results);
      } catch (error) {        setSuggestions([]);
      }
    };

    const debounceTimer = setTimeout(searchUsers, 300); // Debounce search
    return () => clearTimeout(debounceTimer);
  }, [mentionQuery, isVisible, communityId, postId]);

  // Handle keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (!isVisible || suggestions.length === 0) return;

      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          setSelectedIndex(prev => Math.min(prev + 1, suggestions.length - 1));
          break;
        case 'ArrowUp':
          e.preventDefault();
          setSelectedIndex(prev => Math.max(prev - 1, 0));
          break;
        case 'Enter':
        case 'Tab':
          e.preventDefault();
          if (suggestions[selectedIndex]) {
            handleMentionSelect(suggestions[selectedIndex]);
          }
          break;
        case 'Escape':
          setIsVisible(false);
          break;
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isVisible, suggestions, selectedIndex]);

  const handleMentionSelect = (user) => {
    if (mentionStartPos !== null && onMentionSelect) {
      onMentionSelect({
        user,
        startPos: mentionStartPos,
        endPos: mentionStartPos + mentionQuery.length + 1, // +1 for @ symbol
        replacement: `@${user.username} `
      });
    }
    setIsVisible(false);
  };

  if (!isVisible || suggestions.length === 0) {
    return null;
  }

  // Group suggestions by category for better display
  const groupedSuggestions = suggestions.reduce((groups, user, index) => {
    const category = user.category || 'Other';
    if (!groups[category]) {
      groups[category] = [];
    }
    groups[category].push({ ...user, originalIndex: index });
    return groups;
  }, {});

  // Define category order for consistent display
  const categoryOrder = [
    'People you follow',
    'Post author',
    'Community members',
    'Public profiles'
  ];

  let currentIndex = 0;

  return (
    <div className={`absolute z-50 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-lg shadow-lg max-h-64 overflow-y-auto min-w-72 ${className}`}>
      {categoryOrder.map(categoryName => {
        const categoryUsers = groupedSuggestions[categoryName];
        if (!categoryUsers || categoryUsers.length === 0) return null;

        return (
          <div key={categoryName}>
            {/* Category Header */}
            <div className="px-3 py-1 text-xs font-medium text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-700/50 border-b border-gray-100 dark:border-gray-600">
              {categoryName}
            </div>

            {/* Category Users */}
            <ul className="py-1">
              {categoryUsers.map((user) => {
                const itemSelected = currentIndex === selectedIndex;
                const itemIndex = currentIndex++;

                return (
                  <li
                    key={user.id}
                    className={`px-3 py-2 cursor-pointer flex items-center space-x-3 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors ${
                      itemSelected
                        ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400'
                        : 'text-gray-900 dark:text-gray-100'
                    }`}
                    onClick={() => handleMentionSelect(user)}
                    onMouseEnter={() => setSelectedIndex(itemIndex)}
                  >
                    <div className="w-8 h-8 rounded-full bg-gray-300 dark:bg-gray-600 flex items-center justify-center text-sm font-medium flex-shrink-0">
                      {user.avatar_url ? (
                        <img
                          src={user.avatar_url}
                          alt={user.username}
                          className="w-8 h-8 rounded-full object-cover"
                        />
                      ) : (
                        <span className="text-gray-600 dark:text-gray-300">
                          {user.display_name.charAt(0).toUpperCase()}
                        </span>
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="font-medium truncate">@{user.username}</div>
                      {user.display_name !== user.username && (
                        <div className="text-sm text-gray-500 dark:text-gray-400 truncate">
                          {user.display_name}
                        </div>
                      )}
                    </div>
                    {/* Priority badge */}
                    {user.priority === 'post_author' && (
                      <div className="text-xs bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 px-2 py-1 rounded">
                        Author
                      </div>
                    )}
                    {user.priority === 'follower' && (
                      <div className="text-xs bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400 px-2 py-1 rounded">
                        Following
                      </div>
                    )}
                  </li>
                );
              })}
            </ul>
          </div>
        );
      })}

      {/* Help text */}
      <div className="px-3 py-2 text-xs text-gray-500 dark:text-gray-400 border-t border-gray-100 dark:border-gray-600 bg-gray-50 dark:bg-gray-700/50">
        Use ↑↓ to navigate, Enter to select, Esc to close
      </div>
    </div>
  );
};

export default MentionAutocomplete;
