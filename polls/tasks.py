from celery import shared_task
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta
from polls.models import Poll, PollOption, PollVote
from analytics.models import ErrorLog, SystemMetric


@shared_task
def handle_poll_expiration():
    """Handle expired polls and close them with notifications"""
    try:
        # Find polls that have expired but are still active
        expired_polls = Poll.objects.filter(
            expires_at__lte=timezone.now(),
            is_active=True,
            is_closed=False
        )

        updated_count = 0
        for poll in expired_polls:
            poll.is_active = False
            poll.is_closed = True
            poll.save(update_fields=['is_active', 'is_closed'])
            updated_count += 1

            # Create notification for poll author (if integrated with content)
            try:
                if hasattr(poll, 'post') and poll.post:
                    # Would need notification system integration
                    # For now, just log the event
                    question_preview = poll.question[:40]
                    vote_count = poll.total_votes
                    print(f"Poll expired: {question_preview}... ({vote_count} votes)")
            except Exception:
                pass  # Continue if notification fails

        return f"Closed {updated_count} expired polls"

    except Exception as e:
        ErrorLog.objects.create(
            level='error',
            message=f'Error handling poll expiration: {str(e)}',
            extra_data={'task': 'handle_poll_expiration'}
        )
        return f"Error handling poll expiration: {str(e)}"


@shared_task
def update_poll_counters():
    """Update vote counts for poll options"""
    try:
        active_polls = Poll.objects.filter(is_active=True)

        for poll in active_polls:
            # Update total votes
            total_votes = PollVote.objects.filter(poll=poll).count()

            # Update unique voters count
            unique_voters = PollVote.objects.filter(
                poll=poll
            ).values('voter').distinct().count()

            # Update poll counters
            poll.total_votes = total_votes
            poll.voters_count = unique_voters
            poll.save(update_fields=['total_votes', 'voters_count'])

            # Update individual option counters
            for option in poll.options.all():
                option_votes = PollVote.objects.filter(
                    poll=poll,
                    option=option
                ).count()
                option.votes_count = option_votes
                option.save(update_fields=['votes_count'])

        return f"Updated counters for {active_polls.count()} polls"

    except Exception as e:
        ErrorLog.objects.create(
            level='error',
            message=f'Error updating poll counters: {str(e)}',
            extra_data={'task': 'update_poll_counters'}
        )
        return f"Error: {str(e)}"


@shared_task
def analyze_poll_engagement():
    """Analyze poll engagement and update statistics"""
    try:
        # Get polls from the last 7 days
        recent_polls = Poll.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=7)
        )

        for poll in recent_polls:
            # Calculate engagement metrics
            total_votes = PollVote.objects.filter(
                option__poll=poll
            ).count()

            unique_voters = PollVote.objects.filter(
                option__poll=poll
            ).values('voter').distinct().count()

            # Update poll statistics
            poll.total_votes = total_votes
            poll.voters_count = unique_voters
            poll.save(update_fields=['total_votes', 'voters_count'])

        return f"Analyzed engagement for {recent_polls.count()} recent polls"

    except Exception as e:
        ErrorLog.objects.create(
            level='error',
            message=f'Error analyzing poll engagement: {str(e)}',
            extra_data={'task': 'analyze_poll_engagement'}
        )
        return f"Error: {str(e)}"


@shared_task
def generate_poll_analytics():
    """Generate daily analytics for polls"""
    try:
        today = timezone.now().date()

        # Count today's poll activity
        new_polls = Poll.objects.filter(created_at__date=today).count()
        new_votes = PollVote.objects.filter(created_at__date=today).count()

        # Store analytics (would need a PollAnalytics model)
        # For now, just log the metrics
        SystemMetric.objects.create(
            metric_type='daily_new_polls',
            value=new_polls,
            timestamp=timezone.now()
        )

        SystemMetric.objects.create(
            metric_type='daily_poll_votes',
            value=new_votes,
            timestamp=timezone.now()
        )

        return (f"Generated poll analytics: {new_polls} polls, "
                f"{new_votes} votes")

    except Exception as e:
        ErrorLog.objects.create(
            level='error',
            message=f'Error generating poll analytics: {str(e)}',
            extra_data={'task': 'generate_poll_analytics'}
        )
        return f"Error: {str(e)}"


@shared_task
def analyze_poll_option_performance():
    """Analyze performance of poll options to identify trending choices"""
    try:
        # Get active polls from the last 7 days
        recent_polls = Poll.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=7),
            is_active=True
        )

        high_performing_options = []
        low_performing_options = []

        for poll in recent_polls:
            if poll.total_votes == 0:
                continue

            options = poll.options.all().order_by('-votes_count')

            for option in options:
                vote_percentage = option.vote_percentage

                # High performing options (>60% for 2-option, >40% for 3+)
                option_count = poll.options.count()
                if option_count == 2:
                    threshold = 60
                elif option_count >= 3:
                    threshold = 40
                else:
                    threshold = 50

                if vote_percentage >= threshold and poll.total_votes >= 5:
                    high_performing_options.append({
                        'option_id': option.id,
                        'text': option.text[:50],
                        'percentage': vote_percentage,
                        'poll_id': poll.id,
                        'total_votes': poll.total_votes
                    })

                # Low performing options (< 10% with 10+ total votes)
                elif vote_percentage < 10 and poll.total_votes >= 10:
                    low_performing_options.append({
                        'option_id': option.id,
                        'text': option.text[:50],
                        'percentage': vote_percentage,
                        'poll_id': poll.id
                    })

        # Log analytics for high/low performing options
        SystemMetric.objects.create(
            metric_type='high_performing_poll_options',
            value=len(high_performing_options),
            timestamp=timezone.now(),
            additional_data={'options': high_performing_options[:10]}
        )

        SystemMetric.objects.create(
            metric_type='low_performing_poll_options',
            value=len(low_performing_options),
            timestamp=timezone.now(),
            additional_data={'options': low_performing_options[:10]}
        )

        return (f"Analyzed {recent_polls.count()} polls: "
                f"{len(high_performing_options)} high-performing, "
                f"{len(low_performing_options)} low-performing options")

    except Exception as e:
        ErrorLog.objects.create(
            level='error',
            message=f'Error analyzing poll option performance: {str(e)}',
            extra_data={'task': 'analyze_poll_option_performance'}
        )
        return f"Error: {str(e)}"


@shared_task
def cleanup_empty_poll_options():
    """Clean up poll options with no votes after 24+ hours"""
    try:
        # Find polls that have been active for at least 24 hours
        cutoff_time = timezone.now() - timedelta(hours=24)
        mature_polls = Poll.objects.filter(
            created_at__lte=cutoff_time,
            is_active=True
        )

        cleaned_options = 0
        for poll in mature_polls:
            # Only clean up if poll has at least 10 total votes and 4+ options
            if poll.total_votes >= 10 and poll.options.count() >= 4:
                empty_options = poll.options.filter(votes_count=0)

                for option in empty_options:
                    # Log the cleanup
                    print(f"Removing empty option: "
                          f"{option.text[:30]}... from poll {poll.id}")
                    option.delete()
                    cleaned_options += 1

        return f"Cleaned up {cleaned_options} empty poll options"

    except Exception as e:
        ErrorLog.objects.create(
            level='error',
            message=f'Error cleaning up empty poll options: {str(e)}',
            extra_data={'task': 'cleanup_empty_poll_options'}
        )
        return f"Error: {str(e)}"


@shared_task
def reorder_poll_options_by_popularity():
    """Reorder poll options by vote count for better UX in closed polls"""
    try:
        # Find recently closed polls (closed in last 24 hours)
        cutoff_time = timezone.now() - timedelta(hours=24)
        recently_closed_polls = Poll.objects.filter(
            is_closed=True,
            updated_at__gte=cutoff_time
        )

        reordered_polls = 0
        for poll in recently_closed_polls:
            # Skip if already ordered or no votes
            if poll.total_votes == 0:
                continue

            # Get options ordered by votes (descending)
            options = list(poll.options.all().order_by('-votes_count', 'id'))

            # Update order field to reflect vote ranking
            needs_reorder = False
            for index, option in enumerate(options):
                new_order = index + 1
                if option.order != new_order:
                    option.order = new_order
                    option.save(update_fields=['order'])
                    needs_reorder = True

            if needs_reorder:
                reordered_polls += 1

        return f"Reordered options for {reordered_polls} recently closed polls"

    except Exception as e:
        ErrorLog.objects.create(
            level='error',
            message=f'Error reordering poll options: {str(e)}',
            extra_data={'task': 'reorder_poll_options_by_popularity'}
        )
        return f"Error: {str(e)}"


@shared_task
def generate_poll_option_insights():
    """Generate insights about poll option patterns and user preferences"""
    try:
        # Analyze last 30 days of poll data
        cutoff_date = timezone.now() - timedelta(days=30)
        recent_polls = Poll.objects.filter(created_at__gte=cutoff_date)

        # Option length analysis
        short_options = 0
        long_options = 0

        for option in PollOption.objects.filter(poll__in=recent_polls):
            text_length = len(option.text) if option.text else 0
            if text_length <= 20:
                short_options += 1
            elif text_length > 50:
                long_options += 1

        # Most common option count per poll
        option_counts = {}
        for poll in recent_polls:
            count = poll.options.count()
            option_counts[count] = option_counts.get(count, 0) + 1

        most_common_option_count = (
            max(option_counts.items(), key=lambda x: x[1])[0]
            if option_counts else 0
        )        # Options with images vs text-only
        options_with_images = PollOption.objects.filter(
            poll__in=recent_polls,
            image__isnull=False
        ).count()

        total_options = PollOption.objects.filter(
            poll__in=recent_polls
        ).count()
        text_only_options = total_options - options_with_images

        # Store insights
        insights_data = {
            'short_options': short_options,
            'long_options': long_options,
            'most_common_option_count': most_common_option_count,
            'options_with_images': options_with_images,
            'text_only_options': text_only_options,
            'total_options_analyzed': total_options
        }

        SystemMetric.objects.create(
            metric_type='poll_option_insights',
            value=total_options,
            timestamp=timezone.now(),
            additional_data=insights_data
        )

        return (f"Generated insights for {total_options} options across "
                f"{recent_polls.count()} polls")

    except Exception as e:
        ErrorLog.objects.create(
            level='error',
            message=f'Error generating poll option insights: {str(e)}',
            extra_data={'task': 'generate_poll_option_insights'}
        )
        return f"Error: {str(e)}"
