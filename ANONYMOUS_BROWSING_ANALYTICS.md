# Anonymous Browsing Behavior Analytics - Strategy & Architecture

## 🎯 Your Questions

> "Is it not also better to track anonymous user browsing behavior? Like in general, what pages are visited for how many times, is the user authenticated or not?"

**YES! Absolutely!** Anonymous browsing behavior tracking is valuable for:
1. Understanding content popularity (what pages attract visitors)
2. Conversion funnel analysis (anonymous → signup)
3. A/B testing effectiveness
4. SEO and content strategy
5. Bot detection and security

## 📊 Current State Analysis

### What You Already Have

#### 1. **UserSession Model** (DB + Redis) - Authenticated Users
```python
# accounts/models.py - UserSession
class UserSession(models.Model):
    user = ForeignKey(UserProfile)  # Links to account
    session_id = CharField(unique=True)

    # Tracking data
    ip_address = GenericIPAddressField()
    user_agent = TextField()
    device_info = JSONField()
    location_data = JSONField()
    device_fingerprint = CharField(max_length=128)
    fast_fingerprint = CharField(max_length=64)

    # Metrics
    pages_visited = PositiveIntegerField(default=0)  # ✅ Already tracking!

    # Lifecycle
    started_at = DateTimeField()
    ended_at = DateTimeField()
    expires_at = DateTimeField()
    is_active = BooleanField()
```

**Storage:**
- ✅ **Database**: Permanent record
- ✅ **Redis**: `session:{session_id}` - Copy for fast access

#### 2. **Community Visitor Tracking** (Redis Only) - Auth + Anonymous
```python
# communities/visitor_tracker.py
# Redis keys:
community:{id}:visitors = {
    # Authenticated
    "user_uuid": {visitor_data},

    # Anonymous
    "anon_fingerprint123": {visitor_data}
}
```

**Storage:**
- ✅ **Redis**: Temporary (5-min TTL)
- ❌ **Database**: NO permanent storage for anonymous

### The Gap: Anonymous Browsing Behavior

**Currently tracked:**
- ✅ Community page visits (Redis, 5-min TTL)
- ✅ Real-time visitor count
- ✅ Auth vs anonymous split

**NOT currently tracked:**
- ❌ Anonymous page views across the site (posts, profiles, search, etc.)
- ❌ Anonymous user journey (page sequence)
- ❌ Anonymous session duration
- ❌ Anonymous pages_visited count
- ❌ Anonymous conversion tracking (when they sign up)

---

## 🏗️ Proposed Architecture: Anonymous Session Tracking

### Option 1: Session-like Tracking for Anonymous (RECOMMENDED)

Create a **lightweight anonymous session** concept without Django sessions:

#### A. Anonymous Session Model (Database)

```python
# analytics/models.py

class AnonymousSession(models.Model):
    """
    Track anonymous browsing sessions for analytics.

    Unlike authenticated UserSession, this is for:
    - Users without accounts
    - Users not logged in
    - Temporary behavioral tracking
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)

    # Identification (no user link)
    device_fingerprint = models.CharField(
        max_length=128,
        db_index=True,
        help_text="Device fingerprint for anonymous identification"
    )
    session_start = models.DateTimeField(auto_now_add=True)
    session_end = models.DateTimeField(null=True, blank=True)

    # Network/Device
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    device_type = models.CharField(max_length=20)  # mobile/desktop/tablet
    browser = models.CharField(max_length=50, blank=True)
    os = models.CharField(max_length=50, blank=True)

    # Location (optional, from IP geolocation)
    country = models.CharField(max_length=2, blank=True)
    city = models.CharField(max_length=100, blank=True)

    # Behavioral metrics
    pages_visited = models.PositiveIntegerField(default=0)
    duration_seconds = models.PositiveIntegerField(default=0)

    # Conversion tracking
    converted_to_user = models.ForeignKey(
        'accounts.UserProfile',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="If anonymous user signed up, link to their account"
    )
    converted_at = models.DateTimeField(null=True, blank=True)

    # Referral tracking
    landing_page = models.URLField(max_length=500)
    referrer = models.URLField(max_length=500, blank=True)
    utm_source = models.CharField(max_length=100, blank=True)
    utm_medium = models.CharField(max_length=100, blank=True)
    utm_campaign = models.CharField(max_length=100, blank=True)

    # Status
    is_active = models.BooleanField(default=True)
    is_bot = models.BooleanField(default=False)  # Bot detection flag

    class Meta:
        indexes = [
            models.Index(fields=['device_fingerprint', '-session_start']),
            models.Index(fields=['is_active', '-session_start']),
            models.Index(fields=['converted_to_user']),
            models.Index(fields=['-session_start']),
        ]

    def __str__(self):
        return f"Anonymous {self.device_fingerprint[:8]}... - {self.session_start}"
```

#### B. Anonymous Page View Model (Database)

```python
# analytics/models.py

class AnonymousPageView(models.Model):
    """
    Track individual page views for anonymous users.
    Similar to PageView but for anonymous sessions.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)

    # Link to anonymous session
    session = models.ForeignKey(
        AnonymousSession,
        on_delete=models.CASCADE,
        related_name='page_views'
    )

    # Page details
    url = models.URLField(max_length=500)
    url_name = models.CharField(max_length=100, blank=True)  # Django URL name
    page_type = models.CharField(
        max_length=50,
        choices=[
            ('home', 'Homepage'),
            ('community', 'Community Page'),
            ('post', 'Post Detail'),
            ('profile', 'User Profile'),
            ('search', 'Search Results'),
            ('other', 'Other'),
        ]
    )

    # Timing
    viewed_at = models.DateTimeField(auto_now_add=True)
    time_on_page_seconds = models.PositiveIntegerField(default=0)

    # Referral
    referrer = models.URLField(max_length=500, blank=True)

    # Engagement
    scroll_depth = models.PositiveSmallIntegerField(
        default=0,
        help_text="Percentage of page scrolled (0-100)"
    )
    interactions = models.PositiveIntegerField(
        default=0,
        help_text="Clicks, hovers, etc."
    )

    class Meta:
        indexes = [
            models.Index(fields=['session', '-viewed_at']),
            models.Index(fields=['page_type', '-viewed_at']),
            models.Index(fields=['-viewed_at']),
        ]
        ordering = ['-viewed_at']
```

#### C. Redis for Real-Time Tracking

```python
# Redis structure for anonymous sessions (hot data)
anon_session:{fingerprint} = {
    'session_id': 'uuid',
    'device_fingerprint': 'hash',
    'started_at': 'timestamp',
    'last_activity': 'timestamp',
    'pages_visited': 5,
    'current_page': '/communities/montreal/',
    'is_active': true
}

# TTL: 30 minutes (longer than community visitor tracking)
# After expiration, data persists in DB only
```

---

### Option 2: Aggregate Analytics Only (Privacy-First)

If you want maximum privacy and minimal storage:

#### A. No Individual Tracking

```python
# analytics/models.py

class PageAnalytics(models.Model):
    """
    Aggregate page analytics (no individual tracking).
    One record per page per day.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)

    # Page identification
    url_path = models.CharField(max_length=500)
    page_type = models.CharField(max_length=50)

    # Date aggregation
    date = models.DateField(db_index=True)

    # Counts (aggregated, no individuals)
    total_views = models.PositiveIntegerField(default=0)
    authenticated_views = models.PositiveIntegerField(default=0)
    anonymous_views = models.PositiveIntegerField(default=0)
    unique_visitors = models.PositiveIntegerField(default=0)

    # Engagement metrics (averages)
    avg_time_on_page = models.FloatField(default=0.0)
    avg_scroll_depth = models.FloatField(default=0.0)

    # Device breakdown
    mobile_views = models.PositiveIntegerField(default=0)
    desktop_views = models.PositiveIntegerField(default=0)
    tablet_views = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = [['url_path', 'date']]
        indexes = [
            models.Index(fields=['-date', 'page_type']),
        ]
```

**Pros:**
- ✅ Maximum privacy (no individual tracking)
- ✅ Small database (one record per page per day)
- ✅ GDPR compliant
- ✅ Fast queries

**Cons:**
- ❌ No conversion tracking
- ❌ No user journey analysis
- ❌ No personalization possible

---

## 🔄 Recommended Hybrid Approach

Combine both options for balanced privacy and functionality:

### 1. **Real-Time Tracking** (Redis, 30-min TTL)
```python
# Hot data - temporary, auto-expires
anon_session:{fingerprint}
community:{id}:visitors
```

### 2. **Session Summary** (Database - Anonymous)
```python
# AnonymousSession
- Basic session info (start, end, pages_visited, duration)
- Device/location aggregates
- Conversion tracking (if they sign up)
- Retention: 90 days, then delete
```

### 3. **Page Analytics** (Database - Aggregated)
```python
# PageAnalytics
- Daily aggregates per page
- No individual identification
- Retention: Forever (it's aggregated)
```

### 4. **Authenticated Sessions** (Database - Full Detail)
```python
# UserSession (existing)
- Full tracking with user link
- Retention: Forever (user consented by signing up)
```

---

## 📋 Implementation Plan

### Phase 1: Extend Middleware (EASY)

Update `analytics/middleware.py` to track anonymous page views:

```python
# analytics/middleware.py

class AnalyticsTrackingMiddleware(MiddlewareMixin):

    def _track_page_view(self, request, response, user_profile):
        """Track ALL page views (auth + anonymous)."""

        # Generate fingerprint
        from core.device_fingerprint import OptimizedDeviceFingerprint
        fingerprint = OptimizedDeviceFingerprint.get_fast_fingerprint(request)

        is_authenticated = user_profile is not None

        if is_authenticated:
            # Existing authenticated tracking
            self._track_authenticated_page_view(request, user_profile)
        else:
            # NEW: Anonymous tracking
            self._track_anonymous_page_view(request, fingerprint)

    def _track_anonymous_page_view(self, request, fingerprint):
        """Track anonymous user page views."""
        import redis
        from django.conf import settings

        redis_client = redis.StrictRedis.from_url(settings.REDIS_URL)
        session_key = f"anon_session:{fingerprint}"

        # Get or create anonymous session in Redis
        session_data = redis_client.get(session_key)

        if session_data:
            # Existing session - update
            session = json.loads(session_data)
            session['pages_visited'] += 1
            session['last_activity'] = timezone.now().isoformat()
            session['current_page'] = request.path
        else:
            # New session - create
            session = {
                'session_id': str(uuid.uuid4()),
                'device_fingerprint': fingerprint,
                'started_at': timezone.now().isoformat(),
                'last_activity': timezone.now().isoformat(),
                'pages_visited': 1,
                'current_page': request.path,
                'landing_page': request.path,
                'referrer': request.META.get('HTTP_REFERER', ''),
                'ip_address': self._get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'is_active': True
            }

        # Store in Redis with 30-min TTL
        redis_client.setex(
            session_key,
            1800,  # 30 minutes
            json.dumps(session, default=str)
        )

        # Async task: Persist to database periodically
        from analytics.tasks import persist_anonymous_session
        persist_anonymous_session.delay(fingerprint, session)

        logger.info(
            f"Tracked anonymous page view: {fingerprint[:8]}... "
            f"→ {request.path} (page {session['pages_visited']})"
        )
```

### Phase 2: Create Celery Task for DB Persistence

```python
# analytics/tasks.py

@shared_task
def persist_anonymous_session(fingerprint, session_data):
    """
    Persist anonymous session to database periodically.
    Only creates/updates DB record every 5th page view to reduce DB load.
    """
    from analytics.models import AnonymousSession, AnonymousPageView
    from django.utils import timezone

    pages_visited = session_data.get('pages_visited', 0)

    # Only persist every 5 pages or on first page
    if pages_visited % 5 != 1 and pages_visited != 1:
        return

    try:
        # Get or create anonymous session
        session, created = AnonymousSession.objects.get_or_create(
            device_fingerprint=fingerprint,
            is_active=True,
            defaults={
                'ip_address': session_data.get('ip_address'),
                'user_agent': session_data.get('user_agent'),
                'device_type': _detect_device_type(session_data.get('user_agent')),
                'pages_visited': pages_visited,
                'landing_page': session_data.get('landing_page'),
                'referrer': session_data.get('referrer'),
            }
        )

        if not created:
            # Update existing
            session.pages_visited = pages_visited
            session.save(update_fields=['pages_visited'])

        logger.info(f"Persisted anonymous session {session.id} (pages: {pages_visited})")

    except Exception as e:
        logger.error(f"Failed to persist anonymous session: {e}")


@shared_task
def finalize_anonymous_session(fingerprint):
    """
    Finalize anonymous session when it expires (called by Redis expiry webhook or cron).
    """
    from analytics.models import AnonymousSession
    from django.utils import timezone

    try:
        session = AnonymousSession.objects.filter(
            device_fingerprint=fingerprint,
            is_active=True
        ).first()

        if session:
            session.is_active = False
            session.session_end = timezone.now()
            session.duration_seconds = int(
                (session.session_end - session.session_start).total_seconds()
            )
            session.save()

            logger.info(
                f"Finalized anonymous session {session.id} "
                f"({session.pages_visited} pages, {session.duration_seconds}s)"
            )
    except Exception as e:
        logger.error(f"Failed to finalize anonymous session: {e}")
```

### Phase 3: Conversion Tracking (Anonymous → Authenticated)

```python
# accounts/jwt_views.py - In registration/login view

def register_user(request):
    """Handle user registration."""
    # ... existing registration logic ...

    # NEW: Link anonymous session to new account
    from core.device_fingerprint import OptimizedDeviceFingerprint
    from analytics.models import AnonymousSession
    from django.utils import timezone

    fingerprint = OptimizedDeviceFingerprint.get_fast_fingerprint(request)

    # Find recent anonymous session
    recent_anon_session = AnonymousSession.objects.filter(
        device_fingerprint=fingerprint,
        is_active=True,
        session_start__gte=timezone.now() - timedelta(hours=24)
    ).first()

    if recent_anon_session:
        # Link to new user account
        recent_anon_session.converted_to_user = user_profile
        recent_anon_session.converted_at = timezone.now()
        recent_anon_session.is_active = False
        recent_anon_session.save()

        logger.info(
            f"Conversion tracked: Anonymous session {recent_anon_session.id} "
            f"→ User {user_profile.user.username}"
        )

        # Track conversion event
        UserEvent.objects.create(
            user=user_profile,
            event_type='account_created',
            metadata={
                'from_anonymous_session': str(recent_anon_session.id),
                'anonymous_pages_visited': recent_anon_session.pages_visited,
                'anonymous_duration_seconds': recent_anon_session.duration_seconds,
                'landing_page': recent_anon_session.landing_page,
                'referrer': recent_anon_session.referrer,
            }
        )
```

---

## 📊 Data Comparison

### Current State (After Community Visitor Tracking)

| Data Type | Authenticated | Anonymous |
|-----------|---------------|-----------|
| **Community Visits** | ✅ Redis (5min) + DB (UserEvent) | ✅ Redis (5min) only |
| **General Page Views** | ✅ Redis + DB (via UserSession) | ❌ Not tracked |
| **Session Duration** | ✅ DB (UserSession) | ❌ Not tracked |
| **Page Sequence** | ✅ Can query UserEvent | ❌ Not tracked |
| **Conversion Tracking** | N/A | ❌ Not tracked |

### Proposed State (After Anonymous Session Tracking)

| Data Type | Authenticated | Anonymous |
|-----------|---------------|-----------|
| **Community Visits** | ✅ Redis (5min) + DB (UserEvent) | ✅ Redis (5min) + DB (AnonymousSession) |
| **General Page Views** | ✅ Redis + DB (UserSession) | ✅ Redis (30min) + DB (AnonymousSession) |
| **Session Duration** | ✅ DB (UserSession) | ✅ DB (AnonymousSession.duration_seconds) |
| **Page Sequence** | ✅ UserEvent queries | ✅ AnonymousPageView queries (optional) |
| **Conversion Tracking** | N/A | ✅ AnonymousSession.converted_to_user |

---

## 🔐 Privacy Considerations

### What We Track for Anonymous

**Minimal (Current Community Visits):**
- Device fingerprint (non-personal hash)
- Pages visited count
- Division (if community visit)
- TTL: 5 minutes

**Extended (Proposed):**
- Device fingerprint
- Pages visited count
- Session duration
- Landing page + referrer
- Device type (mobile/desktop)
- IP-based location (city/country, not precise)
- TTL: 30 min (Redis), 90 days (DB)

### What We DON'T Track

- ❌ Name, email, or any personal identifiers
- ❌ Precise GPS location
- ❌ Cross-site tracking
- ❌ Third-party cookies
- ❌ Behavioral profiling for ads
- ❌ Data selling to third parties

### GDPR Compliance

**Legitimate Interest:** Analytics for service improvement
**Data Minimization:** Only essential metrics
**Purpose Limitation:** Analytics only, no marketing
**Storage Limitation:** 90-day retention for anonymous
**Right to Object:** Can't identify individuals to honor requests
**Transparency:** Privacy policy disclosure

---

## 💡 Answers to Your Questions

> "Actually for authenticated user, session is already stored in redis (just a copy of what is in the db)."

**Correct!** You have:
```python
# Redis: session:{session_id} (copy for fast access)
# DB: UserSession (permanent record)
```

This is the **hybrid approach** - perfect for performance + persistence.

> "Is it not also better to track anonymous user browsing behavior?"

**YES!** Benefits:
1. **Conversion Funnel**: See what anonymous users do before signing up
2. **Content Strategy**: Know what pages attract visitors
3. **SEO Optimization**: Understand organic traffic behavior
4. **A/B Testing**: Test changes on anonymous traffic
5. **Bot Detection**: Identify bot patterns vs. real users

> "Like in general, what pages are visited for how many times, is the user authenticated or not?"

**Exactly!** Proposed tracking:
- ✅ **Page URL**: What they visited
- ✅ **Visit Count**: How many pages in session
- ✅ **Auth Status**: Authenticated vs. anonymous split
- ✅ **Device Type**: Mobile, desktop, tablet
- ✅ **Time**: When and how long
- ✅ **Journey**: Landing page → conversion path

---

## 🎯 Recommendation

**Implement the Hybrid Approach:**

1. **Redis** (Hot Data - 30 min TTL):
   - `anon_session:{fingerprint}` - Current session state
   - Auto-expires after inactivity
   - Fast lookups

2. **Database** (Warm Data - 90 day retention):
   - `AnonymousSession` - Session summaries
   - Conversion tracking
   - Periodic persistence (every 5th page)
   - Batch cleanup after 90 days

3. **Database** (Cold Data - Forever):
   - `PageAnalytics` - Daily aggregates
   - No individual identification
   - Historical trends

This gives you:
- ✅ Real-time analytics
- ✅ Conversion tracking
- ✅ Privacy compliance
- ✅ Reasonable storage costs
- ✅ Actionable insights

**Start with Phase 1** (middleware) - it's a 20-line addition to existing code!
