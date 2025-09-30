import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useGlobalSearch } from '../hooks/useGlobalSearch';
import { useJWTAuth } from '../services/jwtAuthService';
import {
  MagnifyingGlassIcon,
  UserIcon,
  DocumentTextIcon,
  WrenchScrewdriverIcon,
  UserGroupIcon,
  ChatBubbleLeftRightIcon,
  ChartBarIcon,
  CpuChipIcon
} from '@heroicons/react/24/outline';

function useQueryParams() {
  const { search } = useLocation();
  return React.useMemo(() => Object.fromEntries(new URLSearchParams(search).entries()), [search]);
}

const Section = ({ title, items, render, empty, icon: Icon, count }) => (
  <div className="bg-white rounded-lg shadow border border-gray-100 p-4">
    <div className="flex items-center justify-between mb-3">
      <div className="flex items-center gap-2">
        {Icon && <CommunityIcon Icon={Icon} size="sm" color="gray" />}
        <h3 className="text-sm font-semibold text-gray-900">{title}</h3>
      </div>
      <span className="text-[10px] text-gray-400 bg-gray-100 px-2 py-1 rounded-full">
        {count !== undefined ? count : items.length}
      </span>
    </div>
    {items.length > 0 ? (
      <ul className="divide-y divide-gray-100">
        {items.map(render)}
      </ul>
    ) : (
      <p className="text-[11px] text-gray-400 text-center py-4">{empty}</p>
    )}
  </div>
);

const SearchResults = () => {
  const params = useQueryParams();
  const navigate = useNavigate();
  const { isAuthenticated } = useJWTAuth();
  const query = params.q || '';
  const type = params.type || 'all';
  const { data, isLoading, error } = useGlobalSearch(query, type);

  const onSubmit = (e) => {
    e.preventDefault();
    const form = e.target;
    const q = form.elements.q.value.trim();
    const t = form.elements.type.value;
    navigate(`/search?q=${encodeURIComponent(q)}&type=${encodeURIComponent(t)}`);
  };

  return (
    <div className="space-y-5">
      {/* Search Form */}
      <form onSubmit={onSubmit} className="flex flex-wrap items-center gap-2 bg-white p-3 border border-gray-200 rounded-md shadow">
        <div className="flex items-center gap-2 flex-1 min-w-[240px]">
          <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
          <input
            defaultValue={query}
            name="q"
            placeholder="Search posts, users, equipment, communities..."
            className="flex-1 text-sm bg-transparent focus:outline-none"
          />
        </div>
        <select
          name="type"
          defaultValue={type}
          className="text-sm border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-500"
        >
          <option value="all">All Content</option>
          <option value="posts">Posts</option>
          <option value="users">Users</option>
          <option value="equipment">Equipment</option>
          <option value="communities">Communities</option>
          <option value="messages">Messages</option>
          <option value="polls">Polls</option>
          <option value="ai_conversations">AI Conversations</option>
        </select>
        <button
          type="submit"
          className="px-3 py-1.5 rounded bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 transition-colors"
        >
          Search
        </button>
      </form>

      {/* Authentication Notice */}
      {!isAuthenticated && query && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3">
          <p className="text-sm text-yellow-800">
            💡 <strong>Sign in for better results:</strong> Authenticated users can access more content and personalized search results.
          </p>
        </div>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-2 text-sm text-gray-600">Searching...</span>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-3">
          <p className="text-sm text-red-800">
            ⚠️ <strong>Search Error:</strong> {error.message || 'Unable to perform search at this time.'}
          </p>
        </div>
      )}

      {/* Results */}
      {!isLoading && data && (
        <>
          {/* Results Summary */}
          {data.total > 0 && (
            <div className="text-sm text-gray-600">
              Found <strong>{data.total}</strong> result{data.total !== 1 ? 's' : ''} for "<strong>{data.query}</strong>"
            </div>
          )}

          {/* Results Grid */}
          <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
            {/* Posts */}
            {(type === 'all' || type === 'posts') && (
              <Section
                title="Posts"
                items={data.results.posts}
                count={data.counts?.posts}
                icon={DocumentTextIcon}
                empty="No matching posts found."
                render={post => (
                  <li key={post.id} className="py-2 first:pt-0 last:pb-0">
                    <a href={post.url} className="block group">
                      <p className="text-[13px] font-medium text-gray-800 group-hover:text-blue-600 truncate">
                        {post.title}
                      </p>
                      <p className="text-[11px] text-gray-500 line-clamp-2 mt-1">
                        {post.snippet}
                      </p>
                      <div className="flex items-center justify-between mt-1">
                        <p className="text-[10px] text-gray-400">
                          by {post.authorDisplayName || post.author}
                        </p>
                        {post.engagement && (
                          <p className="text-[10px] text-gray-400">
                            ❤️ {post.engagement.likes || 0}
                          </p>
                        )}
                      </div>
                    </a>
                  </li>
                )}
              />
            )}

            {/* Users */}
            {(type === 'all' || type === 'users') && (
              <Section
                title="Users"
                items={data.results.users}
                count={data.counts?.users}
                icon={UserIcon}
                empty="No matching users found."
                render={user => (
                  <li key={user.id} className="py-2 first:pt-0 last:pb-0">
                    <a href={user.url} className="block group">
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center text-xs font-medium">
                          {user.displayName?.charAt(0) || user.username?.charAt(0) || '?'}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-[13px] font-medium text-gray-800 group-hover:text-green-600 truncate">
                            {user.displayName || user.username}
                          </p>
                          <p className="text-[11px] text-gray-500 truncate">
                            @{user.username} {user.isVerified && '✓'}
                          </p>
                          {user.role && (
                            <p className="text-[10px] text-gray-400">{user.role}</p>
                          )}
                        </div>
                      </div>
                    </a>
                  </li>
                )}
              />
            )}

            {/* Equipment */}
            {(type === 'all' || type === 'equipment') && (
              <Section
                title="Equipment"
                items={data.results.equipment}
                count={data.counts?.equipment}
                icon={WrenchScrewdriverIcon}
                empty="No matching equipment found."
                render={equipment => (
                  <li key={equipment.id} className="py-2 first:pt-0 last:pb-0">
                    <a href={equipment.url} className="block group">
                      <p className="text-[13px] font-medium text-gray-800 group-hover:text-indigo-600 truncate">
                        {equipment.name}
                      </p>
                      <p className="text-[11px] text-gray-500 line-clamp-2 mt-1">
                        {equipment.description}
                      </p>
                      <div className="flex items-center justify-between mt-1">
                        <p className="text-[10px] text-gray-400">{equipment.location}</p>
                        <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${
                          equipment.status === 'operational' ? 'bg-green-100 text-green-800' :
                          equipment.status === 'maintenance' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {equipment.status}
                        </span>
                      </div>
                    </a>
                  </li>
                )}
              />
            )}

            {/* Communities */}
            {(type === 'all' || type === 'communities') && (
              <Section
                title="Communities"
                items={data.results.communities}
                count={data.counts?.communities}
                icon={UserGroupIcon}
                empty="No matching communities found."
                render={community => (
                  <li key={community.id} className="py-2 first:pt-0 last:pb-0">
                    <a href={community.url} className="block group">
                      <p className="text-[13px] font-medium text-gray-800 group-hover:text-purple-600 truncate">
                        {community.name}
                      </p>
                      <p className="text-[11px] text-gray-500 line-clamp-2 mt-1">
                        {community.description}
                      </p>
                      <p className="text-[10px] text-gray-400 mt-1">
                        {community.members} member{community.members !== 1 ? 's' : ''}
                      </p>
                    </a>
                  </li>
                )}
              />
            )}

            {/* Messages */}
            {(type === 'all' || type === 'messages') && (
              <Section
                title="Messages"
                items={data.results.messages}
                count={data.counts?.messages}
                icon={ChatBubbleLeftRightIcon}
                empty="No matching messages found."
                render={message => (
                  <li key={message.id} className="py-2 first:pt-0 last:pb-0">
                    <a href={message.url} className="block group">
                      <p className="text-[13px] font-medium text-gray-800 group-hover:text-orange-600 truncate">
                        Message from {message.author?.username || 'Unknown'}
                      </p>
                      <p className="text-[11px] text-gray-500 line-clamp-2 mt-1">
                        {message.content}
                      </p>
                      <p className="text-[10px] text-gray-400 mt-1">
                        {new Date(message.createdAt).toLocaleDateString()}
                      </p>
                    </a>
                  </li>
                )}
              />
            )}

            {/* Polls */}
            {(type === 'all' || type === 'polls') && (
              <Section
                title="Polls"
                items={data.results.polls}
                count={data.counts?.polls}
                icon={ChartBarIcon}
                empty="No matching polls found."
                render={poll => (
                  <li key={poll.id} className="py-2 first:pt-0 last:pb-0">
                    <a href={poll.url} className="block group">
                      <p className="text-[13px] font-medium text-gray-800 group-hover:text-teal-600 truncate">
                        {poll.question}
                      </p>
                      <p className="text-[11px] text-gray-500 line-clamp-2 mt-1">
                        {poll.description}
                      </p>
                      <div className="flex items-center justify-between mt-1">
                        <p className="text-[10px] text-gray-400">
                          {poll.votesCount} vote{poll.votesCount !== 1 ? 's' : ''}
                        </p>
                        {poll.expiresAt && (
                          <p className="text-[10px] text-gray-400">
                            Expires {new Date(poll.expiresAt).toLocaleDateString()}
                          </p>
                        )}
                      </div>
                    </a>
                  </li>
                )}
              />
            )}

            {/* AI Conversations */}
            {(type === 'all' || type === 'ai_conversations') && (
              <Section
                title="AI Conversations"
                items={data.results.ai_conversations}
                count={data.counts?.ai_conversations}
                icon={CpuChipIcon}
                empty="No matching AI conversations found."
                render={conversation => (
                  <li key={conversation.id} className="py-2 first:pt-0 last:pb-0">
                    <a href={conversation.url} className="block group">
                      <p className="text-[13px] font-medium text-gray-800 group-hover:text-cyan-600 truncate">
                        {conversation.title}
                      </p>
                      <p className="text-[11px] text-gray-500 line-clamp-2 mt-1">
                        {conversation.summary}
                      </p>
                      <p className="text-[10px] text-gray-400 mt-1">
                        {conversation.messagesCount} message{conversation.messagesCount !== 1 ? 's' : ''}
                      </p>
                    </a>
                  </li>
                )}
              />
            )}
          </div>
        </>
      )}

      {/* No Results */}
      {!isLoading && data && data.total === 0 && query && !error && (
        <div className="text-center py-8">
          <MagnifyingGlassIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No results found</h3>
          <p className="text-sm text-gray-500 mb-4">
            We couldn't find anything matching "<strong>{data.query}</strong>".
          </p>
          <div className="text-xs text-gray-400">
            <p>Try adjusting your search:</p>
            <ul className="mt-2 space-y-1">
              <li>• Check your spelling</li>
              <li>• Use different keywords</li>
              <li>• Try searching in "All Content"</li>
              {!isAuthenticated && <li>• Sign in to access more content</li>}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
};

export default SearchResults;
