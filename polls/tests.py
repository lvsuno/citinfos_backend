"""
Comprehensive tests for polls app covering URLs, CRUD operations, and tasks.
"""
from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from polls.models import Poll, PollOption, PollVote, PollVoter
from polls.tasks import (
    handle_poll_expiration,
    update_poll_counters,
    analyze_poll_engagement,
    generate_poll_analytics,
    analyze_poll_option_performance,
    cleanup_empty_poll_options,
    reorder_poll_options_by_popularity,
    generate_poll_option_insights
)
from content.models import Post
from accounts.models import UserProfile
from django.utils import timezone
from core.jwt_test_mixin import JWTAuthTestMixin


class PollModelTest(TestCase):
    """Test Poll model functionality."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.user_profile, _ = UserProfile.objects.get_or_create(user=self.user)
        UserProfile.objects.filter(user=self.user).update(
            phone_number='+15550000401',
            date_of_birth='1990-01-01',
            is_verified=True,
            last_verified_at=timezone.now()
        )
        self.user_profile.refresh_from_db()
        self.post = Post.objects.create(
            author=self.user_profile,
            content='Test poll post',
            post_type='poll'
        )

    def test_create_poll(self):
        """Test creating a poll."""
        poll = Poll.objects.create(
            post=self.post,
            question='What is your favorite color?',
            multiple_choice=False,
            anonymous_voting=False,
            expires_at=timezone.now() + timedelta(days=7)
        )
        self.assertEqual(poll.question, 'What is your favorite color?')
        self.assertEqual(poll.total_votes, 0)
        self.assertEqual(poll.voters_count, 0)
        self.assertTrue(poll.is_active)
        self.assertFalse(poll.is_closed)

    def test_poll_str_method(self):
        """Test poll string representation."""
        poll = Poll.objects.create(
            post=self.post,
            question='Test Question?',
            expires_at=timezone.now() + timedelta(days=7)
        )
        self.assertEqual(str(poll), 'Poll: Test Question?')

    def test_poll_unique_voters_property(self):
        """Test unique_voters relationship."""
        poll = Poll.objects.create(
            post=self.post,
            question='Test Question?',
            expires_at=timezone.now() + timedelta(days=7)
        )
        option = PollOption.objects.create(
            poll=poll,
            text='Option 1',
            order=1
        )

        # Create vote and voter record
        PollVote.objects.create(
            poll=poll,
            option=option,
            voter=self.user
        )
        PollVoter.objects.create(
            poll=poll,
            voter=self.user
        )

        unique_voters = poll.unique_voters.all()
        self.assertEqual(unique_voters.count(), 1)
        self.assertEqual(unique_voters.first().voter, self.user)

    def test_poll_is_expired_property(self):
        """Test is_expired property."""
        # Future expiry
        future_poll = Poll.objects.create(
            post=self.post,
            question='Future Poll?',
            expires_at=timezone.now() + timedelta(days=1)
        )
        self.assertFalse(future_poll.is_expired)

        # Past expiry - create a new post for this poll
        past_post = Post.objects.create(
            author=self.user_profile,
            content='Test past poll post',
            post_type='poll'
        )
        past_poll = Poll.objects.create(
            post=past_post,
            question='Past Poll?',
            expires_at=timezone.now() - timedelta(days=1)
        )
        self.assertTrue(past_poll.is_expired)


class PollOptionModelTest(TestCase):
    """Test PollOption model functionality."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.user_profile, _ = UserProfile.objects.get_or_create(user=self.user)
        UserProfile.objects.filter(user=self.user).update(
            phone_number='+15550000402',
            date_of_birth='1990-01-01',
            is_verified=True,
            last_verified_at=timezone.now()
        )
        self.user_profile.refresh_from_db()
        self.post = Post.objects.create(
            author=self.user_profile,
            content='Test poll post',
            post_type='poll'
        )
        self.poll = Poll.objects.create(
            post=self.post,
            question='Test Question?',
            expires_at=timezone.now() + timedelta(days=7)
        )

    def test_create_poll_option(self):
        """Test creating a poll option."""
        option = PollOption.objects.create(
            poll=self.poll,
            text='Option 1',
            order=1
        )
        self.assertEqual(option.text, 'Option 1')
        self.assertEqual(option.order, 1)
        self.assertEqual(option.votes_count, 0)

    def test_poll_option_str_method(self):
        """Test poll option string representation."""
        option = PollOption.objects.create(
            poll=self.poll,
            text='Test Option',
            order=1
        )
        self.assertEqual(str(option), 'Test Question? - Test Option')


class PollVoteModelTest(TestCase):
    """Test PollVote model functionality."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.user_profile, _ = UserProfile.objects.get_or_create(user=self.user)
        UserProfile.objects.filter(user=self.user).update(
            phone_number='+15550000403',
            date_of_birth='1990-01-01',
            is_verified=True,
            last_verified_at=timezone.now()
        )
        self.user_profile.refresh_from_db()
        self.post = Post.objects.create(
            author=self.user_profile,
            content='Test poll post',
            post_type='poll'
        )
        self.poll = Poll.objects.create(
            post=self.post,
            question='Test Question?',
            multiple_choice=False,
            expires_at=timezone.now() + timedelta(days=7)
        )
        self.option = PollOption.objects.create(
            poll=self.poll,
            text='Option 1',
            order=1
        )

    def test_create_poll_vote(self):
        """Test creating a poll vote."""
        vote = PollVote.objects.create(
            poll=self.poll,
            option=self.option,
            voter=self.user,
            ip_address='127.0.0.1',
            user_agent='TestAgent'
        )
        self.assertEqual(vote.poll, self.poll)
        self.assertEqual(vote.option, self.option)
        self.assertEqual(vote.voter, self.user)
        self.assertEqual(vote.ip_address, '127.0.0.1')

    def test_poll_vote_str_method(self):
        """Test poll vote string representation."""
        vote = PollVote.objects.create(
            poll=self.poll,
            option=self.option,
            voter=self.user
        )
        expected = f"{self.user.username} voted for Option 1"
        self.assertEqual(str(vote), expected)


class PollAPITest(JWTAuthTestMixin, APITestCase):
    """Test Poll API endpoints with JWT authentication."""

    def setUp(self):
        """Set up test data."""
        # Create test users
        self.user1 = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password='testpass123'
        )
        self.user1_profile, _ = UserProfile.objects.get_or_create(user=self.user1)
        UserProfile.objects.filter(user=self.user1).update(
            phone_number='+15550000404',
            date_of_birth='1990-01-01',
            is_verified=True,
            last_verified_at=timezone.now()
        )
        self.user1_profile.refresh_from_db()

        self.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )
        self.user2_profile, _ = UserProfile.objects.get_or_create(user=self.user2)
        UserProfile.objects.filter(user=self.user2).update(
            phone_number='+15550222222',
            date_of_birth='1991-02-02',
            is_verified=True,
            last_verified_at=timezone.now()
        )
        self.user2_profile.refresh_from_db()

        # JWT tokens for new authentication flow
        self.jwt_token1 = self._create_jwt_token_with_session(self.user1)
        self.jwt_token2 = self._create_jwt_token_with_session(self.user2)

        self.post = Post.objects.create(
            author=self.user1_profile,
            content='Test poll post',
            post_type='poll'
        )
        self.poll = Poll.objects.create(
            post=self.post,
            question='Test Question?',
            expires_at=timezone.now() + timedelta(days=7)
        )
        self.option1 = PollOption.objects.create(
            poll=self.poll,
            text='Option 1',
            order=1
        )
        self.option2 = PollOption.objects.create(
            poll=self.poll,
            text='Option 2',
            order=2
        )

    def test_list_polls_unauthenticated(self):
        """Test listing polls without authentication."""
        url = reverse('poll-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_polls_authenticated(self):
        """Test listing polls with JWT authentication."""
        self.authenticate_user1()
        url = reverse('poll-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_poll_authenticated(self):
        """Test creating a poll with JWT authentication."""
        self.authenticate_user1()
        url = reverse('poll-list')
        data = {
            'question': 'New Poll Question?',
            'multiple_choice': False,
            'anonymous_voting': False,
            'expires_at': (timezone.now() + timedelta(days=7)).isoformat()
        }
        response = self.client.post(url, data, format='json')
        if response.status_code != status.HTTP_201_CREATED:
            print("API Response Error:", response.status_code, response.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_poll_unauthenticated(self):
        """Test creating a poll without authentication."""
        url = reverse('poll-list')
        data = {
            'question': 'New Poll Question?',
            'multiple_choice': False,
            'anonymous_voting': False,
            'expires_at': (timezone.now() + timedelta(days=7)).isoformat()
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_vote_in_poll_authenticated(self):
        """Test voting in a poll with JWT authentication."""
        self.authenticate_user1()
        url = reverse('poll-vote', kwargs={'pk': self.poll.pk})
        data = {'option_id': self.option1.pk}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_vote_in_poll_unauthenticated(self):
        """Test voting in a poll without authentication."""
        url = reverse('poll-vote', kwargs={'pk': self.poll.pk})
        data = {'option_id': self.option1.pk}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_close_poll_owner(self):
        """Test closing poll by owner with JWT authentication."""
        self.authenticate_user1()
        url = reverse('poll-close', kwargs={'pk': self.poll.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_close_poll_non_owner(self):
        """Test closing poll by non-owner should fail."""
        self.authenticate_user2()  # Different user
        url = reverse('poll-close', kwargs={'pk': self.poll.pk})
        response = self.client.post(url)
        # Should return 403 Forbidden or 404 Not Found depending on permissions
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_jwt_token_contains_session_id(self):
        """Test that JWT tokens contain session ID claims."""
        token_data = self.jwt_token1
        # This test verifies the JWT token structure
        self.assertIn('session_id', token_data)
        self.assertIn('access', token_data)
        self.assertIn('refresh', token_data)


class PollTaskTest(TestCase):
    """Test poll-related Celery tasks."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.user_profile, _ = UserProfile.objects.get_or_create(user=self.user)
        UserProfile.objects.filter(user=self.user).update(
            phone_number='+15550223333',
            date_of_birth='1990-03-03',
            is_verified=True,
            last_verified_at=timezone.now()
        )
        self.user_profile.refresh_from_db()
            author=self.user_profile,
            content='Test poll post',
            post_type='poll'
        )

    @patch('polls.tasks.ErrorLog.objects.create')
    def test_handle_poll_expiration(self, mock_error):
        """Test poll expiration handling task."""
        # Create expired poll
        expired_poll = Poll.objects.create(
            post=self.post,
            question='Expired Poll?',
            expires_at=timezone.now() - timedelta(hours=1),
            is_active=True,
            is_closed=False
        )

        result = handle_poll_expiration()

        # Check that expired poll was closed
        expired_poll.refresh_from_db()
        self.assertFalse(expired_poll.is_active)
        self.assertTrue(expired_poll.is_closed)
        self.assertEqual(result, "Closed 1 expired polls")

    @patch('polls.tasks.ErrorLog.objects.create')
    def test_update_poll_counters(self, mock_error):
        """Test poll counter update task."""
        poll = Poll.objects.create(
            post=self.post,
            question='Test Poll?',
            expires_at=timezone.now() + timedelta(days=7),
            is_active=True
        )

        option = PollOption.objects.create(
            poll=poll,
            text='Option 1',
            order=1
        )

        # Create vote
        PollVote.objects.create(poll=poll, option=option, voter=self.user)

        result = update_poll_counters()

        # Check updated counters
        poll.refresh_from_db()
        option.refresh_from_db()

        self.assertEqual(poll.total_votes, 1)
        self.assertEqual(option.votes_count, 1)
        self.assertIn("Updated counters for", result)

    @patch('polls.tasks.SystemMetric.objects.create')
    def test_generate_poll_analytics(self, mock_metric):
        """Test poll analytics generation task."""
        # Create poll for today
        poll = Poll.objects.create(
            post=self.post,
            question='Today Poll?',
            expires_at=timezone.now() + timedelta(days=7),
            created_at=timezone.now()
        )

        option = PollOption.objects.create(
            poll=poll,
            text='Option 1',
            order=1
        )

        # Create vote for today
        PollVote.objects.create(
            poll=poll,
            option=option,
            voter=self.user,
            created_at=timezone.now()
        )

        result = generate_poll_analytics()

        # Check that metrics were created
        self.assertEqual(mock_metric.call_count, 2)
        self.assertIn("Generated poll analytics:", result)

    @patch('polls.tasks.ErrorLog.objects.create')
    def test_analyze_poll_engagement(self, mock_error):
        """Test poll engagement analysis task."""
        poll = Poll.objects.create(
            post=self.post,
            question='Test Poll?',
            expires_at=timezone.now() + timedelta(days=7),
            created_at=timezone.now() - timedelta(days=3)  # Recent poll
        )

        option = PollOption.objects.create(
            poll=poll,
            text='Option 1',
            order=1
        )

        # Create vote
        PollVote.objects.create(poll=poll, option=option, voter=self.user)

        result = analyze_poll_engagement()

        # Check that poll stats were updated
        poll.refresh_from_db()
        self.assertEqual(poll.total_votes, 1)
        self.assertEqual(poll.voters_count, 1)
        self.assertIn("Analyzed engagement for", result)

    @patch('polls.tasks.SystemMetric.objects.create')
    @patch('polls.tasks.ErrorLog.objects.create')
    def test_analyze_poll_option_performance(self, mock_error, mock_metric):
        """Test poll option performance analysis task."""
        poll = Poll.objects.create(
            post=self.post,
            question='Performance Test Poll?',
            expires_at=timezone.now() + timedelta(days=7),
            is_active=True,
            created_at=timezone.now() - timedelta(days=3),
            total_votes=10
        )

        option1 = PollOption.objects.create(
            poll=poll,
            text='High Performing Option',
            order=1,
            votes_count=8  # 80% - high performing
        )
        option2 = PollOption.objects.create(
            poll=poll,
            text='Low Performing Option',
            order=2,
            votes_count=1  # 10% - low performing
        )

        # Mock vote_percentage property
        def mock_vote_percentage(self):
            if self.poll.total_votes > 0:
                return (self.votes_count / self.poll.total_votes) * 100
            return 0

        with patch.object(PollOption, 'vote_percentage',
                          property(mock_vote_percentage)):
            result = analyze_poll_option_performance()

        # Check that metrics were created
        self.assertEqual(mock_metric.call_count, 2)  # High and low performing
        self.assertIn("Analyzed", result)
        self.assertIn("high-performing", result)
        self.assertIn("low-performing", result)

    @patch('polls.tasks.ErrorLog.objects.create')
    def test_cleanup_empty_poll_options(self, mock_error):
        """Test cleanup of empty poll options task."""
        # Create a poll with data that meets cleanup criteria
        poll = Poll.objects.create(
            post=self.post,
            question='Cleanup Test Poll?',
            expires_at=timezone.now() + timedelta(days=7),
            is_active=True,
            total_votes=15  # Enough votes to trigger cleanup
        )
        # Set the poll as mature (older than 24 hours)
        poll.created_at = timezone.now() - timedelta(days=2)
        poll.save()

        # Create options - some with votes, some empty
        option1 = PollOption.objects.create(
            poll=poll, text='Popular Option', order=1, votes_count=10
        )
        option2 = PollOption.objects.create(
            poll=poll, text='Empty Option 1', order=2, votes_count=0
        )
        option3 = PollOption.objects.create(
            poll=poll, text='Another Option', order=3, votes_count=5
        )
        option4 = PollOption.objects.create(
            poll=poll, text='Empty Option 2', order=4, votes_count=0
        )

        initial_count = PollOption.objects.filter(poll=poll).count()
        self.assertEqual(initial_count, 4)

        result = cleanup_empty_poll_options()

        # Check that empty options were removed
        remaining_options = PollOption.objects.filter(poll=poll)
        # Only options with votes remain
        self.assertEqual(remaining_options.count(), 2)

        # Check that options with votes still exist
        self.assertTrue(remaining_options.filter(pk=option1.pk).exists())
        self.assertTrue(remaining_options.filter(pk=option3.pk).exists())

        # Check that empty options were removed
        self.assertFalse(PollOption.objects.filter(pk=option2.pk).exists())
        self.assertFalse(PollOption.objects.filter(pk=option4.pk).exists())

        self.assertIn("Cleaned up", result)

    @patch('polls.tasks.ErrorLog.objects.create')
    def test_reorder_poll_options_by_popularity(self, mock_error):
        """Test reordering poll options by popularity task."""
        poll = Poll.objects.create(
            post=self.post,
            question='Reorder Test Poll?',
            expires_at=timezone.now() + timedelta(days=7),
            is_closed=True,
            updated_at=timezone.now() - timedelta(hours=12),  # Recently closed
            total_votes=10
        )

        # Create options with different vote counts but wrong order
        option1 = PollOption.objects.create(
            poll=poll, text='Least Popular', order=1, votes_count=1
        )
        option2 = PollOption.objects.create(
            poll=poll, text='Most Popular', order=2, votes_count=7
        )
        option3 = PollOption.objects.create(
            poll=poll, text='Middle Popular', order=3, votes_count=2
        )

        result = reorder_poll_options_by_popularity()

        # Check that options were reordered by popularity
        option1.refresh_from_db()
        option2.refresh_from_db()
        option3.refresh_from_db()

        # Most popular should be order 1, least popular should be order 3
        self.assertEqual(option2.order, 1)  # Most popular (7 votes)
        self.assertEqual(option3.order, 2)  # Middle popular (2 votes)
        self.assertEqual(option1.order, 3)  # Least popular (1 vote)

        self.assertIn("Reordered options for", result)

    @patch('polls.tasks.SystemMetric.objects.create')
    @patch('polls.tasks.ErrorLog.objects.create')
    def test_generate_poll_option_insights(self, mock_error, mock_metric):
        """Test poll option insights generation task."""
        poll = Poll.objects.create(
            post=self.post,
            question='Insights Test Poll?',
            expires_at=timezone.now() + timedelta(days=7),
            created_at=timezone.now() - timedelta(days=15)  # Within 30 days
        )

        # Create options with different characteristics
        PollOption.objects.create(
            poll=poll, text='Short', order=1  # ≤20 chars
        )
        PollOption.objects.create(
            poll=poll,
            text='This is a very long poll option text that exceeds fifty',
            order=2  # >50 chars
        )

        result = generate_poll_option_insights()

        # Check that insights metric was created
        mock_metric.assert_called_once()
        call_args = mock_metric.call_args[1]

        self.assertEqual(call_args['metric_type'], 'poll_option_insights')
        self.assertEqual(call_args['value'], 2)  # Total options analyzed

        insights_data = call_args['additional_data']
        self.assertIn('short_options', insights_data)
        self.assertIn('long_options', insights_data)
        self.assertIn('total_options_analyzed', insights_data)

        self.assertIn("Generated insights for", result)

    def test_task_error_handling(self):
        """Test that tasks handle errors gracefully."""
        # Test with invalid data that might cause errors
        with patch('polls.tasks.Poll.objects.filter') as mock_filter:
            mock_filter.side_effect = Exception("Database error")

            with patch('polls.tasks.ErrorLog.objects.create') as mock_error:
                result = handle_poll_expiration()

                # Check that error was logged
                mock_error.assert_called_once()
                error_call = mock_error.call_args[1]
                self.assertEqual(error_call['level'], 'error')
                self.assertIn('Error handling poll expiration',
                              error_call['message'])

                # Check that error message is returned
                self.assertIn("Error", result)


class PollURLTest(TestCase):
    """Test poll URL routing."""

    def test_poll_urls_exist(self):
        """Test that poll URLs are properly configured."""
        # Test poll list URL
        url = reverse('poll-list')
        self.assertEqual(url, '/api/polls/')

        # Test poll detail URL
        url = reverse('poll-detail', kwargs={'pk': 1})
        self.assertEqual(url, '/api/polls/1/')

    def test_custom_action_urls(self):
        """Test custom action URLs."""
        # Test poll vote action
        url = reverse('poll-vote', kwargs={'pk': 1})
        self.assertEqual(url, '/api/polls/1/vote/')

        # Test poll close action
        url = reverse('poll-close', kwargs={'pk': 1})
        self.assertEqual(url, '/api/polls/1/close/')


if __name__ == '__main__':
    # Tests can be run with: python manage.py test polls.tests
    pass
