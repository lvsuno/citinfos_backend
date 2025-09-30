"""
Real-time notification signals for polls app.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

try:
    from .models import Poll, PollVote
    from notifications.realtime import send_poll_notification, send_poll_result_notification

    @receiver(post_save, sender=PollVote)
    def send_poll_vote_notification(sender, instance, created, **kwargs):
        """Send real-time notification when someone votes on a poll."""
        if created:
            try:
                # Get poll creator from the post
                poll_creator = instance.poll.post.author

                # Don't notify self-votes
                if poll_creator != instance.voter.profile:
                    send_poll_notification(
                        user_profile=poll_creator,
                        notification_type='poll_vote',
                        data={
                            'title': 'New vote on your poll',
                            'message': f'@{instance.voter.profile.user.username} voted on your poll.',
                            'poll_id': str(instance.poll.id),
                            'voter_username': instance.voter.profile.user.username,
                            'poll_title': getattr(instance.poll, 'title', 'Your poll')
                        }
                    )

                # Check if poll has reached a milestone (every 10 votes)
                total_votes = PollVote.objects.filter(
                    poll=instance.poll,
                    is_deleted=False
                ).count()

                if total_votes > 0 and total_votes % 10 == 0:
                    send_poll_result_notification(
                        poll_creator=poll_creator,
                        poll_title=getattr(instance.poll, 'title', 'Your poll'),
                        total_votes=total_votes
                    )

            except Exception as e:
                print(f"Error sending poll vote notification: {str(e)}")

    @receiver(post_save, sender=Poll)
    def send_poll_created_notification(sender, instance, created, **kwargs):
        """Send real-time notification when a poll is created."""
        if created:
            try:
                # Notify followers of the poll creator
                followers = instance.post.author.followers.filter(
                    status='approved',
                    is_deleted=False
                )

                for follow_relationship in followers[:50]:  # Limit to 50 to avoid spam
                    follower = follow_relationship.follower

                    send_poll_notification(
                        user_profile=follower,
                        notification_type='poll_created',
                        data={
                            'title': f'New poll by @{instance.post.author.user.username}',
                            'message': f'@{instance.post.author.user.username} created a new poll: {getattr(instance, "title", "Check it out!")}',
                            'poll_id': str(instance.id),
                            'creator_username': instance.post.author.user.username,
                            'poll_title': getattr(instance, 'title', 'New poll')
                        }
                    )

            except Exception as e:
                print(f"Error sending poll created notification: {str(e)}")

except ImportError:
    # Polls models not available - skip signal setup
    pass
