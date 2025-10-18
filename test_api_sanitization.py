#!/usr/bin/env python
"""Test API serialization with HTML sanitization."""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'citinfos_backend.settings')
django.setup()

from content.models import Post
from accounts.models import UserProfile
from content.unified_serializers import UnifiedPostSerializer

# Get a verified user for testing
user = UserProfile.objects.filter(
    user__is_active=True,
    is_verified=True
).first()

if not user:
    print('❌ No verified user found. Creating test user...')
    from django.contrib.auth import get_user_model
    User = get_user_model()
    test_user = User.objects.create_user(
        username='test_api_user',
        email='test@example.com',
        password='testpass123'
    )
    user = UserProfile.objects.get(user=test_user)
    user.is_verified = True
    user.save()
    print(f'✅ Created verified test user: {user.user.username}')

print('=== Test 1: Create article post with embedded media (XSS attempt) ===')
# Create an article post with rich HTML including XSS attempt
article_post = Post.objects.create(
    author=user,
    post_type='article',
    content='<p>Article <strong>excerpt</strong></p><script>alert("XSS")</script>',
    article_content='<h2>My Article Title</h2><p>Introduction text</p><video src="https://example.com/video.mp4" controls></video><p>More content</p><audio src="test.mp3" controls></audio><script>alert("XSS")</script><img src="x" onerror="alert(1)">'
)

# Serialize and check the response
serializer = UnifiedPostSerializer(article_post)
data = serializer.data

print(f'Post Type: {data["post_type"]}')
print(f'Is Article: {data["is_article"]}')
print(f'Has Embedded Media: {data["has_embedded_media"]}')
print(f'\nContent (sanitized): {data["content"]}')
print(f'\nArticle Content (sanitized): {data["article_content"]}')
print(f'\n✅ Check: <script> tags removed: {"<script>" not in data["article_content"]}')
print(f'✅ Check: onerror handler removed: {"onerror" not in data["article_content"]}')
print(f'✅ Check: <video> tag preserved: {"<video" in data["article_content"]}')
print(f'✅ Check: <audio> tag preserved: {"<audio" in data["article_content"]}')

print('\n=== Test 2: Create text post with basic HTML (XSS attempt) ===')
# Create a text post with basic HTML
text_post = Post.objects.create(
    author=user,
    post_type='text',
    content='<p>Hello <strong>World</strong>!</p><a href="javascript:alert(1)">Click</a><script>alert("XSS")</script>'
)

serializer2 = UnifiedPostSerializer(text_post)
data2 = serializer2.data

print(f'Post Type: {data2["post_type"]}')
print(f'Is Article: {data2["is_article"]}')
print(f'Has Embedded Media: {data2["has_embedded_media"]}')
print(f'\nContent (sanitized): {data2["content"]}')
print(f'\n✅ Check: <script> tags removed: {"<script>" not in data2["content"]}')
print(f'✅ Check: javascript: protocol removed: {"javascript:" not in data2["content"]}')
print(f'✅ Check: <strong> tag preserved: {"<strong>" in data2["content"]}')

print('\n=== API Field Count ===')
print(f'Total fields in response: {len(data)}')
print(f'\nAll fields: {sorted(data.keys())}')

# Clean up
article_post.delete()
text_post.delete()
print('\n✅ Test completed and cleaned up!')
