from celery import shared_task
from django.utils import timezone
from django.db.models import Count, Avg
from datetime import timedelta
from ai_conversations.models import (
    AIConversation, AIMessage, LLMModel, AIUsageAnalytics,
    AIModelPerformance, ConversationAgent, AIConversationSummary,
    AIMessageRating
)
from analytics.models import ErrorLog
from accounts.models import UserProfile


@shared_task
def summarize_deleted_ai_conversations():
    """Summarize and analyze statistics about deleted AIConversations."""
    from datetime import date, timedelta
    try:
        today = date.today()
        # Get all soft-deleted conversations
        deleted_conversations = AIConversation.objects.filter(is_deleted=True)
        total_deleted = deleted_conversations.count()

        # Breakdown by user
        user_deletion_stats = (
            deleted_conversations.values('user')
            .annotate(deleted_count=Count('id'))
            .order_by('-deleted_count')
        )

        # Deletion trends: count per day for last 30 days
        last_30_days = today - timedelta(days=30)
        daily_deletion_trend = (
            deleted_conversations.filter(deleted_at__gte=last_30_days)
            .extra({'day': "date(deleted_at)"})
            .values('day')
            .annotate(count=Count('id'))
            .order_by('day')
        )

        # Most common agents in deleted conversations
        agent_stats = (
            deleted_conversations.values('agent__name')
            .annotate(count=Count('id'))
            .order_by('-count')[:5]
        )

        # Compose summary
        summary = {
            'total_deleted': total_deleted,
            'user_deletion_stats': list(user_deletion_stats),
            'daily_deletion_trend': list(daily_deletion_trend),
            'top_agents_in_deleted': list(agent_stats),
        }

        # Optionally, log or store summary in ErrorLog for review
        # ErrorLog.objects.create(
        #     level='info',
        #     message='Deleted AIConversation statistics',
        #     extra_data={'summary': summary, 'task': 'summarize_deleted_ai_conversations'}
        # )
        return summary
    except Exception as e:
        ErrorLog.objects.create(
            level='error',
            message=f'Error summarizing deleted AIConversations: {str(e)}',
            extra_data={'task': 'summarize_deleted_ai_conversations'}
        )
        return f"Error summarizing deleted AIConversations: {str(e)}"


@shared_task
def update_ai_usage_analytics():
    """Update daily AI usage analytics for all users."""
    from datetime import date
    today = date.today()

    try:
        users_with_conversations = UserProfile.objects.filter(
            ai_conversations__messages__created_at__date=today,
            ai_conversations__is_deleted=False,
            ai_conversations__messages__is_deleted=False
        ).distinct()

        for user in users_with_conversations:
            # Get today's messages (exclude soft-deleted)
            today_messages = AIMessage.objects.filter(
                conversation__user=user,
                created_at__date=today,
                role='user',
                is_deleted=False
            )

            # Calculate analytics
            conversations_started = AIConversation.objects.filter(
                user=user,
                created_at__date=today,
                is_deleted=False
            ).count()

            messages_sent = today_messages.count()
            tokens_consumed = sum(
                msg.input_tokens + msg.output_tokens
                for msg in today_messages
            )
            total_cost = sum(msg.cost for msg in today_messages)

            # Feature usage counts
            image_analysis_requests = today_messages.filter(
                message_type='image'
            ).count()

            code_generation_requests = today_messages.filter(
                content__icontains='code'
            ).count()

            # Create or update analytics record
            analytics, created = AIUsageAnalytics.objects.get_or_create(
                user=user,
                date=today,
                defaults={
                    'conversations_started': conversations_started,
                    'messages_sent': messages_sent,
                    'tokens_consumed': tokens_consumed,
                    'total_cost': total_cost,
                    'image_analysis_requests': image_analysis_requests,
                    'code_generation_requests': code_generation_requests,
                }
            )

            if not created:
                analytics.conversations_started = conversations_started
                analytics.messages_sent = messages_sent
                analytics.tokens_consumed = tokens_consumed
                analytics.total_cost = total_cost
                analytics.image_analysis_requests = image_analysis_requests
                analytics.code_generation_requests = code_generation_requests
                analytics.save()

        return f"Updated AI usage analytics for {users_with_conversations.count()} users"

    except Exception as e:
        ErrorLog.objects.create(
            level='error',
            message=f'Error updating AI usage analytics: {str(e)}',
            extra_data={'task': 'update_ai_usage_analytics'}
        )
        return f"Error updating AI usage analytics: {str(e)}"


@shared_task
def update_ai_model_performance():
    """Update daily performance metrics for AI models."""
    from datetime import date
    today = date.today()

    try:
        active_models = LLMModel.objects.filter(status='active')

        for model in active_models:
            # Get today's messages using this model (exclude soft-deleted)
            today_messages = AIMessage.objects.filter(
                model_used=model,
                created_at__date=today,
                is_deleted=False
            )

            total_requests = today_messages.count()
            successful_requests = today_messages.filter(is_error=False).count()
            failed_requests = today_messages.filter(is_error=True).count()

            # Calculate averages
            successful_messages = today_messages.filter(is_error=False)
            average_response_time = 0
            average_tokens_per_request = 0
            total_cost = 0

            if successful_messages.exists():
                response_times = [
                    msg.response_time for msg in successful_messages
                    if msg.response_time
                ]
                if response_times:
                    average_response_time = sum(response_times) / len(response_times)

                token_counts = [
                    msg.input_tokens + msg.output_tokens
                    for msg in successful_messages
                ]
                if token_counts:
                    average_tokens_per_request = sum(token_counts) / len(token_counts)

                total_cost = sum(msg.cost for msg in successful_messages)

            # Get user ratings for this model's messages (exclude soft-deleted)
            ratings = AIMessageRating.objects.filter(
                message__model_used=model,
                message__created_at__date=today,
                message__is_deleted=False
            )

            average_user_rating = 0
            total_user_ratings = ratings.count()

            if total_user_ratings > 0:
                average_user_rating = ratings.aggregate(
                    avg_rating=Avg('score')
                )['avg_rating'] or 0

            # Create or update performance record
            performance, created = AIModelPerformance.objects.get_or_create(
                model=model,
                date=today,
                defaults={
                    'total_requests': total_requests,
                    'successful_requests': successful_requests,
                    'failed_requests': failed_requests,
                    'average_response_time': average_response_time,
                    'average_tokens_per_request': average_tokens_per_request,
                    'total_cost': total_cost,
                    'average_user_rating': average_user_rating,
                    'total_user_ratings': total_user_ratings,
                }
            )

            if not created:
                performance.total_requests = total_requests
                performance.successful_requests = successful_requests
                performance.failed_requests = failed_requests
                performance.average_response_time = average_response_time
                performance.average_tokens_per_request = average_tokens_per_request
                performance.total_cost = total_cost
                performance.average_user_rating = average_user_rating
                performance.total_user_ratings = total_user_ratings
                performance.save()

        return f"Updated performance metrics for {active_models.count()} AI models"

    except Exception as e:
        ErrorLog.objects.create(
            level='error',
            message=f'Error updating AI model performance: {str(e)}',
            extra_data={'task': 'update_ai_model_performance'}
        )
        return f"Error updating AI model performance: {str(e)}"


@shared_task
def generate_conversation_summaries():
    """Generate summaries for conversations that need them."""
    try:
        conversations_to_summarize = AIConversation.objects.filter(
            auto_summarize=True,
            total_messages__gte=10,
            summary__isnull=True,
            is_deleted=False
        )

        summarized_count = 0

        for conversation in conversations_to_summarize:
            messages = conversation.messages.filter(is_deleted=False).order_by('created_at')

            # Create a simple summary
            message_count = messages.count()
            user_messages = messages.filter(role='user').count()
            assistant_messages = messages.filter(role='assistant').count()

            # Generate summary text
            summary_text = f"Conversation with {conversation.agent.name} containing {message_count} messages. "
            summary_text += f"User sent {user_messages} messages, assistant replied {assistant_messages} times."

            # Extract key topics (simplified implementation)
            content_words = []
            for message in messages.filter(role='user')[:5]:  # Look at first 5 user messages
                words = message.content.lower().split()
                content_words.extend([word for word in words if len(word) > 4])

            # Get most common words as topics
            from collections import Counter
            common_words = Counter(content_words).most_common(5)
            key_topics = [word for word, count in common_words]

            # Create summary
            AIConversationSummary.objects.create(
                conversation=conversation,
                title_suggestion=f"Discussion about {', '.join(key_topics[:2]) if key_topics else 'various topics'}",
                summary_text=summary_text,
                key_topics=key_topics,
                message_count_at_summary=message_count
            )

            summarized_count += 1

        return f"Generated summaries for {summarized_count} conversations"

    except Exception as e:
        ErrorLog.objects.create(
            level='error',
            message=f'Error generating conversation summaries: {str(e)}',
            extra_data={'task': 'generate_conversation_summaries'}
        )
        return f"Error generating conversation summaries: {str(e)}"


@shared_task
def cleanup_old_ai_data():
    """Clean up old AI conversation data based on retention policies."""
    try:
        # Delete old analytics data (keep 1 year)
        old_analytics_date = timezone.now().date() - timedelta(days=365)
        old_analytics = AIUsageAnalytics.objects.filter(date__lt=old_analytics_date)
        analytics_count = old_analytics.count()
        old_analytics.delete()

        # Delete old performance data (keep 1 year)
        old_performance = AIModelPerformance.objects.filter(date__lt=old_analytics_date)
        performance_count = old_performance.count()
        old_performance.delete()

        # Archive very old conversations (older than 2 years)
        old_conversation_date = timezone.now() - timedelta(days=730)
        old_conversations = AIConversation.objects.filter(
            last_message_at__lt=old_conversation_date,
            status='active',
            is_deleted=False
        )
        archived_count = old_conversations.count()
        old_conversations.update(status='archived')

        return f"Cleaned up {analytics_count} analytics records, {performance_count} performance records, archived {archived_count} conversations"

    except Exception as e:
        ErrorLog.objects.create(
            level='error',
            message=f'Error cleaning up old AI data: {str(e)}',
            extra_data={'task': 'cleanup_old_ai_data'}
        )
        return f"Error cleaning up old AI data: {str(e)}"


@shared_task
def update_agent_statistics():
    """Update conversation agent statistics"""
    try:
        agents = ConversationAgent.objects.all()

        for agent in agents:
            # Count conversations using this agent
            conversation_count = AIConversation.objects.filter(
                agent=agent,
                is_deleted=False
            ).count()

            # Update agent stats
            if hasattr(agent, 'total_conversations'):
                agent.total_conversations = conversation_count
                agent.save()

        return f"Updated statistics for {agents.count()} conversation agents"

    except Exception as e:
        ErrorLog.objects.create(
            level='error',
            message=f'Error updating agent statistics: {str(e)}',
            extra_data={'task': 'update_agent_statistics'}
        )
        return f"Error: {str(e)}"
