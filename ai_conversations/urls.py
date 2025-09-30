"""URLs for the ai_conversations app."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'llm-models', views.LLMModelViewSet, basename='llm-model')
router.register(r'agents', views.ConversationAgentViewSet, basename='agent')
router.register(r'conversations', views.AIConversationViewSet, basename='ai-conversation')
router.register(r'messages', views.AIMessageViewSet, basename='ai-message')
router.register(r'ratings', views.AIMessageRatingViewSet, basename='rating')
router.register(r'analytics', views.AIUsageAnalyticsViewSet, basename='analytics')
router.register(r'model-performance', views.AIModelPerformanceViewSet, basename='model-performance')
router.register(r'conversation-summaries', views.AIConversationSummaryViewSet, basename='conversation-summary')
router.register(r'flags', views.AIMessageFlagViewSet, basename='flag')

# Add custom URL patterns for specific functionality
custom_patterns = [
    path('conversations/',
         views.AIConversationViewSet.as_view({'get': 'list', 'post': 'create'}),
         name='conversation-list'),
    path('models/active/',
         views.LLMModelViewSet.as_view({'get': 'list'}),
         name='active-models'),
    path('agents/public/',
         views.ConversationAgentViewSet.as_view({'get': 'list'}),
         name='public-agents'),
    path('conversations/<uuid:pk>/send-message/',
         views.AIMessageViewSet.as_view({'post': 'create'}),
         name='send-ai-message',
         kwargs={'lookup_field': 'conversation_id'}),
    path('conversations/<uuid:pk>/messages/',
         views.AIConversationViewSet.as_view({'get': 'messages'}),
         name='conversation-messages'),
    path('analytics/dashboard/',
         views.AIUsageAnalyticsViewSet.as_view({'get': 'list'}),
         name='ai-analytics-dashboard'),
]

urlpatterns = [
    path('api/ai/', include(router.urls)),
    path('api/ai/', include(custom_patterns)),
]
