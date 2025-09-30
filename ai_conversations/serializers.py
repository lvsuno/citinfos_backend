"""Serializers for the ai_conversations app (refactored)."""

from decimal import Decimal
from rest_framework import serializers
from .models import (
    LLMModel,
    ConversationAgent,
    AIConversation,
    AIMessage,
    AIMessageRating,
    AIMessageFlag,
    AIUsageAnalytics,
    AIModelPerformance,
    AIConversationSummary,
)


class LLMModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = LLMModel
        fields = [
            'id', 'name', 'model_type', 'model_id', 'api_endpoint',
            'max_tokens', 'temperature', 'top_p',
            'cost_per_input_token', 'cost_per_output_token',
            'status', 'daily_request_limit', 'rate_limit_per_minute',
            'supports_streaming', 'supports_function_calling',
            'supports_vision', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ConversationAgentSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(
        source='created_by.user.username', read_only=True
    )

    class Meta:
        model = ConversationAgent
        fields = [
            'id', 'name', 'agent_type', 'description', 'system_prompt',
            'preferred_model', 'temperature_override',
            'max_tokens_override', 'can_browse_web', 'can_analyze_images',
            'can_generate_images', 'can_code', 'avatar', 'created_by',
            'created_by_username', 'is_public', 'is_active',
            'total_conversations', 'total_messages', 'average_rating',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_by', 'total_conversations', 'total_messages',
            'average_rating', 'created_at', 'updated_at'
        ]


class AIConversationSerializer(serializers.ModelSerializer):
    agent_name = serializers.CharField(source='agent.name', read_only=True)
    user_username = serializers.CharField(
        source='user.user.username', read_only=True
    )

    class Meta:
        model = AIConversation
        fields = [
            'id', 'user', 'user_username', 'agent', 'agent_name',
            'title', 'status', 'total_messages', 'total_tokens_used',
            'total_cost', 'is_deleted', 'deleted_at', 'context_window',
            'auto_summarize', 'created_at', 'updated_at',
            'last_message_at'
        ]
        read_only_fields = [
            'id', 'user', 'total_messages', 'total_tokens_used',
            'total_cost', 'is_deleted', 'deleted_at', 'created_at',
            'updated_at', 'last_message_at'
        ]


class AIMessageSerializer(serializers.ModelSerializer):
    conversation_title = serializers.CharField(
        source='conversation.title', read_only=True
    )

    class Meta:
        model = AIMessage
        fields = [
            'id', 'conversation', 'conversation_title', 'role',
            'message_type', 'content', 'input_tokens', 'output_tokens',
            'cost', 'model_used', 'response_time', 'metadata',
            'attachments', 'is_error', 'error_message', 'is_deleted',
            'deleted_at', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


# Ratings
class AIMessageRatingUpsertSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIMessageRating
        fields = [
            'id', 'message', 'score', 'comment', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        user = self.context['request'].user.userprofile
        obj, _created = AIMessageRating.objects.update_or_create(
            message=validated_data['message'],
            user=user,
            defaults={
                'score': validated_data['score'],
                'comment': validated_data.get('comment', '')
            }
        )
        return obj


class AIMessageRatingSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(
        source='user.user.username', read_only=True
    )
    message_excerpt = serializers.CharField(
        source='message.content', read_only=True
    )

    class Meta:
        model = AIMessageRating
        fields = [
            'id', 'message', 'message_excerpt', 'score',
            'comment', 'user', 'user_username', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'created_at']


# Flags
class AIMessageFlagSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIMessageFlag
        fields = ['id', 'message', 'flag_type', 'comment', 'created_at']
        read_only_fields = ['id', 'created_at']


class AIMessageFlagDetailSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(
        source='user.user.username', read_only=True
    )
    message_excerpt = serializers.CharField(
        source='message.content', read_only=True
    )

    class Meta:
        model = AIMessageFlag
        fields = [
            'id', 'message', 'message_excerpt', 'flag_type', 'comment',
            'user', 'user_username', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'created_at']


class AIUsageAnalyticsSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(
        source='user.user.username', read_only=True
    )

    class Meta:
        model = AIUsageAnalytics
        fields = [
            'id', 'user', 'user_username', 'date', 'conversations_started',
            'messages_sent', 'tokens_consumed', 'total_cost',
            'total_time_spent', 'average_response_time',
            'image_analysis_requests', 'code_generation_requests',
            'web_browsing_requests', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class AIModelPerformanceSerializer(serializers.ModelSerializer):
    model_name = serializers.CharField(source='model.name', read_only=True)

    class Meta:
        model = AIModelPerformance
        fields = [
            'id', 'model', 'model_name', 'date', 'total_requests',
            'successful_requests', 'failed_requests',
            'average_response_time', 'average_tokens_per_request',
            'total_cost', 'average_user_rating', 'total_user_ratings',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class AIConversationSummarySerializer(serializers.ModelSerializer):
    conversation_title = serializers.CharField(
        source='conversation.title', read_only=True
    )

    class Meta:
        model = AIConversationSummary
        fields = [
            'id', 'conversation', 'conversation_title', 'title_suggestion',
            'summary_text', 'key_topics', 'message_count_at_summary',
            'summary_model', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
