import React, { useState, useEffect } from 'react';
import { useParams, Navigate } from 'react-router-dom';
import { useQuery } from 'react-query';
import { useJWTAuth } from '../hooks/useJWTAuth';
import CoverSection from '../components/profile/CoverSection';
import ProfileTabs from '../components/profile/ProfileTabs';
import ActivityList from '../components/profile/ActivityList';
import BadgesGrid from '../components/profile/BadgesGrid';
import { profileAPI } from '../services/profileAPI';
import { socialAPI } from '../services/social-api';
import PostCard from '../components/social/PostCard';
import RepostCard from '../components/social/RepostCard';
import UserBadgeList from '../components/UserBadgeList';
import FollowToggleButton from '../components/FollowToggleButton';
import UserProfileCard from '../components/UserProfileCard';
import FontAwesomeLoader from '../components/FontAwesomeLoader';

/**
 * UserProfile - View other users' profiles
 * This is a read-only version of the profile page for viewing other users
 */
const UserProfile = () => {
  const { userId, username } = useParams();
  const { user: currentUser, isAuthenticated } = useJWTAuth();
  const [tab, setTab] = useState('overview');
  const [resolvedUserId, setResolvedUserId] = useState(userId);

  // If we have a username but no userId, we need to resolve it
  const shouldResolveUsername = username && !userId;

  // Resolve username to userId if needed
  const { data: userSearchData, isLoading: searchLoading } = useQuery(
    ['search-user', username],
    async () => {
      if (!shouldResolveUsername) return null;
      // Use the search mentionable endpoint to find user by username
      const response = await profileAPI.get(`/profiles/search_mentionable/?q=${username}&limit=1`);
      return response.results && response.results.length > 0 ? response.results[0] : null;
    },
    {
      enabled: shouldResolveUsername,
      retry: false
    }
  );

  // Update resolvedUserId when we get search results
  useEffect(() => {
    if (userSearchData) {
      setResolvedUserId(userSearchData.id);
    } else if (userId) {
      setResolvedUserId(userId);
    }
  }, [userSearchData, userId]);

  // Check if this is the current user's profile, redirect if so
  const isOwnProfile = currentUser?.profile?.id === resolvedUserId || currentUser?.id === resolvedUserId;

  // Get user profile data
  const { data: profileData, isLoading: profileLoading, error: profileError } = useQuery(
    ['user-profile', resolvedUserId],
    () => profileAPI.getUserProfile(resolvedUserId),
    {
      enabled: !!resolvedUserId && !isOwnProfile,
      retry: false  // Don't retry on auth errors
    }
  );

  // Server-side filtering removes the need for separate posts query
  // Posts are now included in profile response based on viewing permissions
  const posts = profileData?.recent_posts || [];
  const context = profileData?.context || {};
  const canViewPosts = context.can_view_posts || false;
  const canInteract = context.can_interact || false;
  const canViewBadges = context.can_view_badges || false;

  // Get user stats - only if we have profile data
  const { data: statsData } = useQuery(
    ['user-stats', resolvedUserId],
    () => profileAPI.getUserStats(resolvedUserId),
    {
      enabled: !!resolvedUserId && !isOwnProfile && !!profileData,
      retry: false
    }
  );

  // Follow status is now part of the profile context from server
  const isFollowingUser = context.is_following || false;
  const followStatus = {
    isFollowing: isFollowingUser,
    status: isFollowingUser ? 'approved' : null
  };

  // Get user badges - removed, now fetched directly in BadgesGrid
  // const { data: badgesData } = useQuery(
  //   ['user-badges', userId],
  //   () => profileAPI.getUserBadges(userId),
  //   {
  //     enabled: !!userId && !isOwnProfile && !!profileData,
  //     retry: false
  //   }
  // );

  // Sample badge data removed - now fetched directly in BadgesGrid component

  // If this is the current user's profile, redirect to /profile
  if (isOwnProfile) {
    return <Navigate to="/profile" replace />;
  }

  // Loading state
  if (profileLoading || searchLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">Loading profile...</div>
      </div>
    );
  }

  // Handle username resolution failure
  if (shouldResolveUsername && !searchLoading && !userSearchData) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">User Not Found</h2>
          <p className="text-gray-600">No user found with username @{username}</p>
        </div>
      </div>
    );
  }

  // Error state - handle different types of errors
  if (profileError) {
    // Check if it's an authentication error
    if (profileError.response?.status === 401) {
      return (
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center max-w-md">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Profile Not Accessible</h2>
            <p className="text-gray-600 mb-4">
              This user's profile is private or you need to be logged in to view it.
            </p>
            <button
              onClick={() => window.location.href = '/login'}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Sign In
            </button>
          </div>
        </div>
      );
    }

    // Other errors (404, 500, etc.)
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">User Not Found</h2>
          <p className="text-gray-600">The user profile you're looking for doesn't exist.</p>
        </div>
      </div>
    );
  }

  // Still loading or no data yet
  if (!profileData) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">Loading profile...</div>
      </div>
    );
  }

  const user = {
    id: profileData.id || profileData.user?.id,
    username: profileData.user_username || 'Unknown',
    full_name: profileData.display_name || profileData.full_name ||
               `${profileData.user_first_name || ''} ${profileData.user_last_name || ''}`.trim() ||
               profileData.user_username || 'Unknown User',
    avatar: profileData.profile_picture || '',
    bio: profileData.bio || 'This user hasn\'t added a bio yet.',
    cover: profileData.cover_media || '',
    coverMediaType: profileData.cover_media_type || 'image',
    stats: statsData || {
      polls_created: profileData.posts_count || 0,
      votes_cast: 0,
      communities_joined: 0,
      posts_created: profileData.posts_count || 0,
      posts_count: profileData.posts_count || 0,
      comments_count: 8,
      likes_given_count: 24,
      followers_count: 6,
      equipment_count: 4
    },
    joined_at: profileData.user?.date_joined || profileData.created_at || new Date().toISOString()
  };

  // Privacy and permission logic now comes from server
  const isUserPrivate = profileData.is_private || false;

  // Use posts from server response (already filtered)
  const userPosts = posts;

  return (
    <FontAwesomeLoader>
      <div className="max-w-7xl mx-auto">
        {/* Cover Section */}
        <div className="relative">
          <CoverSection
            coverUrl={user.cover}
            coverMediaType={user.coverMediaType}
            isOwner={isOwnProfile}
          />
        </div>

        {/* Avatar and User Info - Positioned at bottom of cover */}
        <div className="relative -mt-16 px-4 sm:px-6">
          <div className="flex items-end gap-4">
            <div className="relative">
              <div className="h-28 w-28 rounded-full bg-gradient-to-br from-indigo-500 to-blue-500 flex items-center justify-center text-white text-3xl font-bold ring-4 ring-white shadow-md shadow-black/10">
                {user.avatar ? (
                  <img src={user.avatar} alt={user.username} className="h-full w-full rounded-full object-cover" />
                ) : (
                  (user.username || 'U').charAt(0).toUpperCase()
                )}
              </div>
            </div>
            <div className="pb flex-1">
              <div className="flex items-center gap-3">
                <div>
                  <h1 className="text-2xl font-bold text-gray-900">{user.full_name}</h1>
                  <p className="text-sm text-gray-600">@{user.username}</p>
                </div>

                {/* Display badges and follow toggle */}
                <div className="flex items-center gap-3">
                  {/* Display badges for authenticated users viewing private profiles, or public profiles */}
                  {resolvedUserId && canViewBadges && (
                    <UserBadgeList
                      userId={resolvedUserId}
                      maxVisible={5}
                      badges={profileData?.badges}
                    />
                  )}

                  {/* Follow toggle button for authenticated non-owners */}
                  {!isOwnProfile && isAuthenticated && (
                    <FollowToggleButton
                      userId={resolvedUserId}
                      username={user.username}
                      isFollowing={context.is_following}
                      followStatus={context.follow_status}
                      isPrivate={isUserPrivate}
                      disabled={!resolvedUserId}
                    />
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Tabs and Content */}
        <div className="space-y-3 px-4 sm:px-6 mt-6">
          {/* Show private message if user cannot view content */}
          {context.private_message ? (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-8 text-center">
              <div className="flex flex-col items-center space-y-4">
                <i className="fas fa-lock text-yellow-600 text-4xl"></i>
                <h3 className="text-lg font-medium text-gray-900">Private Profile</h3>
                <p className="text-gray-600 max-w-md">{context.private_message}</p>

                {/* Show follow button if authenticated user viewing private profile */}
                {!isOwnProfile && context.is_authenticated && !context.is_following && (
                  <div className="pt-2">
                    <FollowToggleButton
                      userId={resolvedUserId}
                      username={user.username}
                      isFollowing={false}
                      followStatus={context.follow_status}
                      isPrivate={true}
                      disabled={false}
                    />
                  </div>
                )}
              </div>
            </div>
          ) : (
            <>
              {/* Tabs */}
              <ProfileTabs
                tabs={[
                  {key: 'overview', label: 'Overview'},
                  {key: 'posts', label: 'Posts'}
                ]}
                active={tab}
                onChange={setTab}
              />

          {/* Tab Content - This is the scrollable area with space for tooltips */}
          <div className="overflow-y-auto overflow-x-visible" style={{position: 'relative', zIndex: 50}}>
            {tab === 'overview' && (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-8" style={{overflow: 'visible', position: 'relative', zIndex: 100}}>
                <div className="lg:col-span-1 space-y-6" style={{overflow: 'visible', position: 'relative', zIndex: 100}}>
                  <div style={{position: 'relative', zIndex: 1000, isolation: 'isolate'}}>
                    <UserProfileCard
                      userId={resolvedUserId}
                      userName={user.username}
                      userBio={user.bio}
                      avatar={user.avatar}
                      postsCount={user.stats.posts_count || 0}
                      commentsCount={user.stats.comments_count || 0}
                      pollsCount={user.stats.polls_created || 0}
                      memberSince={user.joined_at}
                      maxVisibleBadges={4}
                      isPrivate={isUserPrivate}
                      canViewDetails={canViewPosts || canViewBadges}
                      context={context}
                    />
                  </div>
                </div>
                <div className="lg:col-span-2 space-y-6">
                  {/* Recent Posts - Only show if user is public or current user is following */}
                  {canViewPosts ? (
                    <div className="bg-white rounded-lg shadow p-6">
                      <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Posts</h2>
                      {userPosts.length > 0 ? (
                        <div className="space-y-4">
                          {userPosts.slice(0, 3).map((post) => {
                            const uniqueKey = post.type === 'repost' ?
                              `repost-${post.repost_id || post.id}` :
                              `post-${post.id}`;

                            return post.type === 'repost' ? (
                              <RepostCard
                                key={uniqueKey}
                                repostData={post}
                                readOnly={!canInteract}
                              />
                            ) : (
                              <PostCard
                                key={uniqueKey}
                                post={post}
                                showBorder={false}
                                readOnly={!canInteract}
                                hideActions={!canInteract}
                              />
                            );
                          })}
                          {userPosts.length > 3 && (
                            <button
                              onClick={() => setTab('posts')}
                              className="text-sm text-blue-600 hover:text-blue-800 font-medium"
                            >
                              View all posts ({userPosts.length})
                            </button>
                          )}
                        </div>
                      ) : (
                        <p className="text-gray-500 text-sm">This user hasn't posted anything yet.</p>
                      )}
                    </div>
                  ) : (
                    <div className="bg-white rounded-lg shadow p-6">
                      <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Posts</h2>
                      <div className="text-center py-8">
                        <div className="h-12 w-12 mx-auto mb-4 rounded-full bg-gray-100 flex items-center justify-center">
                          <svg className="h-6 w-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                          </svg>
                        </div>
                        <p className="text-gray-500 text-sm">This account is private</p>
                        <p className="text-gray-400 text-xs mt-1">Follow this user to see their posts</p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {tab === 'posts' && (
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">All Posts</h2>
                {canViewPosts ? (
                  <>
                    {userPosts.length > 0 ? (
                      <div className="space-y-6">
                        {userPosts.map((post) => {
                          const uniqueKey = post.type === 'repost' ?
                            `repost-${post.repost_id || post.id}` :
                            `post-${post.id}`;

                          return post.type === 'repost' ? (
                            <RepostCard
                              key={uniqueKey}
                              repostData={post}
                              readOnly={!canInteract}
                            />
                          ) : (
                            <PostCard
                              key={uniqueKey}
                              post={post}
                              readOnly={!canInteract}
                              hideActions={!canInteract}
                            />
                          );
                        })}
                      </div>
                    ) : (
                      <div className="text-center py-12">
                        <p className="text-gray-500">This user hasn't posted anything yet.</p>
                      </div>
                    )}
                  </>
                ) : (
                  <div className="text-center py-12">
                    <div className="h-16 w-16 mx-auto mb-4 rounded-full bg-gray-100 flex items-center justify-center">
                      <svg className="h-8 w-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                      </svg>
                    </div>
                    <p className="text-gray-500 text-lg font-medium mb-2">This account is private</p>
                    <p className="text-gray-400 text-sm">Follow this user to see their posts</p>
                  </div>
                )}
              </div>
            )}
          </div>
          </>
          )}
        </div>
      </div>
    </FontAwesomeLoader>
  );
};

export default UserProfile;
