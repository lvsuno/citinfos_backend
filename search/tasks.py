

from celery import shared_task
from .models import UserSearchQuery

@shared_task
def analyze_search_queries():
    from django.db.models import Count
    popular = UserSearchQuery.objects.values('query').annotate(count=Count('id')).order_by('-count')[:10]
    return list(popular)

@shared_task
def count_search_queries_by_type():
    from django.db.models import Count
    return list(UserSearchQuery.objects.values('search_type').annotate(count=Count('id')).order_by('-count'))

@shared_task
def get_recent_search_queries(limit=5):
    recent = UserSearchQuery.objects.filter(is_deleted=False).order_by('-created_at')[:limit]
    return [{'id': q.id, 'query': q.query, 'search_type': q.search_type} for q in recent]

# Advanced analytics: cache recent searches by user and type using Redis

@shared_task
def cache_recent_searches_by_user_type(user_id, search_type, limit=5):
    import redis
    from django.conf import settings
    r = redis.Redis.from_url(settings.REDIS_URL)
    recent = UserSearchQuery.objects.filter(user_id=user_id, search_type=search_type, is_deleted=False).order_by('-created_at')[:limit]
    data = [{'id': q.id, 'query': q.query, 'created_at': str(q.created_at)} for q in recent]
    cache_key = f'recent_searches:{user_id}:{search_type}'
    r.set(cache_key, str(data))
    return data



@shared_task
def cache_all_users_recent_searches():
    from accounts.models import UserProfile
    types = ['post', 'user']  # Equipment functionality removed
    for profile in UserProfile.objects.all():
        for t in types:
            cache_recent_searches_by_user_type(str(profile.id), t, limit=5)
