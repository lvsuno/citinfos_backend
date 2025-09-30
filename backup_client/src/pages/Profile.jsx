import React, { useState, useEffect } from 'react';
import { UserCircleIcon, PencilIcon, CheckIcon, XMarkIcon, ChartBarSquareIcon, UserGroupIcon, ChatBubbleLeftRightIcon } from '@heroicons/react/24/outline';
import CommunityIcon from '../components/ui/CommunityIcon';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { useJWTAuth } from '../hooks/useJWTAuth';
import CoverSection from '../components/profile/CoverSection';
import AvatarUploader from '../components/profile/AvatarUploader';
import EditableBio from '../components/profile/EditableBio';
import ProfileTabs from '../components/profile/ProfileTabs';
import ActivityList from '../components/profile/ActivityList';
import LinksBlock from '../components/profile/LinksBlock';
import { getCoverMediaUrl } from '../utils/mediaUtils';
import SettingsPanel from '../components/profile/SettingsPanel';
import BadgesGrid from '../components/profile/BadgesGrid';
import UserBadgeList from '../components/UserBadgeList';
import UserProfileCard from '../components/UserProfileCard';
import PostRenderer from '../components/PostRenderer';
import toast from 'react-hot-toast';
import { profileAPI } from '../services/profileAPI';
import { socialAPI } from '../services/social-api';
import { pollsAPI } from '../services/pollsAPI';
import FontAwesomeLoader from '../components/FontAwesomeLoader';

const iconFor = (type) => {
  switch (type) {
    case 'poll': return <CommunityIcon Icon={ChartBarSquareIcon} size="sm" color="blue" />;
    case 'community': return <CommunityIcon Icon={UserGroupIcon} size="sm" color="purple" />;
    case 'post': return <CommunityIcon Icon={ChatBubbleLeftRightIcon} size="sm" color="green" />;
    case 'vote': return <CommunityIcon Icon={ChartBarSquareIcon} size="sm" color="indigo" />;
    default: return <CommunityIcon Icon={UserCircleIcon} size="sm" color="gray" />;
  }
};

const timeAgo = (ts) => {
  const diff = Date.now() - ts;
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'Just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
};

const Profile = () => {
  const { user: authUser, refreshUser } = useJWTAuth();
  const queryClient = useQueryClient();

  // --- Keep all hook declarations (useState/useEffect) near the top so the
  // hook call order remains stable between renders. This prevents React's
  // "Rendered more hooks than during the previous render" error.
  const [user, setUser] = useState(null);
  const [tab, setTab] = useState('overview');
  const [activity, setActivity] = useState([]);
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [pendingSaves, setPendingSaves] = useState({});
  const [links, setLinks] = useState([]);

  // Helper function for URL hash handling (declared before useEffect that uses it)
  const getTabFromHash = () => {
    try {
      const h = (window.location.hash || '').replace('#', '');
      const allowed = ['overview', 'posts', 'activity', 'settings'];
      return allowed.includes(h) ? h : 'overview';
    } catch (e) {
      return 'overview';
    }
  };

  // Sync tab with URL hash (allow links like /profile/#settings to open settings)
  useEffect(() => {
    // Set initial tab from hash
    setTab(getTabFromHash());

    const onPop = () => setTab(getTabFromHash());
    window.addEventListener('popstate', onPop);
    return () => window.removeEventListener('popstate', onPop);
  }, []);

  // Keep URL hash in sync when user switches tabs
  useEffect(() => {
    try {
      if (window.history && window.history.replaceState) {
        window.history.replaceState({}, '', `/profile/#${tab}`);
      } else {
        window.location.hash = tab;
      }
    } catch (e) {
      // ignore
    }
  }, [tab]);

  // Get user profile data from API
  const { data: profileData, isLoading: profileLoading } = useQuery(
    'user-profile',
    () => profileAPI.getCurrentUserProfile(),
    { enabled: !!authUser }
  );

  // Get user activity
  const { data: activityData, isLoading: activityLoading } = useQuery(
    'user-activity',
    () => profileAPI.getUserActivity(),
    { enabled: !!authUser }
  );

  // Get user badges (removed - now fetched directly in BadgesGrid)
  // const { data: badgesData } = useQuery(
  //   'user-badges',
  //   () => profileAPI.getUserBadges(),
  //   { enabled: !!authUser }
  // );

  // Sample badge data removed - now fetched directly in BadgesGrid component

  // Get user stats
  const { data: statsData } = useQuery(
    'user-stats',
    () => profileAPI.getUserStats(),
    { enabled: !!authUser }
  );

  // Get user posts
  const { data: postsData, isLoading: postsLoading, refetch: refetchPosts } = useQuery(
    'user-posts',
    () => {
      const profileId = authUser?.profile?.id;
      return socialAPI.posts.getUserPosts(profileId);
    },
    {
      enabled: !!authUser?.profile?.id,
      retry: false,
      staleTime: 0, // Don't use stale data
      cacheTime: 1000 * 60 * 5, // 5 minutes
      refetchOnWindowFocus: true // Refetch when window gains focus
    }
  );

  // Update profile mutation
  const updateProfileMutation = useMutation(
        (profileData) => profileAPI.updateProfile(profileData),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('user-profile');
        refreshUser();
      },
      onError: (error) => {
        console.error('Error updating profile:', error);
      }
    }
  );

  // Update user data when API data changes
  useEffect(() => {
    if (authUser) {
      // Handle the nested profile structure correctly
      let profile;
      if (profileData && profileData.profile) {
        // If profileData has nested profile, use that
        profile = profileData.profile;
      } else if (profileData) {
        // If profileData is the profile itself
        profile = profileData;
      } else {
        // Fallback to authUser.profile
        profile = authUser.profile || {};
      }

      setUser({
        id: authUser.id,
        username: authUser.username,
        full_name: `${authUser.first_name || ''} ${authUser.last_name || ''}`.trim() || authUser.username,
        avatar: getCoverMediaUrl(profile.profile_picture),
        bio: profile.bio || 'Welcome to my profile!',
        cover: getCoverMediaUrl(profile.cover_media),
        coverMediaType: profile.cover_media_type || 'image',
        stats: statsData || {
          polls_created: profile.posts_count || 0,
          votes_cast: 0,
          communities_joined: 0,
          posts_created: profile.posts_count || 0,
          posts_count: profile.posts_count || 0,
          comments_count: 25,
          likes_given_count: 73,
          followers_count: 12,
          equipment_count: 8
        },
        joined_at: authUser.date_joined || new Date().toISOString()
      });
    }
  }, [authUser, profileData, statsData]);

  // Get user posts and ensure they belong to the current user
  const posts = postsData?.results || [];
  // Pass raw posts to PostRenderer for transformation
  const userPosts = posts;

  const isOwner = true; // Always true since this is the current user's profile


  // Update activity when data changes
  useEffect(() => {
    if (activityData) {
      setActivity(activityData.slice(0, 2));
    }
  }, [activityData]);

  const handleVote = async (pollId, optionIds) => {
    try {
      await pollsAPI.votePoll(pollId, optionIds);
      // Refetch posts to get updated poll data
      await refetchPosts();
    } catch (error) {
      console.error('Error voting on poll:', error);
    }
  };

  // If no user data available, show loading
  if (!user || profileLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">Loading profile...</div>
      </div>
    );
  }

  const optimisticUpdate = (key, newVal, saver) => {
    const prev = user[key];
    setUser(u => ({ ...u, [key]: newVal }));
    setPendingSaves(p => ({ ...p, [key]: true }));
    saver()
      .then(()=> {
        toast.success(key.charAt(0).toUpperCase()+key.slice(1)+' updated');
        queryClient.invalidateQueries('user-profile');
        refreshUser();
      })
      .catch(err => {
        setUser(u => ({ ...u, [key]: prev }));
        toast.error('Failed to update '+key);
        console.error(err);
      })
      .finally(()=> setPendingSaves(p => ({ ...p, [key]: false })));
  };

  const onAvatarChange = (file, previewUrl) => {
    if (!isOwner) return;
    const url = previewUrl || URL.createObjectURL(file);
    optimisticUpdate('avatar', url, () => updateProfileMutation.mutateAsync({ avatar: file }));
  };

  const onCoverChange = (file, previewUrl) => {
    if (!isOwner) return;
    const url = previewUrl || URL.createObjectURL(file);

    // Infer media type from file
    const isVideo = file.type.startsWith('video/');
    const isImage = file.type.startsWith('image/');
    const cover_media_type = isVideo ? 'video' : 'image';

    // Update both cover URL and media type optimistically
    const prevCover = user.cover;
    const prevMediaType = user.coverMediaType;

    setUser(u => ({
      ...u,
      cover: url,
      coverMediaType: cover_media_type
    }));
    setPendingSaves(p => ({ ...p, cover: true }));

    updateProfileMutation.mutateAsync({
      cover_media: file,
      cover_media_type: cover_media_type
    })
    .then(() => {
      toast.success('Cover updated');
      queryClient.invalidateQueries('user-profile');
      refreshUser();
    })
    .catch(err => {
      // Revert both fields on error
      setUser(u => ({
        ...u,
        cover: prevCover,
        coverMediaType: prevMediaType
      }));
      toast.error('Failed to update cover');
      console.error(err);
    })
    .finally(() => setPendingSaves(p => ({ ...p, cover: false })));
  };

  const saveBio = async (newBio) => {
    if (!isOwner) return;
    optimisticUpdate('bio', newBio, () => updateProfileMutation.mutateAsync({ bio: newBio }));
  };

  const updateLinks = (next) => {
    if (!isOwner) return;
    const prev = links;
    setLinks(next);
    toast.promise(new Promise((res, rej)=> setTimeout(()=>{
      // TODO: Implement actual API call to update links
      Math.random()<0.9?res():rej();
    }, 500)), {
      loading: 'Saving links...',
      success: 'Links saved',
      error: 'Failed to save links'
    }).catch(()=> setLinks(prev));
  };

  const loadMore = () => {
    if (loadingMore) return;
    setLoadingMore(true);

    // Load more activity from API
    profileAPI.getUserActivity(null, {
      offset: activity.length,
      limit: 2
    })
    .then((moreActivity) => {
      setActivity(prev => [...prev, ...moreActivity]);
      if (moreActivity.length < 2) {
        setHasMore(false);
      }
    })
    .catch((error) => {
      console.error('Error loading more activity:', error);
    })
    .finally(() => {
      setLoadingMore(false);
    });
  };

  return (
    <FontAwesomeLoader>
      <div className="max-w-7xl mx-auto">
        {/* Cover Section - Normal height */}
        <div className="relative">
          <CoverSection
            coverUrl={user.cover}
            coverMediaType={user.coverMediaType}
            isOwner={isOwner}
            onChange={onCoverChange}
          />
        </div>

        {/* Avatar and User Info - Normal positioning below cover */}
        <div className="relative -mt-14 px-4 sm:px-6">
          <div className="flex items-end gap-4">
            <div className="relative">
              <AvatarUploader
                currentAvatar={user.avatar}
                onAvatarChange={onAvatarChange}
                isOwner={isOwner}
                username={user.username}
                pending={pendingSaves.avatar}
              />
            </div>
            <div className="pb-2 flex-1">
              <div className="flex items-center gap-3">
                <div>
                  <h1 className="text-2xl font-bold text-gray-900">{user.full_name}</h1>
                  <p className="text-sm text-gray-600">@{user.username}</p>
                </div>
                {/* Display FontAwesome badges to the right of username */}
                {authUser?.profile?.id && (
                  <div className="flex items-center">
                    <UserBadgeList userId={authUser.profile.id} maxVisible={5} />
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Tabs and Content */}
        <div className="space-y-6 px-4 sm:px-6 mt-6">
          {/* Tabs */}
          <ProfileTabs
            tabs={[
              {key: 'overview', label: 'Overview'},
              {key: 'posts', label: 'Posts'},
              {key: 'activity', label: 'Activity'},
              {key: 'settings', label: 'Settings'}
            ]}
            active={tab}
            onChange={setTab}
          />

          {/* Tab Content - This is the scrollable area */}
          <div className="overflow-y-auto overflow-x-visible" style={{position: 'relative'}}>
            {tab === 'overview' && (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-8" style={{overflow: 'visible'}}>
                <div className="lg:col-span-1 space-y-6" style={{overflow: 'visible'}}>
                  <div className="bg-white rounded-lg shadow p-6">
                    <h3 className="text-sm font-semibold text-gray-700 mb-1">Bio</h3>
                    <EditableBio bio={user.bio} onSave={saveBio} isOwner={isOwner} pending={pendingSaves.bio} />
                  </div>
                  <UserProfileCard
                    userId={authUser?.profile?.id}
                    userName={user.username}
                    userBio={user.bio}
                    avatar={user.avatar}
                    postsCount={user.stats.posts_count || 0}
                    commentsCount={user.stats.comments_count || 0}
                    pollsCount={user.stats.polls_created || 0}
                    memberSince={user.joined_at}
                    maxVisibleBadges={4}
                    isPrivate={false}  // Own profile - always show stats
                    canViewDetails={true}  // Own profile - always show details
                    context={{ can_view_badges: true }}  // Own profile - always show badges
                    showBio={false}  // Bio is handled separately with EditableBio above
                    showAvatar={true}  // Show avatar for visual consistency
                    showTitle={true}  // Show username for consistency
                  />
                  <div className="bg-white rounded-lg shadow p-6">
                    <LinksBlock links={links} onUpdate={updateLinks} isOwner={isOwner} />
                  </div>
                </div>
                <div className="lg:col-span-2 space-y-6">
                  <div className="bg-white rounded-lg shadow p-6">
                    <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Posts</h2>
                    {postsLoading ? (
                      <div className="text-center py-8">
                        <div className="animate-spin h-6 w-6 border-2 border-blue-500 border-t-transparent rounded-full mx-auto"></div>
                      </div>
                    ) : userPosts.length > 0 ? (
                      <div className="space-y-4">
                        {userPosts.slice(0, 3).map((post, index) => (
                          <PostRenderer
                            key={post.type === 'repost' ?
                              `repost-${post.repost_id || post.id || index}` :
                              `post-${post.id || index}`
                            }
                            post={post}
                            showBorder={false}
                            onVote={handleVote}
                          />
                        ))}
                        {postsData.results.length > 3 && (
                          <button
                            onClick={() => setTab('posts')}
                            className="text-sm text-blue-600 hover:text-blue-800 font-medium"
                          >
                            View all posts ({postsData.results.length})
                          </button>
                        )}
                      </div>
                    ) : (
                      <p className="text-gray-500 text-sm">You haven't posted anything yet.</p>
                    )}
                  </div>
                  <div className="bg-white rounded-lg shadow p-6">
                    <h2 className="text-lg font-semibold text-gray-900 mb-4">Badges & Achievements</h2>
                    <BadgesGrid userId={null} stats={user.stats} joinedAt={user.joined_at} isOwner={true} />
                  </div>
                </div>
              </div>
            )}

            {tab === 'posts' && (
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">All Posts</h2>
                {postsLoading ? (
                  <div className="text-center py-8">
                    <div className="animate-spin h-6 w-6 border-2 border-blue-500 border-t-transparent rounded-full mx-auto"></div>
                  </div>
                ) : userPosts.length > 0 ? (
                  <div className="space-y-6">
                    {userPosts.map((post, index) => (
                      <PostRenderer
                        key={post.type === 'repost' ?
                          `repost-${post.repost_id || post.id || index}` :
                          `post-${post.id || index}`
                        }
                        post={post}
                        onVote={handleVote}
                      />
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <p className="text-gray-500">You haven't posted anything yet.</p>
                  </div>
                )}
              </div>
            )}

            {tab === 'activity' && (
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">All Activity (demo)</h2>
                <ActivityList items={activity} loading={loadingMore} hasMore={hasMore} onLoadMore={loadMore} skeletonCount={4} />
              </div>
            )}

            {tab === 'settings' && (
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-2">Account Settings</h2>
                <SettingsPanel />
              </div>
            )}
          </div>
        </div>
      </div>
    </FontAwesomeLoader>
  );
};

export default Profile;
