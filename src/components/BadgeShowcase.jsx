import React, { useState } from 'react';
import {
  FaCrown, FaUserPlus, FaComments, FaTrophy, FaCalendarAlt, FaHeart, FaShareAlt,
  FaGem, FaStar, FaFire, FaBolt, FaRocket, FaShieldAlt, FaMedal, FaTools, FaUsers
} from 'react-icons/fa';
import {
  UserPlusIcon, ChatBubbleLeftRightIcon, TrophyIcon, CalendarIcon,
  HeartIcon, ShareIcon, SparklesIcon, StarIcon, FireIcon, BoltIcon,
  RocketLaunchIcon, ShieldCheckIcon, CheckBadgeIcon, WrenchScrewdriverIcon, UsersIcon
} from '@heroicons/react/24/solid';
import {
  Crown, UserPlus, MessageCircle, Trophy, Calendar, Heart, Share2,
  Sparkles, Star, Flame, Zap, Rocket, Shield, Award, Wrench, Users
} from 'lucide-react';
import {
  IconCrown, IconUserPlus, IconMessageCircle, IconTrophyFilled, IconCalendar,
  IconHeart, IconShare, IconSparkles, IconStar, IconFlame, IconBolt,
  IconRocket, IconShield, IconAward, IconTool, IconUsers
} from '@tabler/icons-react';

const BadgeShowcase = () => {
  const [activeTab, setActiveTab] = useState('react-icons');

  // Badge configuration with all 49 badges exactly matching .env thresholds
  const badges = [
    // 1. Early Adopter
    { code: 'early_adopter', name: 'Early Adopter', category: 'Early Adopter', tier: 'Gold', description: 'Be among the first 1000 users' },

    // 2-4. Post Achievement Badges
    { code: 'posts_bronze', name: 'Content Creator (Bronze)', category: 'Content Creation', tier: 'Bronze', description: 'Create 10 posts' },
    { code: 'posts_silver', name: 'Content Creator (Silver)', category: 'Content Creation', tier: 'Silver', description: 'Create 50 posts' },
    { code: 'posts_gold', name: 'Content Creator (Gold)', category: 'Content Creation', tier: 'Gold', description: 'Create 200 posts' },

    // 5-7. Poll Creation Badges
    { code: 'polls_bronze', name: 'Poll Master (Bronze)', category: 'Content Creation', tier: 'Bronze', description: 'Create 5 polls' },
    { code: 'polls_silver', name: 'Poll Master (Silver)', category: 'Content Creation', tier: 'Silver', description: 'Create 25 polls' },
    { code: 'polls_gold', name: 'Poll Master (Gold)', category: 'Content Creation', tier: 'Gold', description: 'Create 100 polls' },

    // 8-10. Poll Voting Badges
    { code: 'poll_voter_bronze', name: 'Poll Participant (Bronze)', category: 'Engagement', tier: 'Bronze', description: 'Vote in 20 polls' },
    { code: 'poll_voter_silver', name: 'Poll Participant (Silver)', category: 'Engagement', tier: 'Silver', description: 'Vote in 100 polls' },
    { code: 'poll_voter_gold', name: 'Poll Participant (Gold)', category: 'Engagement', tier: 'Gold', description: 'Vote in 500 polls' },

    // 11-13. Like Giving Badges
    { code: 'likes_giver_bronze', name: 'Like Enthusiast (Bronze)', category: 'Social', tier: 'Bronze', description: 'Give 50 likes' },
    { code: 'likes_giver_silver', name: 'Like Enthusiast (Silver)', category: 'Social', tier: 'Silver', description: 'Give 250 likes' },
    { code: 'likes_giver_gold', name: 'Like Enthusiast (Gold)', category: 'Social', tier: 'Gold', description: 'Give 1000 likes' },

    // 14-16. Comment Badges
    { code: 'commenter_bronze', name: 'Community Helper (Bronze)', category: 'Engagement', tier: 'Bronze', description: 'Make 20 helpful comments' },
    { code: 'commenter_silver', name: 'Community Helper (Silver)', category: 'Engagement', tier: 'Silver', description: 'Make 100 helpful comments' },
    { code: 'commenter_gold', name: 'Community Helper (Gold)', category: 'Engagement', tier: 'Gold', description: 'Make 400 helpful comments' },

    // 17-19. Follower Achievement Badges
    { code: 'popular_bronze', name: 'Popular (Bronze)', category: 'Social', tier: 'Bronze', description: 'Gain 50 followers' },
    { code: 'popular_silver', name: 'Popular (Silver)', category: 'Social', tier: 'Silver', description: 'Gain 250 followers' },
    { code: 'popular_gold', name: 'Popular (Gold)', category: 'Social', tier: 'Gold', description: 'Gain 1000 followers' },

    // 20-22. Social Butterfly Badges
    { code: 'social_bronze', name: 'Social Butterfly (Bronze)', category: 'Social', tier: 'Bronze', description: 'Follow 25 users' },
    { code: 'social_silver', name: 'Social Butterfly (Silver)', category: 'Social', tier: 'Silver', description: 'Follow 100 users' },
    { code: 'social_gold', name: 'Social Butterfly (Gold)', category: 'Social', tier: 'Gold', description: 'Follow 300 users' },

    // 23-25. Equipment Expert Badges
    { code: 'equipment_bronze', name: 'Equipment Expert (Bronze)', category: 'Equipment', tier: 'Bronze', description: 'Add 3 equipment items' },
    { code: 'equipment_silver', name: 'Equipment Expert (Silver)', category: 'Equipment', tier: 'Silver', description: 'Add 15 equipment items' },
    { code: 'equipment_gold', name: 'Equipment Expert (Gold)', category: 'Equipment', tier: 'Gold', description: 'Add 60 equipment items' },

    // 26-28. Quality Comment Badges
    { code: 'quality_commenter_bronze', name: 'Quality Commenter (Bronze)', category: 'Quality', tier: 'Bronze', description: 'Receive 1 best comment' },
    { code: 'quality_commenter_silver', name: 'Quality Commenter (Silver)', category: 'Quality', tier: 'Silver', description: 'Receive 5 best comments' },
    { code: 'quality_commenter_gold', name: 'Quality Commenter (Gold)', category: 'Quality', tier: 'Gold', description: 'Receive 20 best comments' },

    // 29-31. High Engagement Badges
    { code: 'high_engagement_bronze', name: 'High Engagement (Bronze)', category: 'Activity', tier: 'Bronze', description: 'Maintain 25% engagement score' },
    { code: 'high_engagement_silver', name: 'High Engagement (Silver)', category: 'Activity', tier: 'Silver', description: 'Maintain 50% engagement score' },
    { code: 'high_engagement_gold', name: 'High Engagement (Gold)', category: 'Activity', tier: 'Gold', description: 'Maintain 75% engagement score' },

    // 32-34. Repost Badges
    { code: 'reposter_bronze', name: 'Share Master (Bronze)', category: 'Sharing', tier: 'Bronze', description: 'Make 5 reposts' },
    { code: 'reposter_silver', name: 'Share Master (Silver)', category: 'Sharing', tier: 'Silver', description: 'Make 25 reposts' },
    { code: 'reposter_gold', name: 'Share Master (Gold)', category: 'Sharing', tier: 'Gold', description: 'Make 100 reposts' },

    // 35-37. Share Sender Badges
    { code: 'share_sender_bronze', name: 'Content Sharer (Bronze)', category: 'Sharing', tier: 'Bronze', description: 'Send 5 shares' },
    { code: 'share_sender_silver', name: 'Content Sharer (Silver)', category: 'Sharing', tier: 'Silver', description: 'Send 30 shares' },
    { code: 'share_sender_gold', name: 'Content Sharer (Gold)', category: 'Sharing', tier: 'Gold', description: 'Send 120 shares' },

    // 38-40. Share Magnet Badges
    { code: 'share_magnet_bronze', name: 'Share Magnet (Bronze)', category: 'Popularity', tier: 'Bronze', description: 'Receive 5 shares' },
    { code: 'share_magnet_silver', name: 'Share Magnet (Silver)', category: 'Popularity', tier: 'Silver', description: 'Receive 30 shares' },
    { code: 'share_magnet_gold', name: 'Share Magnet (Gold)', category: 'Popularity', tier: 'Gold', description: 'Receive 120 shares' },

    // 41-43. Community Member Badges
    { code: 'community_member_bronze', name: 'Community Member (Bronze)', category: 'Community', tier: 'Bronze', description: 'Join 3 communities' },
    { code: 'community_member_silver', name: 'Community Member (Silver)', category: 'Community', tier: 'Silver', description: 'Join 10 communities' },
    { code: 'community_member_gold', name: 'Community Member (Gold)', category: 'Community', tier: 'Gold', description: 'Join 25 communities' },

    // 44-46. Quality Content Badges
    { code: 'quality_content_bronze', name: 'Quality Creator (Bronze)', category: 'Quality', tier: 'Bronze', description: 'Maintain 20% content quality score' },
    { code: 'quality_content_silver', name: 'Quality Creator (Silver)', category: 'Quality', tier: 'Silver', description: 'Maintain 45% content quality score' },
    { code: 'quality_content_gold', name: 'Quality Creator (Gold)', category: 'Quality', tier: 'Gold', description: 'Maintain 70% content quality score' },

    // 47-49. Active User Badges
    { code: 'active_user_bronze', name: 'Active User (Bronze)', category: 'Activity', tier: 'Bronze', description: 'Maintain 20% interaction frequency' },
    { code: 'active_user_silver', name: 'Active User (Silver)', category: 'Activity', tier: 'Silver', description: 'Maintain 50% interaction frequency' },
    { code: 'active_user_gold', name: 'Active User (Gold)', category: 'Activity', tier: 'Gold', description: 'Maintain 80% interaction frequency' }
  ];

  // Icon mappings for each category
  const iconMappings = {
    'react-icons': {
      'Early Adopter': FaCrown,
      'Content Creation': FaUserPlus,
      'Engagement': FaComments,
      'Social': FaHeart,
      'Equipment': FaTools,
      'Quality': FaTrophy,
      'Activity': FaBolt,
      'Sharing': FaShareAlt,
      'Popularity': FaStar,
      'Community': FaUsers
    },
    'heroicons': {
      'Early Adopter': TrophyIcon,
      'Content Creation': UserPlusIcon,
      'Engagement': ChatBubbleLeftRightIcon,
      'Social': HeartIcon,
      'Equipment': WrenchScrewdriverIcon,
      'Quality': TrophyIcon,
      'Activity': BoltIcon,
      'Sharing': ShareIcon,
      'Popularity': StarIcon,
      'Community': UsersIcon
    },
    'lucide': {
      'Early Adopter': Crown,
      'Content Creation': UserPlus,
      'Engagement': MessageCircle,
      'Social': Heart,
      'Equipment': Wrench,
      'Quality': Trophy,
      'Activity': Zap,
      'Sharing': Share2,
      'Popularity': Star,
      'Community': Users
    },
    'tabler': {
      'Early Adopter': IconCrown,
      'Content Creation': IconUserPlus,
      'Engagement': IconMessageCircle,
      'Social': IconHeart,
      'Equipment': IconTool,
      'Quality': IconTrophyFilled,
      'Activity': IconBolt,
      'Sharing': IconShare,
      'Popularity': IconStar,
      'Community': IconUsers
    }
  };

  // Tier colors
  const tierColors = {
    Bronze: '#CD7F32',
    Silver: '#C0C0C0',
    Gold: '#FFD700'
  };

  // Get unique categories for organization
  const categories = [...new Set(badges.map(badge => badge.category))];

  const renderIcon = (category, library) => {
    const IconComponent = iconMappings[library][category];
    if (!IconComponent) return null;

    return <IconComponent className="w-6 h-6" />;
  };

  const renderBadgeCard = (badge, library) => (
    <div key={`${badge.code}-${library}`} className="bg-white rounded-lg shadow-md p-4 border-l-4"
         style={{ borderLeftColor: tierColors[badge.tier] }}>
      <div className="flex items-center mb-2">
        <div className="mr-3" style={{ color: tierColors[badge.tier] }}>
          {renderIcon(badge.category, library)}
        </div>
        <div>
          <h3 className="font-semibold text-gray-800">{badge.name}</h3>
          <span className="inline-block px-2 py-1 text-xs rounded-full text-white"
                style={{ backgroundColor: tierColors[badge.tier] }}>
            {badge.tier}
          </span>
        </div>
      </div>
      <p className="text-gray-600 text-sm mb-2">{badge.description}</p>
      <div className="text-xs text-gray-500">
        Category: {badge.category} | Code: {badge.code}
      </div>
    </div>
  );

  const renderBadgesByCategory = (library) => {
    return categories.map(category => (
      <div key={category} className="mb-8">
        <h2 className="text-xl font-bold mb-4 text-gray-800 border-b pb-2">{category}</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {badges
            .filter(badge => badge.category === category)
            .map(badge => renderBadgeCard(badge, library))
          }
        </div>
      </div>
    ));
  };

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6 text-center text-gray-800">
        Badge System Showcase - All 49 Badges
      </h1>

      <div className="mb-6 text-center text-gray-600">
        <p>Displaying all {badges.length} badges that match the .env threshold configuration</p>
      </div>

      {/* Tab Navigation */}
      <div className="flex justify-center mb-8">
        <div className="bg-gray-100 rounded-lg p-1">
          {['react-icons', 'heroicons', 'lucide', 'tabler'].map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 rounded-md mr-1 last:mr-0 transition-colors ${
                activeTab === tab
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              {tab === 'react-icons' && 'React Icons'}
              {tab === 'heroicons' && 'Heroicons'}
              {tab === 'lucide' && 'Lucide React'}
              {tab === 'tabler' && 'Tabler Icons'}
            </button>
          ))}
        </div>
      </div>

      {/* Badge Display */}
      <div className="max-w-7xl mx-auto">
        {renderBadgesByCategory(activeTab)}
      </div>

      {/* Summary */}
      <div className="mt-8 p-4 bg-gray-50 rounded-lg">
        <h3 className="font-semibold mb-2">Badge Summary:</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <span className="font-medium">Total Badges:</span> {badges.length}
          </div>
          <div>
            <span className="font-medium">Categories:</span> {categories.length}
          </div>
          <div>
            <span className="font-medium">Bronze:</span> {badges.filter(b => b.tier === 'Bronze').length}
          </div>
          <div>
            <span className="font-medium">Silver:</span> {badges.filter(b => b.tier === 'Silver').length}
          </div>
          <div>
            <span className="font-medium">Gold:</span> {badges.filter(b => b.tier === 'Gold').length}
          </div>
        </div>
      </div>
    </div>
  );
};

export default BadgeShowcase;
