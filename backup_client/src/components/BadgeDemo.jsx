import React from 'react';
import BadgeCard from './BadgeCard';
import BadgeIcon from './BadgeIcon';
import UserBadgeList from './UserBadgeList';

const BadgeDemo = () => {
  // Sample badge data matching server format (id, name, description, icon, points)
  const sampleBadges = [
    {
      id: 1,
      name: 'Welcome Newcomer',
      description: 'Successfully registered and completed profile setup',
      tier: 'Bronze',
      icon: 'fas fa-user-plus',
      points: 10
    },
    {
      id: 2,
      name: 'Conversation Starter',
      description: 'Posted first message to start engaging with the community',
      tier: 'Bronze',
      icon: 'fas fa-comments',
      points: 15
    },
    {
      id: 3,
      name: 'Equipment Expert',
      description: 'Shared valuable insights about technical equipment',
      tier: 'Silver',
      icon: 'fas fa-cogs',
      points: 75
    },
    {
      id: 4,
      name: 'Community Champion',
      description: 'Recognized for exceptional community leadership and support',
      tier: 'Gold',
      icon: 'fas fa-crown',
      points: 200
    },
    {
      id: 5,
      name: 'Active Contributor',
      description: 'Consistently participates in discussions and helps others',
      tier: 'Silver',
      icon: 'fas fa-star',
      points: 100
    },
    {
      id: 6,
      name: 'Master Technician',
      description: 'Demonstrated exceptional expertise across multiple technical domains',
      tier: 'Gold',
      icon: 'fas fa-trophy',
      points: 500
    }
  ];

  // Convert sample badges to UserBadgeList format
  const userBadgeListFormat = sampleBadges.map(badge => ({
    id: badge.id,
    badge_name: badge.name,
    badge_tier: badge.tier,
    badge_icon: badge.icon,
    badge_points: badge.points
  }));

  return (
    <div className="badge-demo">
      <h1>Badge System Components</h1>
      <p className="demo-description">
        These components match the exact styling from badge_preview.html with Font Awesome icons.
        The server provides: id, name, description, icon (Font Awesome class), and points.
      </p>

      <section>
        <h2>BadgeCard Component (For Badge Collections)</h2>
        <div className="badge-cards-demo">
          {sampleBadges.map(badge => (
            <BadgeCard
              key={badge.id}
              id={badge.id}
              name={badge.name}
              description={badge.description}
              tier={badge.tier}
              icon={badge.icon}
              points={badge.points}
              size="medium"
            />
          ))}
        </div>
      </section>

      <section>
        <h2>BadgeIcon Component (For User Profiles)</h2>
        <div className="badge-icons-demo">
          <div className="profile-example">
            <div className="user-info">
              <h3>John Smith</h3>
              <p>Senior Equipment Specialist</p>
            </div>
            <div className="user-badges">
              <span className="badges-label">Badges:</span>
              <UserBadgeList
                badges={userBadgeListFormat}
                maxVisible={4}
              />
            </div>
          </div>

          <div className="profile-example">
            <div className="user-info">
              <h3>Sarah Johnson</h3>
              <p>Equipment Maintenance Expert</p>
            </div>
            <div className="user-badges">
              <span className="badges-label">Badges (max 3):</span>
              <UserBadgeList
                badges={userBadgeListFormat}
                maxVisible={3}
              />
            </div>
          </div>
        </div>

        <div className="size-variants">
          <h3>Badge Card Size Variants</h3>
          <div className="size-demo">
            <BadgeCard
              id={4}
              name="Community Champion"
              description="Recognized for exceptional community leadership"
              tier="Gold"
              icon="fas fa-crown"
              points={200}
              size="small"
            />
            <BadgeCard
              id={4}
              name="Community Champion"
              description="Recognized for exceptional community leadership"
              tier="Gold"
              icon="fas fa-crown"
              points={200}
              size="medium"
            />
            <BadgeCard
              id={4}
              name="Community Champion"
              description="Recognized for exceptional community leadership"
              tier="Gold"
              icon="fas fa-crown"
              points={200}
              size="large"
            />
          </div>
        </div>
      </section>

      {/* Font Awesome CDN */}
      <link
        rel="stylesheet"
        href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css"
        integrity="sha512-SnH5WK+bZxgPHs44uWIX+LLJAJ9/2PkPKZ5QiAj6Ta86w+fsb2TkcmfRyVX3pBnMFcV7oQPJkl9QevSCWr3W6A=="
        crossOrigin="anonymous"
      />

      <style jsx>{`
        .badge-demo {
          max-width: 1200px;
          margin: 0 auto;
          padding: 20px;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
          background: #f8fafc;
          min-height: 100vh;
        }

        h1 {
          color: #1e293b;
          text-align: center;
          margin-bottom: 1rem;
          font-size: 2.5rem;
          font-weight: 700;
        }

        .demo-description {
          text-align: center;
          color: #64748b;
          margin-bottom: 3rem;
          font-size: 1.1rem;
          max-width: 800px;
          margin-left: auto;
          margin-right: auto;
        }

        h2 {
          color: #334155;
          margin: 3rem 0 1.5rem 0;
          border-bottom: 2px solid #e2e8f0;
          padding-bottom: 0.5rem;
          font-size: 1.8rem;
        }

        h3 {
          color: #475569;
          margin: 2rem 0 1rem 0;
          font-size: 1.3rem;
        }

        .badge-cards-demo {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
          gap: 1.5rem;
          margin-bottom: 3rem;
          padding: 2rem;
          background: white;
          border-radius: 12px;
          box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }

        .badge-icons-demo {
          padding: 2rem;
          background: white;
          border-radius: 12px;
          box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
          margin-bottom: 2rem;
        }

        .profile-example {
          display: flex;
          align-items: center;
          gap: 2rem;
          padding: 1.5rem;
          background: #f8fafc;
          border-radius: 8px;
          border: 1px solid #e2e8f0;
          margin-bottom: 1rem;
        }

        .profile-example:last-child {
          margin-bottom: 0;
        }

        .user-info h3 {
          margin: 0 0 0.5rem 0;
          color: #1e293b;
          font-size: 1.25rem;
        }

        .user-info p {
          margin: 0;
          color: #64748b;
          font-size: 0.9rem;
        }

        .user-badges {
          display: flex;
          align-items: center;
          gap: 8px;
          flex-wrap: wrap;
        }

        .badges-label {
          font-weight: 600;
          color: #475569;
          margin-right: 4px;
        }

        .size-variants {
          background: white;
          padding: 2rem;
          border-radius: 12px;
          box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }

        .size-demo {
          display: flex;
          align-items: center;
          gap: 2rem;
          flex-wrap: wrap;
          justify-content: center;
        }

        @media (max-width: 768px) {
          .badge-cards-demo {
            grid-template-columns: 1fr;
          }

          .profile-example {
            flex-direction: column;
            text-align: center;
            gap: 1rem;
          }

          .size-demo {
            flex-direction: column;
            gap: 1rem;
          }
        }
      `}</style>
    </div>
  );
};

export default BadgeDemo;