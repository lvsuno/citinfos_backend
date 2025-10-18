import React from 'react';
import { useNavigate } from 'react-router-dom';
import DOMPurify from 'dompurify';

// Renders post text with HTML rendering, mention (@user) and hashtag (#tag) highlighting
export const PostContentRenderer = ({ text, mentions = {} }) => {
  const navigate = useNavigate();

  const handleMentionClick = (username) => {
    // Remove the @ symbol and get the user ID from mentions mapping
    const cleanUsername = username.replace('@', '');
    const userId = mentions[cleanUsername];

    if (userId) {
      // Use the same pattern as ClickableAuthorName - navigate to /users/:userId
      navigate(`/users/${userId}`);
    }
  };

  if (!text) return null;

  // Check if text contains HTML tags
  const hasHTML = /<[a-z][\s\S]*>/i.test(text);

  // If text contains HTML, sanitize and render it
  if (hasHTML) {
    // Sanitize HTML to prevent XSS attacks
    const sanitizedHTML = DOMPurify.sanitize(text, {
      ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'u', 'a', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'code', 'pre'],
      ALLOWED_ATTR: ['href', 'target', 'rel']
    });

    return (
      <div
        className="prose prose-sm max-w-none break-words leading-relaxed"
        dangerouslySetInnerHTML={{ __html: sanitizedHTML }}
      />
    );
  }

  // Otherwise, use the original mention/hashtag highlighting
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
