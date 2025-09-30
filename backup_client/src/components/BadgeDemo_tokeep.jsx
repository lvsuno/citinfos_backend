import React from 'react';
import TinyBadgeList from './TinyBadgeList';
import UserBadgeList from './UserBadgeList';
import BadgeIcon from './BadgeIcon';
import UserProfileCard from './UserProfileCard';

const BadgeDemo = () => {
  // Sample user ID that has badges (replace with actual user ID from your system)
  const sampleUserId = '8e25a402-45a8-4cad-b3de-4f371d64d720';

  // Sample badges for manual examples (matching the HTML preview structure)
  const sampleBadges = [
    { id: 1, name: 'Rocket Launcher', tier: 'Gold', icon: 'fas fa-rocket', points: 100 },
    { id: 2, name: 'Comment King', tier: 'Silver', icon: 'fas fa-comments', points: 75 },
    { id: 3, name: 'Equipment Master', tier: 'Bronze', icon: 'fas fa-wrench', points: 50 },
    { id: 4, name: 'Top Contributor', tier: 'Gold', icon: 'fas fa-star', points: 150 },
    { id: 5, name: 'Helper', tier: 'Bronze', icon: 'fas fa-hands-helping', points: 25 },
    { id: 6, name: 'Verified Pro', tier: 'Silver', icon: 'fas fa-check-circle', points: 80 },
  ];

  return (
    <div className="badge-demo">
      {/* Header matching HTML preview */}
      <div className="demo-header">
        <h1>🏆 Badge System Showcase</h1>
        <p>Comprehensive demonstration of our badge components and implementations</p>
      </div>

      {/* Badge Categories Section - matching HTML structure */}
      <div className="badge-categories">
        <h2>🎖️ Badge Categories & Tiers</h2>

        {/* Gold Tier */}
        <div className="tier-section">
          <h3 className="tier-title">🥇 Gold Tier Badges</h3>
          <div className="badge-grid">
            {sampleBadges.filter(b => b.tier === 'Gold').map(badge => (
              <div key={badge.id} className="badge-card">
                <BadgeIcon
                  name={badge.name}
                  tier={badge.tier}
                  icon={badge.icon}
                  points={badge.points}
                  showTooltip={true}
                />
                <div className="badge-info">
                  <div className="badge-name">{badge.name}</div>
                  <div className="badge-tier">{badge.tier}</div>
                  <div className="badge-points">{badge.points} points</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Silver Tier */}
        <div className="tier-section">
          <h3 className="tier-title">🥈 Silver Tier Badges</h3>
          <div className="badge-grid">
            {sampleBadges.filter(b => b.tier === 'Silver').map(badge => (
              <div key={badge.id} className="badge-card">
                <BadgeIcon
                  name={badge.name}
                  tier={badge.tier}
                  icon={badge.icon}
                  points={badge.points}
                  showTooltip={true}
                />
                <div className="badge-info">
                  <div className="badge-name">{badge.name}</div>
                  <div className="badge-tier">{badge.tier}</div>
                  <div className="badge-points">{badge.points} points</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Bronze Tier */}
        <div className="tier-section">
          <h3 className="tier-title">🥉 Bronze Tier Badges</h3>
          <div className="badge-grid">
            {sampleBadges.filter(b => b.tier === 'Bronze').map(badge => (
              <div key={badge.id} className="badge-card">
                <BadgeIcon
                  name={badge.name}
                  tier={badge.tier}
                  icon={badge.icon}
                  points={badge.points}
                  showTooltip={true}
                />
                <div className="badge-info">
                  <div className="badge-name">{badge.name}</div>
                  <div className="badge-tier">{badge.tier}</div>
                  <div className="badge-points">{badge.points} points</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* TinyBadgeList Examples */}
      <div className="component-section">
        <h2>🔸 TinyBadgeList Component (12px icons)</h2>
        <p>Perfect for inline display next to usernames in posts and comments</p>

        <div className="example-grid">
          <div className="example-card">
            <h4>Default (max 3 badges)</h4>
            <div className="user-example">
              <span className="username">john_doe</span>
              <TinyBadgeList userId={sampleUserId} maxVisible={3} />
            </div>
          </div>

          <div className="example-card">
            <h4>Compact (max 2 badges)</h4>
            <div className="user-example">
              <span className="username">jane_smith</span>
              <TinyBadgeList userId={sampleUserId} maxVisible={2} />
            </div>
          </div>

          <div className="example-card">
            <h4>Extended (max 5 badges)</h4>
            <div className="user-example">
              <span className="username">alex_wilson</span>
              <TinyBadgeList userId={sampleUserId} maxVisible={5} />
            </div>
          </div>
        </div>
      </div>

      {/* UserBadgeList Examples */}
      <div className="component-section">
        <h2>🔹 UserBadgeList Component (24px icons)</h2>
        <p>Standard size for profile pages and detailed user views</p>

        <div className="example-grid">
          <div className="example-card">
            <h4>Profile Display (max 3)</h4>
            <div className="profile-example">
              <h5>User Profile</h5>
              <UserBadgeList userId={sampleUserId} maxVisible={3} />
            </div>
          </div>

          <div className="example-card">
            <h4>Compact Profile (max 2)</h4>
            <div className="profile-example">
              <h5>Mini Profile</h5>
              <UserBadgeList userId={sampleUserId} maxVisible={2} />
            </div>
          </div>

          <div className="example-card">
            <h4>Full Display (max 6)</h4>
            <div className="profile-example">
              <h5>Achievement Gallery</h5>
              <UserBadgeList userId={sampleUserId} maxVisible={6} />
            </div>
          </div>
        </div>
      </div>

      {/* Different Size Examples */}
      <div className="component-section">
        <h2>📏 Badge Size Variations</h2>
        <p>Examples with different icon sizes from the HTML preview</p>

        <div className="size-examples">
          <div className="size-example">
            <h4>12px Icons (Tiny)</h4>
            <div className="badge-row">
              <TinyBadgeList userId={sampleUserId} maxVisible={4} />
            </div>
          </div>

          <div className="size-example">
            <h4>24px Icons (Standard)</h4>
            <div className="badge-row">
              <UserBadgeList userId={sampleUserId} maxVisible={4} />
            </div>
          </div>

          <div className="size-example">
            <h4>Individual 24px Badges</h4>
            <div className="badge-row">
              {sampleBadges.slice(0, 4).map(badge => (
                <BadgeIcon
                  key={badge.id}
                  name={badge.name}
                  tier={badge.tier}
                  icon={badge.icon}
                  points={badge.points}
                  showTooltip={true}
                />
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* UserProfileCard Component Section */}
      <div className="component-section">
        <h2>👤 UserProfileCard Component</h2>
        <p>Reusable profile card component with customizable user information, badges, and statistics including posts, comments, and polls with beautiful icons</p>

        <div className="example-grid">
          <div className="example-card">
            <h4>Basic Profile Card</h4>
            <UserProfileCard
              userId={sampleUserId}
              userName="JohnDoe123"
              userBio="Love working with heavy machinery and sharing knowledge with the community."
              postsCount={45}
              commentsCount={123}
              pollsCount={18}
              memberSince="2023-06-20"
              maxVisibleBadges={3}
            />
          </div>

          <div className="example-card">
            <h4>Profile with Custom Avatar</h4>
            <UserProfileCard
              userId={sampleUserId}
              userName="MachineExpert"
              userBio="Industrial engineer specializing in automated systems and predictive maintenance."
              avatar="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='48' height='48' viewBox='0 0 48 48'%3E%3Ccircle cx='24' cy='24' r='24' fill='%2310b981'/%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' font-size='18' fill='white'%3E🔧%3C/text%3E%3C/svg%3E"
              postsCount={287}
              commentsCount={654}
              pollsCount={92}
              memberSince="2022-02-14"
              maxVisibleBadges={4}
            />
          </div>

          <div className="example-card">
            <h4>Minimal Profile Card</h4>
            <UserProfileCard
              userId={sampleUserId}
              userName="QuickLearner"
              postsCount={8}
              commentsCount={25}
              pollsCount={2}
              memberSince="2024-07-01"
              maxVisibleBadges={2}
            />
          </div>
        </div>
      </div>

      {/* Real-world Usage Examples */}
      <div className="component-section">
        <h2>💼 Real-world Usage Examples</h2>
        <p>How badges appear in actual application contexts</p>

        <div className="usage-examples">
          <div className="usage-card">
            <h4>📝 Post Header</h4>
            <div className="post-example">
              <div className="post-header">
                <img src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='32' height='32' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' fill='%23ddd'/%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' font-size='12' fill='%23999'%3E32x32%3C/text%3E%3C/svg%3E" alt="Avatar" className="avatar" />
                <div className="post-info">
                  <div className="author-line">
                    <span className="author-name">equipment_guru</span>
                    <TinyBadgeList userId={sampleUserId} maxVisible={3} />
                  </div>
                  <div className="post-meta">Posted 2 hours ago • Equipment Discussion</div>
                </div>
              </div>
            </div>
          </div>

          <div className="usage-card">
            <h4>👤 User Profile Card</h4>
            <UserProfileCard
              userId={sampleUserId}
              userName="Professional User"
              userBio="Equipment specialist with 5+ years of experience in industrial machinery and safety protocols."
              avatar="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='48' height='48' viewBox='0 0 48 48'%3E%3Crect width='48' height='48' fill='%23ddd'/%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' font-size='14' fill='%23999'%3E48x48%3C/text%3E%3C/svg%3E"
              postsCount={125}
              commentsCount={89}
              pollsCount={34}
              memberSince="2023-03-15"
              maxVisibleBadges={4}
            />
          </div>

          <div className="usage-card">
            <h4>👨‍💻 New User Card</h4>
            <UserProfileCard
              userId={sampleUserId}
              userName="TechNewbie2024"
              userBio="Just started my journey in equipment management. Eager to learn from the community!"
              postsCount={3}
              commentsCount={12}
              pollsCount={1}
              memberSince="2024-08-01"
              maxVisibleBadges={2}
            />
          </div>

          <div className="usage-card">
            <h4>🏆 Expert User Card</h4>
            <UserProfileCard
              userId={sampleUserId}
              userName="EquipmentMaster"
              userBio="Senior consultant with 15+ years in heavy machinery. Author of 'Equipment Safety Guidelines 2024'."
              avatar="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='48' height='48' viewBox='0 0 48 48'%3E%3Ccircle cx='24' cy='24' r='24' fill='%23f59e0b'/%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' font-size='18' fill='white'%3E⭐%3C/text%3E%3C/svg%3E"
              postsCount={1250}
              commentsCount={3400}
              pollsCount={287}
              memberSince="2020-01-10"
              maxVisibleBadges={6}
            />
          </div>

          <div className="usage-card">
            <h4>💬 Comment Section</h4>
            <div className="comment-example">
              <div className="comment-header">
                <img src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='28' height='28' viewBox='0 0 28 28'%3E%3Crect width='28' height='28' fill='%23ddd'/%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' font-size='10' fill='%23999'%3E28x28%3C/text%3E%3C/svg%3E" alt="Avatar" className="comment-avatar" />
                <div className="comment-author">
                  <span className="commenter-name">tech_expert</span>
                  <TinyBadgeList userId={sampleUserId} maxVisible={2} />
                </div>
                <span className="comment-time">• 45 min ago</span>
              </div>
              <div className="comment-content">
                Great question! I've been using similar equipment for years...
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* CSS Styles matching the HTML preview */}
      <style jsx>{`
        .badge-demo {
          min-height: 100vh;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          padding: 40px 20px;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
        }

        .demo-header {
          text-align: center;
          margin-bottom: 60px;
          color: white;
        }

        .demo-header h1 {
          font-size: 3rem;
          margin-bottom: 15px;
          text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }

        .demo-header p {
          font-size: 1.3rem;
          opacity: 0.9;
          max-width: 600px;
          margin: 0 auto;
        }

        .badge-categories {
          background: white;
          border-radius: 20px;
          padding: 40px;
          margin-bottom: 40px;
          box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }

        .badge-categories h2 {
          color: #2d3748;
          font-size: 2rem;
          margin-bottom: 30px;
          text-align: center;
        }

        .tier-section {
          margin-bottom: 40px;
        }

        .tier-title {
          color: #4a5568;
          font-size: 1.5rem;
          margin-bottom: 20px;
          padding-left: 10px;
          border-left: 4px solid #667eea;
        }

        .badge-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
          gap: 20px;
          margin-bottom: 30px;
        }

        .badge-card {
          background: #f8f9fa;
          border: 2px solid #e9ecef;
          border-radius: 15px;
          padding: 20px;
          text-align: center;
          transition: all 0.3s ease;
          cursor: pointer;
        }

        .badge-card:hover {
          transform: translateY(-5px);
          box-shadow: 0 10px 25px rgba(0,0,0,0.15);
          border-color: #667eea;
        }

        .badge-info {
          margin-top: 15px;
        }

        .badge-name {
          font-weight: 600;
          color: #2d3748;
          font-size: 14px;
          margin-bottom: 5px;
        }

        .badge-tier {
          font-weight: 500;
          font-size: 12px;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          margin-bottom: 3px;
        }

        .badge-points {
          font-size: 11px;
          color: #718096;
        }

        .component-section {
          background: white;
          border-radius: 20px;
          padding: 40px;
          margin-bottom: 40px;
          box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }

        .component-section h2 {
          color: #2d3748;
          font-size: 1.8rem;
          margin-bottom: 10px;
        }

        .component-section p {
          color: #718096;
          font-size: 1rem;
          margin-bottom: 30px;
        }

        .example-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
          gap: 25px;
        }

        .example-card {
          background: #f7fafc;
          border: 2px solid #e2e8f0;
          border-radius: 15px;
          padding: 25px;
          transition: all 0.3s ease;
        }

        .example-card:hover {
          transform: translateY(-3px);
          box-shadow: 0 8px 20px rgba(0,0,0,0.1);
          border-color: #cbd5e1;
        }

        .example-card h4 {
          color: #2d3748;
          margin-bottom: 15px;
          font-size: 1.1rem;
        }

        .user-example {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 15px;
          background: white;
          border-radius: 10px;
          border: 1px solid #e2e8f0;
        }

        .username {
          font-weight: 600;
          color: #2d3748;
          font-size: 14px;
        }

        .profile-example {
          background: white;
          border-radius: 10px;
          padding: 20px;
          border: 1px solid #e2e8f0;
        }

        .profile-example h5 {
          color: #2d3748;
          margin-bottom: 12px;
          font-size: 1rem;
        }

        .size-examples {
          display: flex;
          flex-direction: column;
          gap: 25px;
        }

        .size-example {
          background: #f7fafc;
          border-radius: 15px;
          padding: 25px;
          border: 2px solid #e2e8f0;
        }

        .size-example h4 {
          color: #2d3748;
          margin-bottom: 15px;
          font-size: 1.1rem;
        }

        .badge-row {
          display: flex;
          gap: 15px;
          flex-wrap: wrap;
          align-items: center;
          padding: 15px;
          background: white;
          border-radius: 10px;
          border: 1px solid #e2e8f0;
        }

        .usage-examples {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
          gap: 30px;
        }

        .usage-card {
          background: #f7fafc;
          border-radius: 15px;
          padding: 25px;
          border: 2px solid #e2e8f0;
          transition: all 0.3s ease;
        }

        .usage-card:hover {
          transform: translateY(-3px);
          box-shadow: 0 8px 20px rgba(0,0,0,0.1);
        }

        .usage-card h4 {
          color: #2d3748;
          margin-bottom: 20px;
          font-size: 1.1rem;
        }

        .post-example,
        .user-card-example,
        .comment-example {
          background: white;
          border-radius: 12px;
          padding: 20px;
          border: 1px solid #e2e8f0;
        }

        .post-header {
          display: flex;
          gap: 12px;
          align-items: flex-start;
        }

        .avatar {
          width: 32px;
          height: 32px;
          border-radius: 50%;
          object-fit: cover;
        }

        .post-info {
          flex: 1;
        }

        .author-line {
          display: flex;
          align-items: center;
          gap: 10px;
          margin-bottom: 5px;
        }

        .author-name {
          font-weight: 600;
          color: #2d3748;
          font-size: 14px;
        }

        .post-meta {
          font-size: 12px;
          color: #718096;
        }

        .card-header {
          display: flex;
          gap: 15px;
          align-items: flex-start;
        }

        .card-avatar {
          width: 48px;
          height: 48px;
          border-radius: 50%;
          object-fit: cover;
        }

        .card-info {
          flex: 1;
        }

        .card-name {
          color: #2d3748;
          margin-bottom: 10px;
          font-size: 1.1rem;
          font-weight: 600;
        }

        .card-stats {
          font-size: 12px;
          color: #718096;
          margin-top: 10px;
        }

        .comment-header {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 12px;
        }

        .comment-avatar {
          width: 28px;
          height: 28px;
          border-radius: 50%;
          object-fit: cover;
        }

        .commenter-name {
          font-weight: 600;
          color: #2d3748;
          font-size: 13px;
        }

        .comment-time {
          color: #718096;
          font-size: 12px;
        }

        .comment-content {
          color: #4a5568;
          line-height: 1.5;
          font-size: 14px;
        }

        /* Responsive Design */
        @media (max-width: 768px) {
          .badge-demo {
            padding: 20px 10px;
          }

          .demo-header h1 {
            font-size: 2rem;
          }

          .demo-header p {
            font-size: 1rem;
          }

          .component-section,
          .badge-categories {
            padding: 25px 20px;
          }

          .example-grid,
          .usage-examples {
            grid-template-columns: 1fr;
          }

          .badge-grid {
            grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
            gap: 15px;
          }

          .badge-card {
            padding: 15px;
          }
        }

        @media (max-width: 480px) {
          .badge-grid {
            grid-template-columns: 1fr 1fr;
          }

          .size-examples {
            gap: 15px;
          }

          .badge-row {
            gap: 8px;
            padding: 10px;
          }
        }
      `}</style>
    </div>
  );
};

export default BadgeDemo;
