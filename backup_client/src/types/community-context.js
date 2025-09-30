// Simple helpers for community context UI (Clean JS)

export const getCommunityContextIcon = (contextType) => (contextType === 'community' ? '🏘️' : '🌐');

export const getCommunityContextColor = (contextType) =>
  contextType === 'community' ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-800';

// Example usage (JSX):
// <span className={`inline-flex items-center px-2 py-1 rounded ${getCommunityContextColor(post.context_type)}`}>
//   <span className="mr-1">{getCommunityContextIcon(post.context_type)}</span>
//   {post.context_name}
// </span>
