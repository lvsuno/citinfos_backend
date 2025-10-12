import React from 'react';
import { useNavigate } from 'react-router-dom';

// Renders post text with mention (@user) and hashtag (#tag) highlighting
export const PostContentRenderer = ({ text, mentions = {} }) => {
  const navigate = useNavigate();

  const handleMentionClick = (username) => {
    // Remove the @ symbol and get the user ID from mentions mapping
    const cleanUsername = username.replace('@', '');
    const userId = mentions[cleanUsername];

    if (userId) {
      // Use the same pattern as ClickableAuthorName - navigate to /users/:userId
      navigate(`/users/${userId}`);
    } else {
      console.warn(`No user ID found for mention: ${cleanUsername}`);
    }
  };

  if (!text) return null;

  return (
    <span className="break-words leading-relaxed">
      {text.split(/(\s+)/).map((part, i) => {
        if (/^@[A-Za-z0-9_]+$/.test(part)) {
          return (
            <span
              key={i}
              className="text-blue-600 font-medium hover:underline cursor-pointer"
              onClick={() => handleMentionClick(part)}
            >
              {part}
            </span>
          );
        }
        if (/^#[A-Za-z0-9_]+$/.test(part)) {
          return <span key={i} className="text-green-600 font-medium hover:underline cursor-pointer">{part}</span>;
        }
        return <span key={i}>{part}</span>;
      })}
    </span>
  );
};
export default PostContentRenderer;
