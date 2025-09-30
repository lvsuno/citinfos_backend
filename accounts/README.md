````markdown
# Accounts App Documentation 👥

## Overview
The `accounts` app provides comprehensive user management for the  Database Social Platform. It handles user authentication, registration with email verification, profile management, professional profiles, social features (follow/block), user sessions, events, and settings. This is the core app for user identity and social network functionality.

## Key Features
- ✅ **Multi-Authentication System**: JWT + Session hybrid authentication with automatic token renewal
- ✅ **Activity Tracking System**: Real-time user activity monitoring with smart throttling
- ✅ **User Profile Management**: Comprehensive profiles with location, privacy, and social features
- ✅ **Professional Profiles**: Extended profiles for business users with verification
- ✅ **Social Network Features**: Follow/block system with relationship management
- ✅ **Session Management**: Redis-backed sessions with activity tracking middleware
- ✅ **Event Logging**: Comprehensive user event tracking for security and analytics
- ✅ **Badge System**: Achievement and badge management for user gamification
- ✅ **Background Tasks**: Celery integration for email sending and cleanup
- ✅ **Security Features**: Bot detection, rate limiting, and session validation

---

## Models

### Core Models
- **VerificationCode**: Email verification codes with expiration and auto-sync
- **UserProfile**: Extended user profile with comprehensive activity tracking and analytics
- **ProfessionalProfile**: Business profiles with company info and verification
- **UserSettings**: User preferences for notifications, privacy, and UI customization
- **Follow**: Social following relationships with approval system
- **Block**: User blocking system for safety
- **UserSession**: Track user login sessions and device analytics
- **UserEvent**: Comprehensive event logging system with 50+ event types
- **BadgeDefinition**: Achievement badge definitions with JSON criteria
- **UserBadge**: Awarded badges to users with metadata

---

## API Endpoints

### Authentication & Session Management
- `POST /api/auth/jwt/login/` — JWT + Session hybrid login with token generation
- `POST /api/auth/jwt/refresh/` — Refresh access tokens (session-bound)
- `POST /api/auth/jwt/logout/` — Logout and blacklist tokens
- `POST /api/auth/jwt/register/` — Register with JWT token response
- `GET /api/auth/jwt/user-info/` — Get current user info via JWT
- `POST /api/auth/jwt/verify/` — Verify token validity
- `GET /api/auth/session/check/` — Check session validity and activity
- `POST /api/auth/session/refresh/` — Refresh session timeout
- `POST /api/auth/register/` — Traditional registration with email verification
- `POST /api/auth/verify/` — Verify registration with email code
- `POST /api/auth/resend-code/` — Resend verification code
- `POST /api/auth/login/` — Session-based login
- `POST /api/auth/logout/` — Session-based logout
- `GET /api/auth/me/` — Get current authenticated user profile

### Badge & Achievement System
- `GET /api/badges/` — List available badges and definitions
- `POST /api/badges/` — Create badge definition (admin)
- `GET /api/badges/{id}/` — Get badge details and criteria
- `PUT/PATCH /api/badges/{id}/` — Update badge definition
- `DELETE /api/badges/{id}/` — Delete badge definition
- `GET /api/user-badges/` — List user's earned badges
- `POST /api/user-badges/` — Award badge to user (system)
- `GET /api/user-badges/{id}/` — Get earned badge details

---

## 🏆 **Badge & Achievement System (Comprehensive Guide)**

The  Database Social Platform includes a sophisticated badge and achievement system designed to gamify user engagement, recognize accomplishments, and encourage community participation.

### **🎯 System Overview**

The badge system consists of two main components:
1. **BadgeDefinition**: Templates that define what badges exist and their criteria
2. **UserBadge**: Records of badges earned by users with metadata

### **📊 Badge Categories**

#### **🥇 Achievement Badges**
Recognize user accomplishments and milestones:
- **First Post** - Create your first  post
- **Popular Creator** - Receive 100+ likes on a single post
- **Community Helper** - Receive 50+ helpful votes on comments
- **Consistent Contributor** - Post  items for 30 consecutive days
- **Expert Reviewer** - Write 10+ detailed reviews

#### **📈 Activity Badges**
Reward ongoing platform engagement:
- **Early Adopter** - Join within first 1000 users
- **Social Butterfly** - Follow 50+ users and get 100+ followers
- **Comment Champion** - Leave 500+ comments
- **Like Enthusiast** - Give 1000+ likes to other users
- **Daily Visitor** - Login for 30 consecutive days

#### **⚡ Special Badges**
Limited or event-based achievements:
- **Beta Tester** - Participate in platform beta testing
- **Bug Hunter** - Report verified platform bugs
- **Community Leader** - Become a moderator or admin
- **Content Creator** - Reach 1000+ followers


### **🏗️ Technical Implementation**

#### **BadgeDefinition Model Structure**
```python
class BadgeDefinition(models.Model):
    # Basic Information
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    category = models.CharField(max_length=50)  # achievement, activity, special

    # Visual Elements
    icon = models.CharField(max_length=100)  # Icon identifier (font-awesome, etc.)
    color = models.CharField(max_length=7)   # Hex color code
    image = models.ImageField(upload_to='badges/', blank=True, null=True)

    # Achievement Criteria (JSON)
    criteria = models.JSONField(default=dict)

    # Metadata
    points = models.PositiveIntegerField(default=10)  # Gamification points
    rarity = models.CharField(max_length=20, default='common')  # common, rare, epic, legendary
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

#### **UserBadge Model Structure**
```python
class UserBadge(models.Model):
    # Core Relationship
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    badge = models.ForeignKey(BadgeDefinition, on_delete=models.CASCADE)

    # Achievement Details
    earned_at = models.DateTimeField(auto_now_add=True)
    progress_data = models.JSONField(default=dict)  # Progress tracking
    is_featured = models.BooleanField(default=False)  # Display on profile

    # System Metadata
    awarded_by = models.CharField(max_length=50, default='system')  # system, admin, manual
    notes = models.TextField(blank=True)  # Admin notes or special circumstances

    class Meta:
        unique_together = ['user', 'badge']  # One badge per user
```

### **🎨 Badge Criteria System**

Badge criteria are stored as flexible JSON configurations that support various achievement types:

#### **Example Criteria Configurations**

**1. Simple Counter Badge:**
```json
{
  "type": "counter",
  "field": "posts_count",
  "threshold": 10,
  "description": "Create 10  posts"
}
```

**2. Time-Based Badge:**
```json
{
  "type": "consecutive_days",
  "action": "login",
  "days": 30,
  "description": "Login for 30 consecutive days"
}
```

**3. Complex Multi-Criteria Badge:**
```json
{
  "type": "multi_criteria",
  "requirements": [
    {"field": "follower_count", "operator": ">=", "value": 100},
    {"field": "posts_count", "operator": ">=", "value": 50},
    {"field": "engagement_score", "operator": ">=", "value": 80}
  ],
  "logic": "AND",
  "description": "Be an influential community member"
}
```

**4. Event-Based Badge:**
```json
{
  "type": "event_based",
  "event_type": "review",
  "count": 10,
  "quality_threshold": 4.0,
  "description": "Write 10 high-quality reviews"
}
```

**5. Social Interaction Badge:**
```json
{
  "type": "social_interaction",
  "interactions": ["like", "comment", "share"],
  "min_count": 500,
  "timeframe": "all_time",
  "description": "Engage actively with community content"
}
```

### **⚙️ Badge Awarding System**

#### **Automatic Badge Detection**
The system uses several mechanisms to automatically detect and award badges:

**1. Real-time Signal Processing:**
```python
# In signals.py
@receiver(post_save, sender=Post)
def check_posting_badges(sender, instance, created, **kwargs):
    if created:
        user_profile = instance.author

        # Check for "First Post" badge
        if user_profile.posts_count == 1:
            award_badge(user_profile, 'first_post')

        # Check for posting milestone badges
        check_milestone_badges(user_profile, 'posts_count')
```

**2. Scheduled Badge Evaluation (Celery Tasks):**
```python
@shared_task
def evaluate_user_badges():
    """Daily task to evaluate all users for badge eligibility"""

    active_badges = BadgeDefinition.objects.filter(is_active=True)
    users = UserProfile.objects.select_related('user').all()

    for user in users:
        for badge in active_badges:
            if not UserBadge.objects.filter(user=user, badge=badge).exists():
                if evaluate_badge_criteria(user, badge.criteria):
                    award_badge(user, badge.name)
```

**3. Event-Driven Badge Awards:**
```python
def award_badge(user_profile, badge_name, notes='', awarded_by='system'):
    """Award a badge to a user"""
    try:
        badge_def = BadgeDefinition.objects.get(name=badge_name, is_active=True)

        # Check if user already has this badge
        if UserBadge.objects.filter(user=user_profile, badge=badge_def).exists():
            return False

        # Award the badge
        user_badge = UserBadge.objects.create(
            user=user_profile,
            badge=badge_def,
            awarded_by=awarded_by,
            notes=notes
        )

        # Log the achievement event
        UserEvent.objects.create(
            user=user_profile,
            event_type='badge_earned',
            description=f'Earned badge: {badge_def.name}',
            metadata={'badge_id': badge_def.id, 'points': badge_def.points}
        )

        # Update user's total badge points (if tracking)
        user_profile.badge_points = F('badge_points') + badge_def.points
        user_profile.save(update_fields=['badge_points'])

        # Send notification (optional)
        send_badge_notification(user_profile, badge_def)

        return True

    except BadgeDefinition.DoesNotExist:
        return False
```

### **🔍 Badge Evaluation Logic**

The system includes sophisticated logic for evaluating different types of badge criteria:

```python
def evaluate_badge_criteria(user_profile, criteria):
    """Evaluate if a user meets badge criteria"""

    criteria_type = criteria.get('type')

    if criteria_type == 'counter':
        field_value = getattr(user_profile, criteria['field'], 0)
        return field_value >= criteria['threshold']

    elif criteria_type == 'consecutive_days':
        return check_consecutive_activity(
            user_profile,
            criteria['action'],
            criteria['days']
        )

    elif criteria_type == 'multi_criteria':
        requirements = criteria['requirements']
        logic = criteria.get('logic', 'AND')
        results = []

        for req in requirements:
            field_value = getattr(user_profile, req['field'], 0)
            operator = req['operator']
            expected = req['value']

            if operator == '>=':
                results.append(field_value >= expected)
            elif operator == '<=':
                results.append(field_value <= expected)
            elif operator == '==':
                results.append(field_value == expected)

        if logic == 'AND':
            return all(results)
        elif logic == 'OR':
            return any(results)

    elif criteria_type == 'event_based':
        return check_event_criteria(user_profile, criteria)

    elif criteria_type == 'social_interaction':
        return check_social_criteria(user_profile, criteria)

    return False
```

### **📱 Frontend Integration**

#### **Badge Display Components**

**1. User Profile Badge Showcase:**
```javascript
// BadgeShowcase.jsx
const BadgeShowcase = ({ user, limit = 6 }) => {
  const [featuredBadges, setFeaturedBadges] = useState([]);
  const [allBadges, setAllBadges] = useState([]);

  useEffect(() => {
    fetchUserBadges(user.id).then(badges => {
      setFeaturedBadges(badges.filter(b => b.is_featured).slice(0, limit));
      setAllBadges(badges);
    });
  }, [user.id, limit]);

  return (
    <div className="badge-showcase">
      <h3>Achievements ({allBadges.length})</h3>
      <div className="badge-grid">
        {featuredBadges.map(userBadge => (
          <BadgeCard
            key={userBadge.id}
            badge={userBadge.badge}
            earnedAt={userBadge.earned_at}
            progress={userBadge.progress_data}
          />
        ))}
      </div>
      {allBadges.length > limit && (
        <button onClick={() => setShowAll(true)}>
          View All Badges ({allBadges.length})
        </button>
      )}
    </div>
  );
};
```

**2. Badge Progress Tracking:**
```javascript
// BadgeProgressCard.jsx
const BadgeProgressCard = ({ badgeDefinition, userProgress }) => {
  const calculateProgress = () => {
    const criteria = badgeDefinition.criteria;
    if (criteria.type === 'counter') {
      const current = userProgress[criteria.field] || 0;
      const target = criteria.threshold;
      return Math.min((current / target) * 100, 100);
    }
    return 0;
  };

  const progress = calculateProgress();
  const isEarned = progress >= 100;

  return (
    <div className={`badge-card ${isEarned ? 'earned' : 'in-progress'}`}>
      <div className="badge-icon" style={{ color: badgeDefinition.color }}>
        <i className={badgeDefinition.icon} />
      </div>
      <div className="badge-info">
        <h4>{badgeDefinition.name}</h4>
        <p>{badgeDefinition.description}</p>
        <div className="progress-bar">
          <div
            className="progress-fill"
            style={{ width: `${progress}%` }}
          />
        </div>
        <span className="progress-text">
          {isEarned ? 'Earned!' : `${Math.round(progress)}% Complete`}
        </span>
      </div>
    </div>
  );
};
```

### **📊 Badge Analytics & Reporting**

#### **Badge Statistics Dashboard**
```python
# In views.py
class BadgeAnalyticsView(APIView):
    def get(self, request):
        analytics = {
            'total_badges_defined': BadgeDefinition.objects.count(),
            'active_badges': BadgeDefinition.objects.filter(is_active=True).count(),
            'total_awards': UserBadge.objects.count(),
            'unique_badge_holders': UserBadge.objects.values('user').distinct().count(),

            # Badge distribution by category
            'badges_by_category': BadgeDefinition.objects.values('category')
                .annotate(count=Count('id'))
                .order_by('category'),

            # Most earned badges
            'popular_badges': UserBadge.objects.values('badge__name')
                .annotate(earned_count=Count('id'))
                .order_by('-earned_count')[:10],

            # Recent achievements
            'recent_awards': UserBadge.objects.select_related('user', 'badge')
                .order_by('-earned_at')[:20],

            # Badge rarity analysis
            'rarity_distribution': BadgeDefinition.objects.values('rarity')
                .annotate(count=Count('id'))
                .order_by('rarity')
        }

        return Response(analytics)
```

### **🎮 Gamification Integration**

#### **Point System**
Each badge awards points that contribute to user gamification:
- **Common badges**: 10-25 points
- **Rare badges**: 50-100 points
- **Epic badges**: 150-300 points
- **Legendary badges**: 500+ points

#### **Leaderboards**
```python
def get_badge_leaderboard(timeframe='all_time'):
    """Get users ranked by badge achievements"""

    users = UserProfile.objects.annotate(
        total_badges=Count('userbadge'),
        badge_points=Sum('userbadge__badge__points'),
        recent_badges=Count(
            'userbadge',
            filter=Q(userbadge__earned_at__gte=timezone.now() - timedelta(days=30))
        )
    ).order_by('-badge_points', '-total_badges')

    return users[:50]  # Top 50
```

### **🔧 Administration & Management**

#### **Badge Management Interface**
Admins can manage badges through Django admin or custom API endpoints:

```python
# In admin.py
@admin.register(BadgeDefinition)
class BadgeDefinitionAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'rarity', 'points', 'is_active', 'created_at']
    list_filter = ['category', 'rarity', 'is_active']
    search_fields = ['name', 'description']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'category', 'rarity')
        }),
        ('Visual Design', {
            'fields': ('icon', 'color', 'image')
        }),
        ('Achievement Rules', {
            'fields': ('criteria', 'points')
        }),
        ('Status', {
            'fields': ('is_active',)
        })
    )
```

#### **Manual Badge Awards**
```python
# Management command: award_badge.py
class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--user', type=int, required=True)
        parser.add_argument('--badge', type=str, required=True)
        parser.add_argument('--reason', type=str, default='Manual award')

    def handle(self, *args, **options):
        try:
            user = UserProfile.objects.get(id=options['user'])
            success = award_badge(
                user,
                options['badge'],
                notes=options['reason'],
                awarded_by='admin'
            )

            if success:
                self.stdout.write(f"Badge '{options['badge']}' awarded to user {user.user.username}")
            else:
                self.stdout.write("Badge award failed")

        except UserProfile.DoesNotExist:
            self.stdout.write("User not found")
```

### **🚀 Usage Examples**

#### **API Usage Examples**

**1. Get User's Badges:**
```http
GET /api/user-badges/?user=123
Authorization: Bearer <token>

Response:
{
  "count": 5,
  "results": [
    {
      "id": 1,
      "badge": {
        "id": 1,
        "name": "First Post",
        "description": "Create your first  post",
        "icon": "fas fa-star",
        "color": "#FFD700",
        "category": "achievement",
        "points": 25
      },
      "earned_at": "2025-08-15T10:30:00Z",
      "is_featured": true,
      "progress_data": {}
    }
  ]
}
```

**2. Get Available Badges:**
```http
GET /api/badges/?category=achievement
Authorization: Bearer <token>

Response:
{
  "count": 10,
  "results": [
    {
      "id": 1,
      "name": "Expert",
      "description": "Post 100+  items",
      "criteria": {
        "type": "counter",
        "field": "posts_count",
        "threshold": 100
      },
      "rarity": "epic",
      "points": 200
    }
  ]
}
```

**3. Check Badge Progress:**
```http
GET /api/users/123/badge-progress/
Authorization: Bearer <token>

Response:
{
  "eligible_badges": [
    {
      "badge": {...},
      "progress": 75,
      "requirements_met": 3,
      "total_requirements": 4,
      "next_milestone": "Need 25 more posts"
    }
  ]
}
```

### **🎯 Best Practices**

#### **Badge Design Guidelines**
1. **Clear Criteria**: Make achievement requirements obvious and measurable
2. **Progressive Difficulty**: Create badge tiers (Bronze, Silver, Gold)
3. **Meaningful Rewards**: Ensure badges represent real accomplishments
4. **Visual Consistency**: Use consistent design language across badges
5. **Regular Updates**: Add seasonal or event-based badges to maintain interest

#### **Performance Considerations**
1. **Batch Processing**: Evaluate badges in background tasks, not real-time
2. **Caching**: Cache badge data for frequently accessed information
3. **Database Optimization**: Use proper indexes on badge-related queries
4. **Rate Limiting**: Prevent badge farming through rate limiting

#### **User Experience**
1. **Celebration**: Show badge awards prominently with animations
2. **Progress Tracking**: Let users see progress toward unearned badges
3. **Social Sharing**: Allow users to share badge achievements
4. **Customization**: Let users choose which badges to display prominently

This comprehensive badge and achievement system enhances user engagement through meaningful recognition of accomplishments and encourages continued platform participation through gamification elements.

## Current Implementation Status 🚀

### ✅ **Completed Features**
- **JWT + Session Hybrid Authentication**: Complete implementation with auto-renew middleware
- **User Activity Tracking**: Real-time last_active updates via middleware with 60-second throttling
- **Profile Signal System**: Automatic updated_at tracking on User model changes (password changes)
- **Badge Achievement System**: Complete badge definitions and user badge tracking
- **Session Management**: Redis-backed sessions with validation and refresh capabilities
- **Professional Profiles**: Extended business user profiles with verification
- **Social Features**: Complete follow/block system with relationship management
- **Event Logging**: Comprehensive user event tracking with 50+ event types
- **Background Tasks**: Scheduled Celery tasks for analytics and cleanup

### 🔧 **Key Technical Features**
- **Smart Activity Middleware**: `UpdateLastActiveMiddleware` using `process_response()` for JWT compatibility
- **Django Signals**: `post_save` signal for automatic UserProfile field updates
- **Migration System**: Applied migration for role field default values
- **Multi-Authentication Support**: DRF Token, JWT+Session (privileged), and Session-only
- **Performance Optimization**: Smart throttling to reduce database writes
- **Error Handling**: Graceful handling of missing profiles and edge cases

---

## API Endpoints 📡

### User Management (RESTful ViewSets)
- `GET /api/users/` — List users with filtering and pagination
- `POST /api/users/` — Create user (admin only)
- `GET /api/users/{id}/` — Retrieve user details
- `PUT/PATCH /api/users/{id}/` — Update user information
- `DELETE /api/users/{id}/` — Delete user account

### User Profiles
- `GET /api/profiles/` — List user profiles with search
- `POST /api/profiles/` — Create user profile
- `GET /api/profiles/{id}/` — Retrieve profile details
- `PUT/PATCH /api/profiles/{id}/` — Update profile information
- `DELETE /api/profiles/{id}/` — Delete profile

### Professional Profiles
- `GET /api/professional-profiles/` — List professional profiles
- `POST /api/professional-profiles/` — Create professional profile
- `GET /api/professional-profiles/{id}/` — Retrieve professional profile
- `PUT/PATCH /api/professional-profiles/{id}/` — Update professional profile
- `DELETE /api/professional-profiles/{id}/` — Delete professional profile

### Social Features
- `GET /api/follows/` — List following relationships
- `POST /api/follows/` — Follow a user
- `GET /api/follows/{id}/` — Get follow relationship details
- `DELETE /api/follows/{id}/` — Unfollow a user
- `GET /api/blocks/` — List blocked users
- `POST /api/blocks/` — Block a user
- `DELETE /api/blocks/{id}/` — Unblock a user

### User Management
- `GET /api/sessions/` — List user sessions
- `POST /api/sessions/` — Create session (login)
- `DELETE /api/sessions/{id}/` — End session (logout)
- `GET /api/events/` — List user events with filtering
- `POST /api/events/` — Log user event
- `GET /api/settings/` — Get user settings
- `PUT/PATCH /api/settings/` — Update user settings

---

## CRUD Operations
All ViewSets support standard RESTful CRUD:
- `GET` (list/retrieve)
- `POST` (create)
- `PUT/PATCH` (update)
- `DELETE` (delete)

---

## Main ViewSets and Functions
- **UserViewSet**: CRUD for users
- **UserProfileViewSet**: CRUD for user profiles
- **ProfessionalProfileViewSet**: CRUD for professional profiles
- **FollowViewSet**: Follow/unfollow users
- **BlockViewSet**: Block/unblock users
- **UserSessionViewSet**: Manage user sessions
- **UserEventViewSet**: Track user events (logins, actions, etc.)
- **UserSettingsViewSet**: User preferences and settings

### Key Functions
- `register_user`: Handles user registration
- `verify_code`: Verifies registration/activation code
- `register_professional`: Registers a professional user
- `login_user`: Authenticates and logs in a user
- `logout_user`: Logs out the current user
- `current_user`: Returns the current authenticated user's info

---

## URLs
All endpoints are prefixed with `/api/`.

- Authentication: `/api/auth/...`
- Users, profiles, follows, blocks, sessions, events, settings: `/api/users/`, `/api/profiles/`, etc.

---

## Example Usage

**Register a user:**
```http
POST /api/auth/register/
{
  "username": "jane",
  "email": "jane@example.com",
  "password": "securepass"
}
```

**Login:**
```http
POST /api/auth/login/
{
  "username": "jane",
  "password": "securepass"
}
```

**Follow a user:**
```http
POST /api/follows/
{
  "follower": 1,
  "following": 2
}
```

---

## Tests

### Test Files
- `tests.py` — Main test suite for accounts
- `test_follow.py` — Tests for follow/unfollow/block logic

### Running Tests
```sh
python manage.py test accounts
```
Or for a specific test file:
```sh
python manage.py test accounts.test_follow
```

---


## Models (Detailed)

- **User**: Standard Django user model from `django.contrib.auth.models.User`. Handles authentication, username, email, password, and basic user info.

- **UserProfile**: Extends the User model with:
  - `role`: User's role (owner, normal, data_provider, professional, admin, moderator)
  - `phone_number`, `date_of_birth`, `bio`, `profile_picture`, `cover_media`, `cover_media_type`
  - `country`, `city`: Foreign keys to location
  - Privacy: `is_private`, `show_email`, `show_phone`, `show_location`
  - Status: `is_verified`, `is_suspended`, `suspension_reason`
  - Analytics: `follower_count`, `following_count`, `posts_count`
  - Recommendation: `engagement_score`, `content_quality_score`, `interaction_frequency`
  - Timestamps: `created_at`, `updated_at`, `last_active`
  - Properties: `location`, `full_name`, `display_name`
  - Methods: `update_follower_counts()`

- **ProfessionalProfile**: For users with professional roles. Fields:
  - `profile`: One-to-one with UserProfile
  - `description`, `phone`, `website`, `business_address`
  - Professional details: `company_name`, `job_title`, `years_experience`, `certifications`, `services_offered`
  - Verification: `is_verified`, `verification_date`
  - Timestamps: `created_at`, `updated_at`

- **UserSettings**: User preferences/settings. Fields:
  - `user`: One-to-one with UserProfile
  - Notification: `email_notifications`, `push_notifications`, `warranty_expiry_notifications`, `maintenance_reminder_notifications`, `notification_frequency`
  - Privacy: `profile_visibility`
  - Interface: `language`, `theme`, `timezone`
  - Content: `mature_content`, `auto_play_videos`
  - Timestamps: `created_at`, `updated_at`

- **Follow**: User following relationships.
  - `follower`, `followed`: Foreign keys to UserProfile
  - `created_at`, `is_deleted`
  - Unique constraint: (follower, followed)

- **Block**: User blocking relationships.
  - `blocker`, `blocked`: Foreign keys to UserProfile
  - `reason`, `created_at`
  - Unique constraint: (blocker, blocked)

- **UserSession**: Tracks user sessions for analytics.
  - `user`: ForeignKey to UserProfile
  - `session_id`, `ip_address`, `user_agent`, `device_info`, `location_data`, `device_fingerprint`
  - Metrics: `pages_visited`, `started_at`, `ended_at`, `is_active`, `is_deleted`
  - Properties: `time_spent`

- **UserEvent**: Logs user account, security, and activity events.
  - `user`: ForeignKey to UserProfile
  - `session`: ForeignKey to UserSession (nullable)
  - `event_type`: Type of event (login, logout, register, follow, post_create, etc.)
  - `severity`: Event severity (low, medium, high, critical)
  - `description`, `metadata`, `success`, `error_message`
  - `target_user`: ForeignKey to UserProfile (nullable, for events about another user)
  - Review: `requires_review`, `reviewed_at`, `reviewed_by`
  - `created_at`
  - Properties: `is_security_event`, `risk_score`

- **VerificationCode**: Stores verification codes for user registration/activation.
  - `user`: One-to-one with UserProfile
  - `code`, `created_at`, `is_used`


## Background Tasks (Celery)
The accounts app uses Celery for background processing of analytics, counters, security, and session management. Tasks are scheduled via **django-celery-beat** (database-driven scheduling) and can be managed through Django Admin at `/admin/django_celery_beat/`.

### Task Schedule Table

| Task Name                        | Function Name                        | Schedule (crontab)         | Description |
|----------------------------------|--------------------------------------|----------------------------|-------------|
| update-user-counters             | update_user_counters                 | Every 30 minutes           | Update follower, following, and post counters for all users |
| update-user-engagement-scores    | update_user_engagement_scores        | Daily at 02:00             | Update engagement scores for all users based on activity |
| cleanup-old-user-events          | cleanup_old_user_events              | Daily at 03:15             | Clean up old user events for performance |
| analyze-user-security-events     | analyze_user_security_events         | Daily at 00:15             | Analyze and flag suspicious user security events |
| update-user-session-analytics    | update_user_session_analytics        | Every 20 minutes           | Update session analytics and metrics |
| process-user-event-alerts        | process_user_event_alerts            | Every 5 minutes            | Process and alert on high-priority user events |
| cleanup-expired-sessions         | cleanup_expired_sessions             | Daily at 04:00             | Clean up expired and inactive user sessions |
| generate-user-analytics-report   | generate_user_analytics_report       | Daily at 05:00             | Generate analytics report for user activity |

---

## Detailed Task Descriptions

### 1. update_user_counters
**Schedule:** Every 30 minutes
**Purpose:** Updates follower, following, and post counters for all users.

### 2. update_user_engagement_scores
**Schedule:** Daily at 02:00
**Purpose:** Updates engagement scores for all users based on recent activity.

### 3. cleanup_old_user_events
**Schedule:** Daily at 03:15
**Purpose:** Cleans up old user events to maintain database performance.

### 4. analyze_user_security_events
**Schedule:** Daily at 00:15
**Purpose:** Analyzes security events and flags suspicious patterns.

### 5. update_user_session_analytics
**Schedule:** Every 20 minutes
**Purpose:** Updates session analytics and metrics, marks inactive sessions.

### 6. process_user_event_alerts
**Schedule:** Every 5 minutes
**Purpose:** Processes high-priority user events and sends alerts.

### 7. cleanup_expired_sessions
**Schedule:** Daily at 04:00
**Purpose:** Cleans up expired and inactive user sessions.

### 8. generate_user_analytics_report
**Schedule:** Daily at 05:00
**Purpose:** Generates a daily analytics report for user activity.

## Signals & Automation
- Auto-create UserProfile on user creation
- Track login/logout and other events

---

## Permissions & Security
- Most endpoints require authentication
- Registration and login are public
- Follows/blocks are permission-checked


---

## 🔐 Authentication System (Updated)

This project implements a **hybrid JWT + Session authentication system** with the following characteristics:

### **Current Implementation (August 2025)**
- **JWT Access Tokens**: 1 hour lifetime with automatic renewal via middleware
- **JWT Refresh Tokens**: 7 days lifetime with rotation and blacklisting
- **Redis Sessions**: Server-side session storage with configurable timeout
- **Activity Middleware**: Real-time user activity tracking with smart throttling
- **Auto-Renewal**: Seamless token refresh when session is valid

### **Key Features**
- ✅ **Hybrid Authentication**: JWT tokens + Redis sessions working together
- ✅ **Smart Middleware**: `UpdateLastActiveMiddleware` for activity tracking
- ✅ **Signal Integration**: Automatic profile updates on User model changes
- ✅ **Session Validation**: Multi-layer session validation and refresh
- ✅ **Security**: Token blacklisting, rotation, and session binding

### **Authentication Flow (Simplified)**
1. **Login**: `POST /api/auth/jwt/login/` → Returns access + refresh tokens + creates session
2. **API Requests**: Use `Authorization: Bearer <access-token>` header
3. **Activity Tracking**: Middleware automatically updates `last_active` field every 60+ seconds
4. **Auto-Renewal**: Middleware provides new tokens in `X-Renewed-Access` header when needed
5. **Session Refresh**: `POST /api/auth/session/refresh/` extends session timeout
6. **Logout**: `POST /api/auth/jwt/logout/` → Blacklists tokens and cleans session

### **User Activity Tracking**
- **Real-time Updates**: `UserProfile.last_active` updated automatically on authenticated requests
- **Smart Throttling**: Database writes limited to once per 60 seconds per user
- **Signal-based Updates**: `UserProfile.updated_at` updated on password changes via Django signals
- **Performance Optimized**: Middleware uses `process_response()` for JWT compatibility

---

## 🏗 Architecture & Technical Implementation

### **Middleware Stack**
- **UpdateLastActiveMiddleware**: Tracks user activity with JWT authentication support
- **JWTAutoRenewMiddleware**: Automatic token renewal for seamless user experience
- **SessionValidationMiddleware**: Validates and manages session lifecycle
- **SessionActivityMiddleware**: Tracks session activity and metrics

### **Django Signals**
- **User post_save**: Automatically updates `UserProfile.updated_at` on User model changes
- **Profile Creation**: Auto-creates UserProfile on User creation
- **Event Logging**: Automatically logs user events for security and analytics

### **Background Tasks (Celery)**
The accounts app includes comprehensive background task scheduling for maintenance and analytics.

---

## See Also
- [Django REST Framework docs](https://www.django-rest-framework.org/)
- [Project main README](../README.md)