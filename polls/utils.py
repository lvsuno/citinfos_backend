"""Poll utility functions for analytics, validation, and data processing."""

from datetime import timedelta
from django.utils import timezone
from django.db.models import Count
from polls.models import Poll, PollVote


def calculate_poll_engagement_score(poll):
    """
    Calculate engagement score for a poll.

    This function is useful for:
    - Ranking polls by engagement
    - Analytics and reporting
    - Recommendation algorithms
    """
    try:
        # For polls integrated with content app
        if hasattr(poll, 'post') and poll.post:
            views_count = getattr(poll.post, 'views_count', 0)
            comments_count = getattr(poll.post, 'comments_count', 0)
            shares_count = getattr(poll.post, 'shares_count', 0)
        else:
            # Fallback for standalone polls
            # Assume at least voters viewed for standalone polls
            views_count = max(poll.total_votes, 1)
            comments_count = 0
            shares_count = 0

        if views_count == 0:
            return 0

        # Basic engagement metrics
        vote_rate = poll.total_votes / views_count
        comment_rate = comments_count / views_count if views_count > 0 else 0
        share_rate = shares_count / views_count if views_count > 0 else 0

        # Weight different actions
        engagement_score = (
            vote_rate * 3.0 +      # Voting is the primary action
            comment_rate * 2.0 +   # Comments show deeper engagement
            share_rate * 4.0       # Shares extend reach
        )

        # Bonus for multiple choice polls (more complex)
        if poll.multiple_choice:
            engagement_score *= 1.2

        # Time factor (newer polls get slight boost)
        age_hours = (timezone.now() - poll.created_at).total_seconds() / 3600
        if age_hours < 24:
            time_factor = 1.1
        elif age_hours < 72:
            time_factor = 1.0
        else:
            time_factor = 0.95

        return min(engagement_score * time_factor, 10.0)  # Cap at 10

    except Exception:
        return 0.0


def get_poll_results_summary(poll):
    """
    Get comprehensive poll results summary.

    Returns detailed poll data including:
    - Vote counts and percentages
    - Option details
    - Engagement metrics
    """
    try:
        options_data = []

        for option in poll.options.all().order_by('order'):
            options_data.append({
                'id': option.id,
                'text': option.text,
                'votes': option.votes_count,
                'percentage': option.vote_percentage,
                'order': option.order,
            })

        return {
            'poll_id': poll.id,
            'question': poll.question,
            'total_votes': poll.total_votes,
            'unique_voters': poll.voters_count,
            'is_active': poll.is_active,
            'is_expired': poll.is_expired,
            'created_at': poll.created_at,
            'expires_at': poll.expires_at,
            'options': options_data,
            'engagement_score': calculate_poll_engagement_score(poll),
        }

    except Exception:
        return {
            'poll_id': poll.id,
            'question': poll.question,
            'error': 'Failed to generate summary'
        }


def get_user_poll_analytics(user, days=30):
    """
    Get poll analytics for a specific user.

    Provides insights into:
    - Polls created by user
    - Voting activity
    - Engagement metrics
    """
    try:
        cutoff_date = timezone.now() - timedelta(days=days)

        # Polls created by user (if integrated with content app)
        if hasattr(Poll, 'post'):
            user_polls = Poll.objects.filter(
                post__author=user,
                created_at__gte=cutoff_date
            )
        else:
            # For standalone polls, need to add creator field or different logic
            user_polls = Poll.objects.filter(created_at__gte=cutoff_date)

        # Votes cast by user
        user_votes = PollVote.objects.filter(
            voter=user,
            created_at__gte=cutoff_date
        )

        # Analytics summary
        total_polls_created = user_polls.count()
        total_votes_received = sum(poll.total_votes for poll in user_polls)
        total_votes_cast = user_votes.count()

        # Average engagement for user's polls
        avg_engagement = 0
        if total_polls_created > 0:
            engagement_scores = [
                calculate_poll_engagement_score(poll) for poll in user_polls
            ]
            avg_engagement = sum(engagement_scores) / len(engagement_scores)

        # Most popular poll
        most_popular_poll = user_polls.order_by('-total_votes').first()

        return {
            'user_id': user.id,
            'period_days': days,
            'polls_created': total_polls_created,
            'votes_received': total_votes_received,
            'votes_cast': total_votes_cast,
            'avg_engagement_score': round(avg_engagement, 2),
            'most_popular_poll': {
                'id': most_popular_poll.id if most_popular_poll else None,
                'question': most_popular_poll.question if most_popular_poll else None,
                'votes': most_popular_poll.total_votes if most_popular_poll else 0,
            } if most_popular_poll else None,
        }

    except Exception:
        return {
            'user_id': user.id,
            'period_days': days,
            'error': 'Failed to generate analytics'
        }


def get_trending_polls(limit=10, hours=24):
    """
    Get trending polls based on recent engagement.

    Identifies popular polls with recent activity.
    """
    try:
        cutoff_time = timezone.now() - timedelta(hours=hours)

        # Get polls with recent activity
        trending_polls = Poll.objects.filter(
            is_active=True,
            created_at__gte=cutoff_time
        ).annotate(
            recent_votes=Count('votes', distinct=True)
        ).order_by('-recent_votes', '-total_votes')[:limit]

        return [get_poll_results_summary(poll) for poll in trending_polls]

    except Exception:
        return []


def validate_poll_vote(user, poll, option):
    """
    Validate if a user can vote on a poll option.

    Essential for:
    - Vote validation in views
    - API endpoints
    - Preventing duplicate/invalid votes

    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        # Check if poll is active
        if not poll.is_active or poll.is_closed:
            return False, "Poll is not active"

        # Check if poll has expired
        if poll.is_expired:
            return False, "Poll has expired"

        # Check if option belongs to this poll
        if option.poll_id != poll.id:
            return False, "Option does not belong to this poll"

        # Check for existing vote
        existing_vote = PollVote.objects.filter(
            poll=poll,
            voter=user,
            option=option
        ).exists()

        if existing_vote:
            return False, "You have already voted for this option"

        # For single choice polls, check if user already voted
        if not poll.multiple_choice:
            has_voted = PollVote.objects.filter(
                poll=poll,
                voter=user
            ).exists()

            if has_voted:
                return False, "You have already voted on this poll"

        return True, "Vote is valid"

    except Exception as e:
        return False, f"Validation error: {str(e)}"


def update_poll_counters(poll):
    """
    Update all counters for a specific poll.

    Essential for:
    - Maintaining data consistency
    - Performance optimization
    - Real-time updates

    Updates:
    - Total votes count
    - Unique voters count
    - Individual option vote counts
    """
    try:
        # Update total votes
        poll.total_votes = PollVote.objects.filter(poll=poll).count()

        # Update unique voters
        poll.voters_count = PollVote.objects.filter(
            poll=poll
        ).values('voter').distinct().count()

        poll.save(update_fields=['total_votes', 'voters_count'])

        # Update option counters
        for option in poll.options.all():
            option.votes_count = PollVote.objects.filter(
                poll=poll,
                option=option
            ).count()
            option.save(update_fields=['votes_count'])

        return poll

    except Exception as e:
        # Log error but don't break the application
        print(f"Error updating poll counters: {e}")
        return poll


def get_poll_participation_rate(poll):
    """
    Calculate participation rate if poll is linked to content.

    Useful for measuring poll effectiveness.
    """
    try:
        if hasattr(poll, 'post') and poll.post:
            views = getattr(poll.post, 'views_count', 0)
            if views > 0:
                return round((poll.voters_count / views) * 100, 2)

        # Fallback: assume 100% participation rate
        return 100.0 if poll.voters_count > 0 else 0.0

    except Exception:
        return 0.0


def close_expired_polls():
    """
    Utility function to close expired polls.

    Can be used in:
    - Management commands
    - Celery tasks
    - Cron jobs
    """
    try:
        expired_polls = Poll.objects.filter(
            expires_at__lt=timezone.now(),
            is_active=True,
            is_closed=False
        )

        closed_count = 0
        for poll in expired_polls:
            poll.is_active = False
            poll.is_closed = True
            poll.save(update_fields=['is_active', 'is_closed'])
            closed_count += 1

        return closed_count

    except Exception as e:
        print(f"Error closing expired polls: {e}")
        return 0


def get_poll_vote_distribution(poll):
    """
    Get vote distribution analysis for a poll.

    Returns detailed statistics about voting patterns.
    """
    try:
        if poll.total_votes == 0:
            return {
                'total_votes': 0,
                'distribution': [],
                'winner': None,
                'is_tie': False
            }

        options_data = []
        max_votes = 0
        winners = []

        for option in poll.options.all().order_by('-votes_count'):
            votes = option.votes_count
            percentage = option.vote_percentage

            if votes > max_votes:
                max_votes = votes
                winners = [option]
            elif votes == max_votes and max_votes > 0:
                winners.append(option)

            options_data.append({
                'option_id': option.id,
                'text': option.text,
                'votes': votes,
                'percentage': percentage,
                'is_winner': votes == max_votes if max_votes > 0 else False
            })

        return {
            'total_votes': poll.total_votes,
            'unique_voters': poll.voters_count,
            'distribution': options_data,
            'winner': winners[0].text if len(winners) == 1 else None,
            'winners': [w.text for w in winners] if len(winners) > 1 else None,
            'is_tie': len(winners) > 1,
            'participation_rate': get_poll_participation_rate(poll)
        }

    except Exception:
        return {
            'total_votes': poll.total_votes,
            'error': 'Failed to calculate distribution'
        }
