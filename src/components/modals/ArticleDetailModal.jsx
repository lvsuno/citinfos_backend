import React, { useEffect } from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { formatTimeAgo, formatFullDateTime } from '../../utils/timeUtils';
import ClickableAuthorName from '../ui/ClickableAuthorName';
import TinyBadgeList from '../TinyBadgeList';

const ArticleDetailModal = ({ isOpen, onClose, post }) => {
  // Close on Escape key
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape') onClose();
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  if (!isOpen || !post) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
      />

      {/* Modal - positioned relative to content area, accounting for sidebar */}
      <div className="flex min-h-full items-start justify-center p-4 pt-8 lg:ml-[300px]">
        <div
          className="relative w-full max-w-4xl bg-white rounded-2xl shadow-2xl my-8"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="sticky top-0 z-10 flex items-center justify-between px-6 py-4 border-b border-gray-200 bg-white rounded-t-2xl">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-full bg-gradient-to-br from-indigo-500 to-blue-500 flex items-center justify-center text-white text-sm font-semibold">
                {(post.author?.username || 'U').charAt(0).toUpperCase()}
              </div>
              <div>
                <ClickableAuthorName
                  author={post.author}
                  authorUsername={post.author_username}
                />
                <div className="flex items-center gap-2 text-xs text-gray-500">
                  <span
                    className="cursor-help"
                    title={formatFullDateTime(post.created_at)}
                  >
                    {formatTimeAgo(post.created_at)}
                  </span>
                  {post.is_edited && (
                    <>
                      <span>•</span>
                      <span className="italic">Modifié</span>
                    </>
                  )}
                </div>
              </div>
            </div>

            {/* Close Button */}
            <button
              type="button"
              onClick={onClose}
              className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <XMarkIcon className="w-6 h-6" />
            </button>
          </div>

          {/* Article Content */}
          <article className="px-6 py-8 overflow-y-auto" style={{ maxHeight: 'calc(100vh - 200px)' }}>
            {/* Featured Image */}
            {post.featured_image && (
              <img
                src={post.featured_image}
                alt={post.content || 'Article'}
                className="w-full h-96 object-cover rounded-lg mb-8"
              />
            )}

            {/* Title */}
            <h1 className="text-4xl font-bold text-gray-900 mb-4">
              {post.content || 'Sans titre'}
            </h1>

            {/* Author Badges */}
            {post.author && (
              <div className="flex items-center gap-2 mb-6">
                <TinyBadgeList userId={post.author.id || post.author} maxVisible={5} />
              </div>
            )}

            {/* Excerpt */}
            {post.excerpt && (
              <p className="text-xl text-gray-600 italic mb-6 pb-6 border-b border-gray-200">
                {post.excerpt}
              </p>
            )}

            {/* Article Body */}
            <div
              className="prose prose-lg max-w-none article-content"
              dangerouslySetInnerHTML={{ __html: post.article_content || post.content }}
            />

            {/* Article Footer */}
            <div className="mt-12 pt-6 border-t border-gray-200">
              <div className="flex items-center justify-between text-sm text-gray-500">
                <div className="flex items-center gap-4">
                  <span>{post.likes_count || 0} J'aime</span>
                  <span>{post.comments_count || 0} Commentaires</span>
                  <span>{post.shares_count || 0} Partages</span>
                  <span>{post.views_count || 0} Vues</span>
                </div>

                {post.visibility && (
                  <span className="text-xs">
                    {post.visibility === 'public' && '🌍 Public'}
                    {post.visibility === 'followers' && '👥 Abonnés'}
                    {post.visibility === 'private' && '🔒 Privé'}
                  </span>
                )}
              </div>
            </div>
          </article>
        </div>
      </div>

      {/* Global styles for article content */}
      <style jsx>{`
        .article-content {
          line-height: 1.8;
        }

        .article-content h1 {
          font-size: 2rem;
          font-weight: 700;
          margin-top: 2rem;
          margin-bottom: 1rem;
          color: #111827;
        }

        .article-content h2 {
          font-size: 1.5rem;
          font-weight: 600;
          margin-top: 1.5rem;
          margin-bottom: 0.75rem;
          color: #1f2937;
        }

        .article-content h3 {
          font-size: 1.25rem;
          font-weight: 600;
          margin-top: 1.25rem;
          margin-bottom: 0.5rem;
          color: #374151;
        }

        .article-content p {
          margin-bottom: 1rem;
          color: #374151;
        }

        .article-content img {
          max-width: 100%;
          height: auto;
          border-radius: 0.5rem;
          margin: 1.5rem 0;
        }

        .article-content blockquote {
          border-left: 4px solid #3b82f6;
          padding-left: 1rem;
          margin: 1.5rem 0;
          font-style: italic;
          color: #6b7280;
        }

        .article-content ul, .article-content ol {
          margin: 1rem 0;
          padding-left: 1.5rem;
        }

        .article-content li {
          margin: 0.5rem 0;
        }

        .article-content code {
          background-color: #f3f4f6;
          padding: 0.125rem 0.25rem;
          border-radius: 0.25rem;
          font-size: 0.875em;
          font-family: 'Courier New', monospace;
        }

        .article-content pre {
          background-color: #1f2937;
          color: #f3f4f6;
          padding: 1rem;
          border-radius: 0.5rem;
          overflow-x: auto;
          margin: 1.5rem 0;
        }

        .article-content pre code {
          background-color: transparent;
          padding: 0;
          color: inherit;
        }

        .article-content a {
          color: #3b82f6;
          text-decoration: underline;
        }

        .article-content a:hover {
          color: #2563eb;
        }
      `}</style>
    </div>
  );
};

export default ArticleDetailModal;
