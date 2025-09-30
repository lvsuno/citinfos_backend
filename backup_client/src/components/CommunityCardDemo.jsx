import React from 'react';
import CommunityCard from './CommunityCard';

/**
 * CommunityCardDemo - Demonstrates the different variants and options of CommunityCard
 */
const CommunityCardDemo = () => {
  // Sample community data
  const sampleCommunity = {
    id: '1',
    name: 'Tech Enthusiasts',
    slug: 'tech-enthusiasts',
    description: 'A community for discussing the latest in technology, programming, and innovation. Join us to share ideas, get help with projects, and stay updated on tech trends.',
    community_type: 'public',
    cover_media: 'https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=800&h=400&fit=crop',
    cover_media_type: 'image',
    avatar: 'https://images.unsplash.com/photo-1611224923853-80b023f02d71?w=200&h=200&fit=crop',
    membership_count: 15420,
    posts_count: 8934,
    threads_count: 2156,
    user_is_member: true,
    user_role: 'moderator',
    tags: ['technology', 'programming', 'innovation', 'coding', 'ai'],
    category: 'Technology',
    is_featured: true,
    created_at: '2024-01-15T10:30:00Z'
  };

  const privateCommunity = {
    ...sampleCommunity,
    id: '2',
    name: 'VIP Members Only',
    slug: 'vip-members',
    community_type: 'private',
    user_is_member: false,
    user_role: null,
    cover_media: null, // Test fallback gradient
    membership_count: 89,
    posts_count: 234,
    threads_count: 45,
    description: 'An exclusive community for premium members.',
    is_featured: false
  };

  const restrictedCommunity = {
    ...sampleCommunity,
    id: '3',
    name: 'Local Developers Network',
    slug: 'local-dev-network',
    community_type: 'restricted',
    user_is_member: true,
    user_role: 'owner',
    membership_count: 456,
    posts_count: 1234,
    threads_count: 234,
    description: 'For developers in the San Francisco Bay Area.',
    tags: ['local', 'networking', 'developers']
  };

  const handleJoin = (slug) => {
    console.log('Joining community:', slug);
  };

  const handleLeave = (slug) => {
    console.log('Leaving community:', slug);
  };

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-8">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">CommunityCard Component Demo</h1>
        <p className="text-gray-600">
          Demonstrating the various configurations and variants of the CommunityCard component
        </p>
      </div>

      {/* Grid Variant */}
      <section>
        <h2 className="text-2xl font-semibold text-gray-800 mb-4">Grid Variant (Default)</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <CommunityCard
            community={sampleCommunity}
            options={{
              variant: 'grid',
              showStats: true,
              showDescription: true,
              showTags: true,
              showActions: true,
              showMembershipBadge: true
            }}
            onJoin={handleJoin}
            onLeave={handleLeave}
          />
          <CommunityCard
            community={privateCommunity}
            options={{
              variant: 'grid',
              showStats: true,
              showDescription: true,
              showTags: true,
              showActions: true,
              showMembershipBadge: true
            }}
            onJoin={handleJoin}
            onLeave={handleLeave}
          />
          <CommunityCard
            community={restrictedCommunity}
            options={{
              variant: 'grid',
              showStats: true,
              showDescription: true,
              showTags: true,
              showActions: true,
              showMembershipBadge: true
            }}
            onJoin={handleJoin}
            onLeave={handleLeave}
          />
        </div>
      </section>

      {/* List Variant */}
      <section>
        <h2 className="text-2xl font-semibold text-gray-800 mb-4">List Variant</h2>
        <div className="space-y-4">
          <CommunityCard
            community={sampleCommunity}
            options={{
              variant: 'list',
              showStats: true,
              showDescription: true,
              showTags: true,
              showActions: true,
              showMembershipBadge: true
            }}
            onJoin={handleJoin}
            onLeave={handleLeave}
          />
          <CommunityCard
            community={privateCommunity}
            options={{
              variant: 'list',
              showStats: true,
              showDescription: true,
              showTags: true,
              showActions: true,
              showMembershipBadge: true
            }}
            onJoin={handleJoin}
            onLeave={handleLeave}
          />
        </div>
      </section>

      {/* Compact Variant */}
      <section>
        <h2 className="text-2xl font-semibold text-gray-800 mb-4">Compact Variant</h2>
        <div className="space-y-2">
          <CommunityCard
            community={sampleCommunity}
            options={{
              variant: 'compact',
              showStats: true,
              showDescription: false,
              showTags: false,
              showActions: false,
              showMembershipBadge: true
            }}
            onJoin={handleJoin}
            onLeave={handleLeave}
          />
          <CommunityCard
            community={privateCommunity}
            options={{
              variant: 'compact',
              showStats: true,
              showDescription: false,
              showTags: false,
              showActions: false,
              showMembershipBadge: true
            }}
            onJoin={handleJoin}
            onLeave={handleLeave}
          />
          <CommunityCard
            community={restrictedCommunity}
            options={{
              variant: 'compact',
              showStats: true,
              showDescription: false,
              showTags: false,
              showActions: false,
              showMembershipBadge: true
            }}
            onJoin={handleJoin}
            onLeave={handleLeave}
          />
        </div>
      </section>

      {/* Customization Examples */}
      <section>
        <h2 className="text-2xl font-semibold text-gray-800 mb-4">Customization Examples</h2>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Minimal card */}
          <div>
            <h3 className="text-lg font-medium text-gray-700 mb-3">Minimal Card (Stats Only)</h3>
            <CommunityCard
              community={sampleCommunity}
              options={{
                variant: 'grid',
                showStats: true,
                showDescription: false,
                showTags: false,
                showActions: false,
                showMembershipBadge: false
              }}
            />
          </div>

          {/* Clickable card */}
          <div>
            <h3 className="text-lg font-medium text-gray-700 mb-3">Clickable Card</h3>
            <CommunityCard
              community={sampleCommunity}
              options={{
                variant: 'grid',
                showStats: true,
                showDescription: true,
                showTags: false,
                showActions: false,
                showMembershipBadge: true,
                clickable: true
              }}
            />
          </div>
        </div>
      </section>

      {/* Usage Documentation */}
      <section className="bg-gray-50 p-6 rounded-lg">
        <h2 className="text-2xl font-semibold text-gray-800 mb-4">Usage Documentation</h2>
        <div className="prose max-w-none">
          <h3>Props</h3>
          <ul>
            <li><strong>community</strong>: Community data object with id, name, slug, description, etc.</li>
            <li><strong>options</strong>: Configuration object for display options</li>
            <li><strong>onJoin</strong>: Callback function when join button is clicked</li>
            <li><strong>onLeave</strong>: Callback function when leave button is clicked</li>
            <li><strong>isLoading</strong>: Boolean to show loading state</li>
            <li><strong>className</strong>: Additional CSS classes</li>
          </ul>

          <h3>Options</h3>
          <ul>
            <li><strong>variant</strong>: 'grid' | 'list' | 'compact'</li>
            <li><strong>showStats</strong>: Show member/post counts</li>
            <li><strong>showDescription</strong>: Show community description</li>
            <li><strong>showTags</strong>: Show community tags</li>
            <li><strong>showActions</strong>: Show join/visit buttons</li>
            <li><strong>showMembershipBadge</strong>: Show user's role badge</li>
            <li><strong>clickable</strong>: Make entire card clickable</li>
          </ul>

          <h3>Example Usage</h3>
          <pre className="bg-gray-100 p-4 rounded text-sm overflow-x-auto">
{`<CommunityCard
  community={communityData}
  options={{
    variant: 'grid',
    showStats: true,
    showDescription: true,
    showTags: true,
    showActions: true,
    showMembershipBadge: true,
    clickable: false
  }}
  onJoin={(slug) => handleJoin(slug)}
  isLoading={isJoining}
/>`}
          </pre>
        </div>
      </section>
    </div>
  );
};

export default CommunityCardDemo;
