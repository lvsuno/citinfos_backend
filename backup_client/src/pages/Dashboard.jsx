import React, { useState, useMemo } from 'react';
import { useQuery } from 'react-query';
import socialAPI from '../services/social-api';
import FontAwesomeLoader from '../components/FontAwesomeLoader';
import { useJWTAuth } from '../hooks/useJWTAuth';
import PostRenderer from '../components/PostRenderer';
import {
  ChartBarSquareIcon,
  UserGroupIcon,
  ChatBubbleLeftRightIcon,
  ArrowTrendingUpIcon,
  WrenchScrewdriverIcon,
  CpuChipIcon,
  ExclamationTriangleIcon,
  CalendarIcon,
  CurrencyDollarIcon,
  CheckCircleIcon,
  ClockIcon,
  PlusIcon,
  PencilSquareIcon
} from '@heroicons/react/24/outline';
import CommunityIcon from '../components/ui/CommunityIcon';
import PostCreationModal from '../components/PostCreationModal';

// Helper function to extract filename from URL
const extractFilename = (url) => {
  if (!url) return 'Untitled';
  const parts = url.split('/');
  return parts[parts.length - 1] || 'Untitled';
};
import { dashboardAPI } from '../services/dashboardAPI';
import { pollsAPI } from '../services/pollsAPI';
import { communitiesAPI } from '../services/communitiesAPI';

const Dashboard = () => {
  const { user, isAuthenticated } = useJWTAuth();
  const { data: stats, isLoading: statsLoading } = useQuery('dashboard-stats', () => dashboardAPI.getDashboardStats());
  const { data: trendingPolls, isLoading: pollsLoading } = useQuery('trending-polls', () =>
    pollsAPI.getTrendingPollPosts()
  );
  const { data: trendingCommunityPosts } = useQuery('trending-community-posts', () => dashboardAPI.getTrendingContent());
  const { data: recommendedPosts } = useQuery('recommended-posts', () => dashboardAPI.getPersonalizedFeed());
  const { data: userCommunities } = useQuery('user-communities', () => communitiesAPI.getUserCommunities());
  const { data: serverPosts, refetch } = useQuery('server-posts', () => socialAPI.posts.list(), {
    staleTime: 30000, // 30 seconds
    refetchOnWindowFocus: true
  });

  // Fetch feed data for reposts
  const { data: feedData } = useQuery('feed-posts', () => socialAPI.posts.feed(), {
    staleTime: 30000,
    refetchOnWindowFocus: true
  });
  const [localPosts, setLocalPosts] = useState([]);
  const [showAllCommunities, setShowAllCommunities] = useState(false); // reintroduced for in-panel expansion

  // Post creation modal state
  const [showPostCreationModal, setShowPostCreationModal] = useState(false);

  // IP Location Debugger State
  const [showIPDebugger, setShowIPDebugger] = useState(true);
  const [ipDebugData, setIpDebugData] = useState(null);
  const [customIP, setCustomIP] = useState('');
  const [isLoadingIPDebug, setIsLoadingIPDebug] = useState(false);

  // IP Location Debug Functions
  const fetchIPLocationDebug = async () => {
    setIsLoadingIPDebug(true);
    try {
      const data = await dashboardAPI.getIPLocationDebug();
      setIpDebugData(data);
    } catch (error) {
      console.error('Error fetching IP debug data:', error);
      setIpDebugData({ success: false, error: error.message });
    } finally {
      setIsLoadingIPDebug(false);
    }
  };

  const fetchCustomIPDebug = async () => {
    if (!customIP.trim()) {
      alert('Please enter an IP address');
      return;
    }

    setIsLoadingIPDebug(true);
    try {
      const data = await dashboardAPI.getCustomIPLocationDebug(customIP.trim());
      setIpDebugData(data);
    } catch (error) {
      console.error('Error fetching custom IP debug data:', error);
      setIpDebugData({ success: false, error: error.message });
    } finally {
      setIsLoadingIPDebug(false);
    }
  };

  // Combine feed data for display (transformation now handled by PostRenderer)
  const allFeedItems = useMemo(() => {
    const feedItems = feedData?.results || [];
    const serverPostList = serverPosts || [];
    const localPostIds = new Set(localPosts.map(p => p.id));

    // Process feed items (includes reposts and regular posts)
    const processedFeedItems = feedItems.map(item => {
      if (item.type === 'repost') {
        // Return repost data as-is
        return {
          id: `repost-${item.repost_id}`,
          type: 'repost',
          created_at: item.created_at,
          ...item
        };
      } else {
        // Return regular post from feed as-is
        const post = item.data || item;
        return { ...post, type: 'post' };
      }
    });

    // Add server posts that aren't in feed and aren't local
    const feedPostIds = new Set(feedItems.map(item =>
      item.type === 'repost' ? item.data?.id : (item.data?.id || item.id)
    ));

    const uniqueServerPosts = serverPostList
      .filter(p => !localPostIds.has(p.id) && !feedPostIds.has(p.id))
      .map(post => ({ ...post, type: 'post' }));

    // Add local posts
    const localPostsWithType = localPosts.map(post => ({ ...post, type: 'post' }));

    // Combine all items and sort by created_at
    const combined = [...localPostsWithType, ...processedFeedItems, ...uniqueServerPosts];
    return combined.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
  }, [localPosts, serverPosts, feedData]);

  // Get trending poll posts (these are already complete post objects with polls)
  const trendingPollPosts = Array.isArray(trendingPolls) ? trendingPolls : (trendingPolls?.results || []);

  const addLocalPost = async (post) => {
    // If the post has a server ID (was successfully created on server),
    // refetch server posts instead of adding to local state
    if (post.id && !post.id.toString().startsWith('temp-') && !post.id.toString().startsWith('local-')) {
      // This post was successfully created on the server, refetch server posts
      await refetch();
    } else {
      // This is a true local-only post (e.g., draft or failed to save)
      setLocalPosts(prev => [post, ...prev]);
    }
  };

  // Handle new modal post creation
  const handlePostCreation = async (postData) => {
    try {
      // Transform the post data from modal format to API format
      const apiPost = {
        visibility: postData.visibility,
        customAudience: postData.customAudience,
      };

      // Handle different content types (now single type instead of multiple)
      if (postData.type === 'article' && postData.content.article) {
        apiPost.content = postData.content.article;
        apiPost.post_type = 'text';
      }

      if (postData.type === 'poll' && postData.content.poll) {
        const poll = postData.content.poll;
        apiPost.poll = {
          question: poll.question,
          options: poll.options.map((text, index) => ({ text, order: index })),
          allow_multiple_votes: poll.allowMultiple,
          expires_at: new Date(Date.now() + poll.expirationHours * 60 * 60 * 1000).toISOString()
        };
        apiPost.post_type = 'poll';
      }

      if (postData.type === 'media' && postData.content.media && postData.content.media.length > 0) {
        // For now, we'll handle media as attachments
        // This might need more sophisticated handling depending on your API
        apiPost.attachments = postData.content.media.map(media => ({
          type: media.type,
          file: media.file,
          name: media.name
        }));

        apiPost.post_type = 'media';
      }

      // Submit to the existing addLocalPost function
      await addLocalPost(apiPost);
    } catch (error) {
      console.error('Error creating post:', error);
      throw new Error('Failed to create post. Please try again.');
    }
  };

  // Media upload handlers for the modal
  const handleImageUpload = async (file) => {
    // Implement your image upload logic here
    // For now, return a placeholder URL
    return URL.createObjectURL(file);
  };

  const handleVideoUpload = async (file) => {
    // Implement your video upload logic here
    return URL.createObjectURL(file);
  };

  const handleAudioUpload = async (file) => {
    // Implement your audio upload logic here
    return URL.createObjectURL(file);
  };
  const updateLocalPost = async (id, data) => {
    try {
      // Update server-side first
      const response = await socialAPI.posts.update(id, data);

      // Transform the server response to match frontend expectations
      let transformedResponse = { ...response };

      // Add a timestamp to force React re-render
      transformedResponse._lastUpdated = Date.now();

      // Transform polls if present in response
      if (response.polls && Array.isArray(response.polls)) {
        const transformedPolls = response.polls.map(serverPoll => {
          // Transform poll options to include user voting state
          const transformedOptions = (serverPoll.options || []).map(option => ({
            id: option.id,
            text: option.text,
            order: option.order,
            vote_count: option.votes_count,
            percentage: option.vote_percentage,
            user_has_voted: option.user_has_voted
          }));

          return {
            ...serverPoll,
            // Map backend fields to frontend expectations
            user_vote: serverPoll.user_votes || [], // user_votes -> user_vote
            user_voted: serverPoll.user_has_voted || false, // user_has_voted -> user_voted
            allows_multiple_votes: serverPoll.multiple_choice || false, // multiple_choice -> allows_multiple_votes
            vote_count: serverPoll.total_votes || 0, // total_votes -> vote_count
            voter_count: serverPoll.voters_count || 0, // voters_count -> voter_count
            options: transformedOptions
          };
        });

        transformedResponse.polls = transformedPolls;
      }

      // Check if post exists in localPosts first
      const existsInLocal = localPosts.some(p => p.id === id);

      if (existsInLocal) {
        // Update existing local post
        setLocalPosts(prev => prev.map(p => {
          if (p.id === id) {
            return { ...p, ...transformedResponse };
          }
          return p;
        }));
      } else {
        // Post is from server, add updated version to local posts
        // This ensures the updated version takes precedence in allPosts
        setLocalPosts(prev => [transformedResponse, ...prev]);
      }

      // Refresh server posts to get latest data (but updated post will show immediately from localPosts)
      refetch();
    } catch (error) {
      console.error('Error updating post:', error);
      // Still update local state for optimistic UI
      setLocalPosts(prev => prev.map(p => p.id === id ? { ...p, ...data } : p));
    }
  };
  const deleteLocalPost = async (id) => {
    try {
      // Check if post exists in localPosts or serverPosts
      const existsInLocal = localPosts.some(p => p.id === id);
      const existsInServer = serverPosts?.some(p => p.id === id);

      // If it exists on server or we're not sure, try to delete from server
      if (existsInServer || !existsInLocal) {
        try {
          await socialAPI.posts.delete(id);
        } catch (error) {
          // If it's a 404, the post doesn't exist on server (already deleted or local-only)
          if (error.response?.status === 404) {
            // Post doesn't exist on server, removing from local state only
          } else {
            // Re-throw other errors
            throw error;
          }
        }
      }

      // Remove from local state regardless
      setLocalPosts(prev => prev.filter(p => {
        if (p.id === id) {
          p.attachments?.forEach(a => { if (a.preview) { try { URL.revokeObjectURL(a.preview); } catch(_){} } });
        }
        return p.id !== id;
      }));

      // Refresh server posts to reflect the change
      await refetch();
    } catch (error) {
      console.error('Error deleting post:', error);
      const errorMessage = error.response?.data?.detail || error.message || 'Unknown error occurred';
      alert(`Failed to delete post: ${errorMessage}`);
    }
  };

  const handleVote = async (pollId, optionIds) => {
    try {
      await pollsAPI.votePoll(pollId, optionIds);

    } catch (error) {
      console.error('Error voting on poll:', error);
    }
  };

  const statCards = [
    { title: 'Polls Created', value: stats?.polls_created || 0, icon: ChartBarSquareIcon, color: 'blue' },
    { title: 'Votes Cast', value: stats?.votes_cast || 0, icon: ArrowTrendingUpIcon, color: 'green' },
    { title: 'Communities', value: stats?.communities_joined || 0, icon: UserGroupIcon, color: 'purple' },
    { title: 'Equipment', value: stats?.equipment_total || 0, icon: WrenchScrewdriverIcon, color: 'orange' },
    { title: 'AI Conversations', value: stats?.ai_conversations || 0, icon: CpuChipIcon, color: 'indigo' },
    { title: 'Monthly AI Cost', value: `$${(stats?.ai_cost_month || 0).toFixed(2)}`, icon: CurrencyDollarIcon, color: 'green' },
  ];

  const equipmentStats = [
    { status: 'Operational', count: stats?.equipment_operational || 0, icon: CheckCircleIcon, color: 'green' },
    { status: 'Maintenance', count: stats?.equipment_maintenance || 0, icon: CalendarIcon, color: 'yellow' },
    { status: 'Broken', count: stats?.equipment_broken || 0, icon: ExclamationTriangleIcon, color: 'red' },
  ];

  if (statsLoading || pollsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <FontAwesomeLoader>
      <div className="space-y-6">
        {/* FontAwesome is now loaded locally via index.css */}

      {/* Animated Banner */}
      <div className="relative overflow-hidden rounded-xl shadow border border-blue-200/40">
        <div className="banner-animated p-3 sm:p-4 text-white">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center justify-center h-7 w-7 rounded-lg bg-white/20 backdrop-blur-sm shadow-sm">
                <CpuChipIcon className="h-4 w-4" />
              </span>
              <h1 className="text-base sm:text-lg font-bold tracking-tight drop-shadow m-0">Welcome to CityHub</h1>
            </div>
            <span className="text-[10px] sm:text-xs text-blue-50/90 font-medium whitespace-nowrap sm:ml-auto">Realtime snapshot of your community engagement, equipment health & AI activity. Stay proactive and discover what matters now.</span>
          </div>
          {/* Floating accents */}
          <div className="pointer-events-none absolute inset-0">
            <div className="absolute -top-6 -right-6 h-20 w-20 rounded-full bg-pink-400/30 blur-2xl animate-pulse" />
            <div className="absolute bottom-0 left-0 h-16 w-16 rounded-full bg-indigo-400/30 blur-2xl animate-[pulse_5s_ease-in-out_infinite]" />
          </div>
        </div>
        {/* Animated gradient keyframes */}
        <style>{`
          @keyframes gradientShift { 0%,100% { background-position:0% 50%; } 50% { background-position:100% 50%; } }
          .banner-animated { background:linear-gradient(120deg,#1d4ed8,#7c3aed,#db2777,#2563eb); background-size:300% 300%; animation:gradientShift 12s ease-in-out infinite; }
        `}</style>
      </div>

      <div className="grid grid-cols-12 gap-6 items-start">
        {/* Left column with feed */}
        <div className="col-span-12 lg:col-span-8 space-y-6">
          {allFeedItems.length > 0 && (
            <section>
              <h2 className="text-lg font-semibold text-gray-900 mb-3">Recent Posts</h2>
              <PostRenderer
                posts={allFeedItems}
                onDelete={deleteLocalPost}
                onUpdate={updateLocalPost}
                onVote={handleVote}
                onPostUpdate={updateLocalPost}
                onPostDelete={deleteLocalPost}
                context="dashboard"
              />
            </section>
          )}
          {/* Trending Polls */}
          <section>
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-lg font-semibold text-gray-900">Trending Polls</h2>
              <a href="/polls" className="inline-flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors duration-200">
                <ChartBarSquareIcon className="w-4 h-4 mr-2" />
                View All Polls
              </a>
            </div>
            {pollsLoading ? (
              <div className="text-center py-8">
                <div className="animate-spin h-6 w-6 border-2 border-blue-500 border-t-transparent rounded-full mx-auto"></div>
              </div>
            ) : trendingPollPosts.length > 0 ? (
              <PostRenderer
                posts={trendingPollPosts}
                onVote={handleVote}
                context="trending-polls"
                className="space-y-4"
              />
            ) : (
              <div className="text-center py-10 bg-white rounded-lg shadow">
                <CommunityIcon Icon={ChartBarSquareIcon} size="lg" color="gray" className="mx-auto mb-3" />
                <p className="text-gray-500 text-sm">No trending polls right now.</p>
              </div>
            )}
          </section>

          {/* Trending Community Posts */}
          <section>
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-lg font-semibold text-gray-900">Trending Community Posts</h2>
              <a href="/communities" className="text-blue-600 hover:text-blue-700 text-sm font-medium">Explore communities →</a>
            </div>
            <div className="space-y-3">
              {Array.isArray(trendingCommunityPosts) && trendingCommunityPosts?.map((p, index) => (
                <div key={`community-post-${p.id || index}`} className="bg-white rounded-lg p-4 shadow flex items-start gap-4 border border-gray-100 hover:border-blue-200 transition-colors">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">{p.title}</p>
                    <p className="text-[11px] text-gray-500 mt-0.5">by <span className="text-gray-700 font-semibold">{p.author}</span> • {p.community}</p>
                    <div className="flex items-center gap-4 mt-2 text-[11px] text-gray-500">
                      <span>👍 {p.likes}</span><span>💬 {p.comments}</span>
                    </div>
                  </div>
                  <button className="text-xs px-2 py-1 rounded-md bg-blue-50 text-blue-600 hover:bg-blue-100 whitespace-nowrap">Open</button>
                </div>
              ))}
            </div>
            {(!Array.isArray(trendingCommunityPosts) || trendingCommunityPosts.length === 0) && (
              <div className="text-center py-8 bg-white rounded-lg shadow text-sm text-gray-500">No trending posts.</div>
            )}
          </section>

          {/* Recommended For You */}
          <section>
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-lg font-semibold text-gray-900">Recommended For You</h2>
              <a href="/ab-testing" className="text-blue-600 hover:text-blue-700 text-sm font-medium">Why these? →</a>
            </div>
            <div className="space-y-3">
              {recommendedPosts?.map((r, index) => (
                <div key={`recommended-${r.id || index}`} className="bg-white rounded-lg p-4 shadow flex items-start justify-between border border-gray-100 hover:border-indigo-200 transition-colors">
                  <div>
                    <p className="text-sm font-medium text-gray-900">{r.title}</p>
                    <p className="text-[11px] text-gray-500 mt-1">{r.reason}</p>
                  </div>
                  <button className="text-xs px-2 py-1 rounded-md bg-indigo-50 text-indigo-600 hover:bg-indigo-100">View</button>
                </div>
              ))}
            </div>
            {(!recommendedPosts || recommendedPosts.length === 0) && (
              <div className="text-center py-8 bg-white rounded-lg shadow text-sm text-gray-500">No recommendations yet.</div>
            )}
          </section>
        </div>

        {/* Sidebar (right) */}
        <aside className="col-span-12 lg:col-span-4 space-y-6 lg:sticky lg:top-4 self-start">
          {/* Create Post Button */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
            <button
              onClick={() => setShowPostCreationModal(true)}
              className="flex items-center justify-center w-full p-4 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white rounded-lg font-medium transition-all duration-200 shadow-md hover:shadow-lg transform hover:scale-105"
            >
              <PencilSquareIcon className="w-5 h-5 mr-2" />
              Create New Post
            </button>
          </div>




          {/* Recent Communities */}
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-semibold text-gray-900">Recent Communities</h3>
              {userCommunities?.filter(c=>c.member).length > 0 && (
                <button onClick={()=>setShowAllCommunities(s=>!s)} className="text-[11px] font-medium text-blue-600 hover:text-blue-700">
                  {showAllCommunities ? 'Hide' : 'All'} →
                </button>
              )}
            </div>
            {!userCommunities && <p className="text-[11px] text-gray-400">Loading...</p>}
            {userCommunities && userCommunities.filter(c=>c.member).length === 0 && (
              <p className="text-[11px] text-gray-400">No joined communities yet.</p>
            )}
            {userCommunities && userCommunities.filter(c=>c.member).length > 0 && (() => {
              const memberCommunities = userCommunities.filter(c=>c.member).sort((a,b)=>b.lastVisited - a.lastVisited);
              const displayList = showAllCommunities ? memberCommunities : memberCommunities.slice(0,3);
              const list = (
                <div className={`${showAllCommunities ? 'max-h-56 overflow-auto pr-1 space-y-1' : 'space-y-2'} transition-all`}>
                  {displayList.map((c, idx) => {
                    const minsAgo = Math.floor((Date.now() - c.lastVisited)/60000);
                    const rel = minsAgo < 60 ? `${minsAgo}m` : `${Math.floor(minsAgo/60)}h`;
                    return (
                      <a key={`community-${c.id || idx}`} href={`/c/${c.id}`} className={`flex items-center justify-between text-[11px] px-2 py-2 rounded border ${idx===0 && !showAllCommunities ? 'border-indigo-200 bg-indigo-50/50 hover:border-indigo-300 hover:bg-indigo-50' : 'border-gray-100 hover:border-gray-200 hover:bg-gray-50'} group`}>
                        <span className="truncate text-gray-700 font-medium group-hover:text-gray-900">{c.name}</span>
                        <span className="ml-3 shrink-0 text-[10px] text-gray-400 tabular-nums">{rel}</span>
                      </a>
                    );
                  })}
                </div>
              );
              return list;
            })()}
          </div>

            {/* AI Usage */}
          <div className="bg-white rounded-lg shadow p-4">
            <h3 className="text-sm font-semibold text-gray-900 mb-3">AI Usage Today</h3>
            <div className="space-y-2 text-[12px]">
              <div className="flex items-center justify-between"><span className="text-gray-600 flex items-center gap-1"><ChatBubbleLeftRightIcon className="h-4 w-4 text-blue-600" /> Messages</span><span className="font-semibold text-blue-600">{stats?.ai_messages_today || 0}</span></div>
              <div className="flex items-center justify-between"><span className="text-gray-600 flex items-center gap-1"><CurrencyDollarIcon className="h-4 w-4 text-green-600" /> Cost</span><span className="font-semibold text-green-600">${(stats?.ai_cost_today || 0).toFixed(2)}</span></div>
              <div className="flex items-center justify-between"><span className="text-gray-600 flex items-center gap-1"><ClockIcon className="h-4 w-4 text-purple-600" /> Active</span><span className="font-semibold text-purple-600">{stats?.ai_conversations || 0}</span></div>
            </div>
            <div className="mt-3 pt-3 border-t border-gray-100 text-right">
              <a href="/ai-conversations" className="text-[11px] font-medium text-blue-600 hover:text-blue-700">Open AI Chat →</a>
            </div>
          </div>

          {/* IP Location Debugger */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg shadow p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-gray-900">🔍 IP Location Debugger</h3>
              <button
                onClick={() => setShowIPDebugger(!showIPDebugger)}
                className="text-xs px-2 py-1 rounded-md bg-gray-100 text-gray-600 hover:bg-gray-200"
              >
                {showIPDebugger ? 'Hide' : 'Show'}
              </button>
            </div>

            {showIPDebugger && (
              <div className="space-y-3">
                <div className="flex gap-2">
                  <button
                    onClick={fetchIPLocationDebug}
                    disabled={isLoadingIPDebug}
                    className="text-xs px-3 py-1 rounded-md bg-blue-100 text-blue-600 hover:bg-blue-200 disabled:opacity-50"
                  >
                    {isLoadingIPDebug ? 'Loading...' : 'Get My IP Location'}
                  </button>
                </div>

                <div className="border-t pt-2">
                  <div className="flex gap-1 mb-2">
                    <input
                      type="text"
                      placeholder="Enter IP address"
                      value={customIP}
                      onChange={(e) => setCustomIP(e.target.value)}
                      className="text-xs p-1 border rounded flex-1"
                    />
                    <button
                      onClick={fetchCustomIPDebug}
                      disabled={isLoadingIPDebug}
                      className="text-xs px-2 py-1 rounded-md bg-green-100 text-green-600 hover:bg-green-200 disabled:opacity-50"
                    >
                      Test
                    </button>
                  </div>
                </div>

                {ipDebugData && (
                  <div className="bg-gray-50 rounded p-2 mt-2">
                    <div className="text-xs text-gray-600 mb-1">
                      <strong>Status:</strong> {ipDebugData.success ? '✅ Success' : '❌ Failed'}
                    </div>

                    {ipDebugData.success ? (
                      <div className="space-y-1 text-xs">
                        <div><strong>IP:</strong> {ipDebugData.client_ip || ipDebugData.provided_ip}</div>
                        {ipDebugData.location_data?.country && (
                          <div><strong>Country:</strong> {ipDebugData.location_data.country}</div>
                        )}
                        {ipDebugData.location_data?.city && (
                          <div><strong>City:</strong> {ipDebugData.location_data.city}</div>
                        )}
                        {ipDebugData.location_data?.region && (
                          <div><strong>Region:</strong> {ipDebugData.location_data.region}</div>
                        )}
                        {ipDebugData.location_data?.latitude && ipDebugData.location_data?.longitude && (
                          <div>
                            <strong>Coordinates:</strong> {ipDebugData.location_data.latitude.toFixed(4)}, {ipDebugData.location_data.longitude.toFixed(4)}
                          </div>
                        )}
                        {ipDebugData.location_data?.timezone && (
                          <div><strong>Timezone:</strong> {ipDebugData.location_data.timezone}</div>
                        )}
                      </div>
                    ) : (
                      <div className="text-xs text-red-600">
                        <strong>Error:</strong> {ipDebugData.error || 'Unknown error'}
                      </div>
                    )}

                    <details className="mt-2">
                      <summary className="text-xs cursor-pointer text-gray-500">Raw Data</summary>
                      <pre className="text-xs text-gray-600 mt-1 bg-white p-1 rounded border overflow-auto max-h-32">
                        {JSON.stringify(ipDebugData, null, 2)}
                      </pre>
                    </details>
                  </div>
                )}
              </div>
            )}
          </div>
        </aside>
      </div>

      {/* Quick Actions (full width below) */}
      <div className="bg-white rounded-lg shadow p-5">
        <h3 className="text-sm font-bold text-gray-900 mb-3">Quick Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <a href="/polls/create" className="flex items-center p-4 border-2 border-dashed border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors">
            <CommunityIcon Icon={ChartBarSquareIcon} size="lg" color="gray" className="mr-3" />
            <div><p className="font-medium text-gray-900 text-sm">Create Poll</p><p className="text-[11px] text-gray-500">Ask your community</p></div>
          </a>
          <a href="/communities" className="flex items-center p-4 border-2 border-dashed border-gray-200 rounded-lg hover:border-purple-500 hover:bg-purple-50 transition-colors">
            <CommunityIcon Icon={UserGroupIcon} size="lg" color="gray" className="mr-3" />
            <div><p className="font-medium text-gray-900 text-sm">Join Community</p><p className="text-[11px] text-gray-500">Find your tribe</p></div>
          </a>
          <a href="/profile" className="flex items-center p-4 border-2 border-dashed border-gray-200 rounded-lg hover:border-green-500 hover:bg-green-50 transition-colors">
            <CommunityIcon Icon={ChatBubbleLeftRightIcon} size="lg" color="gray" className="mr-3" />
            <div><p className="font-medium text-gray-900 text-sm">Update Profile</p><p className="text-[11px] text-gray-500">Customize your presence</p></div>
          </a>
        </div>
      </div>

      {/* Post Creation Modal */}
      <PostCreationModal
        isOpen={showPostCreationModal}
        onClose={() => setShowPostCreationModal(false)}
        onSubmit={handlePostCreation}
        onImageUpload={handleImageUpload}
        onVideoUpload={handleVideoUpload}
        onAudioUpload={handleAudioUpload}
      />
      </div>
    </FontAwesomeLoader>
  );
};

export default Dashboard;
