// Social Components - Reusable components for social media functionality
export { default as PostCard } from './PostCard';
export { default as RepostCard } from './RepostCard';
export { default as PostComposer } from './PostComposer';
export { default as PostActionBar } from './PostActionBar';
export { default as PostContentRenderer } from './PostContentRenderer';
export { default as PostCommentThread } from './PostCommentThread';
export { default as AttachmentDisplay } from './AttachmentDisplay';
export { default as PollDisplay } from './PollDisplay';

// Usage Examples:
//
// For regular posts:
// import { PostCard } from '../components/social';
// <PostCard post={postData} onUpdate={handleUpdate} onDelete={handleDelete} />
//
// For reposts (feed items with type="repost"):
// import { RepostCard } from '../components/social';
// <RepostCard repostData={repostFeedItem} onPostUpdate={handleUpdate} onPostDelete={handleDelete} />
//
// For rendering feed with mixed content:
// {feedItems.map(item => {
//   if (item.type === 'repost') {
//     return <RepostCard key={item.repost_id} repostData={item} />;
//   } else {
//     return <PostCard key={item.id} post={item} />;
//   }
// })}
