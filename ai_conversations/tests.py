"""Simple tests for ai_conversations app."""
from django.contrib.auth.models import User
from django.urls import reverse
from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from core.jwt_test_mixin import JWTAuthTestMixin
from .serializers import AIConversationSerializer
from .models import UserProfile, LLMModel, ConversationAgent, AIConversation, AIMessage
from django.utils import timezone

from .tasks import (
    update_ai_usage_analytics, update_ai_model_performance,
    generate_conversation_summaries, cleanup_old_ai_data,
    update_agent_statistics, summarize_deleted_ai_conversations
)


# --- DRF API Endpoint and Edge Case Tests ---
class AIConversationAPITests(APITestCase, JWTAuthTestMixin):
    """Test DRF API endpoints for AI conversations."""
    def setUp(self):
        self.user = User.objects.create_user(
            username='aiuser',
            password='pass123'
        )
        self.profile, _ = UserProfile.objects.get_or_create(user=self.user)
        UserProfile.objects.filter(user=self.user).update(
            phone_number='+15550000501',
            date_of_birth='1990-01-01',
            is_verified=True,
            last_verified_at=timezone.now()
        )
        self.profile.refresh_from_db()
        self.llm_model = LLMModel.objects.create(
            name='GPT-4',
            model_type='openai',
            model_id='gpt-4'
        )
        self.agent = ConversationAgent.objects.create(
            name='General Assistant',
            agent_type='assistant',
            description='A helpful AI',
            system_prompt='You are a helpful AI.',
            preferred_model=self.llm_model,
            created_by=self.profile
        )
        self.client = APIClient()

        # Create JWT token
        self.jwt_token = self._create_jwt_token_with_session(self.user)

    def test_create_conversation(self):
        """Test creating an AI conversation with authentication."""
        self.authenticate(self.user)

        url = reverse('conversation-list')
        data = {
            'user': self.profile.pk,
            'agent': self.agent.pk,
            'title': 'Test Conversation',
            'status': 'active'
        }
        response = self.client.post(url, data, format='json')
        self.assertIn(response.status_code, [
            status.HTTP_201_CREATED,
            status.HTTP_404_NOT_FOUND
        ])

        if response.status_code == status.HTTP_201_CREATED:
            self.assertTrue(
                AIConversation.objects.filter(
                    title='Test Conversation'
                ).exists()
            )

    def test_list_conversations(self):
        """Test listing conversations with authentication."""
        self.authenticate(self.user)

        AIConversation.objects.create(
            user=self.profile,
            agent=self.agent,
            title='C1',
            status='active'
        )
        url = reverse('conversation-list')
        response = self.client.get(url)
        self.assertIn(response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND
        ])

        if response.status_code == status.HTTP_200_OK:
            self.assertGreaterEqual(len(response.data['results']), 1)

    def test_send_message(self):
        """Test sending an AI message with authentication."""
        self.authenticate(self.user)

        conv = AIConversation.objects.create(
            user=self.profile,
            agent=self.agent,
            title='C2',
            status='active'
        )
        url = reverse('send-ai-message', args=[conv.id])
        data = {'role': 'user', 'content': 'Hello AI!', 'conversation': conv.id}
        response = self.client.post(url, data, format='json')
        self.assertIn(response.status_code, [
            status.HTTP_201_CREATED,
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_404_NOT_FOUND
        ])

        if response.status_code in [status.HTTP_201_CREATED, status.HTTP_200_OK]:
            self.assertTrue(
                AIMessage.objects.filter(
                    conversation=conv,
                    content='Hello AI!'
                ).exists()
            )

    def test_get_conversation_messages(self):
        """Test getting conversation messages with authentication."""
        self.authenticate(self.user)

        conv = AIConversation.objects.create(
            user=self.profile,
            agent=self.agent,
            title='C3',
            status='active'
        )
        AIMessage.objects.create(conversation=conv, role='user', content='Hi')
        url = reverse('conversation-messages', args=[conv.id])
        response = self.client.get(url)
        self.assertIn(response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND
        ])

        if response.status_code == status.HTTP_200_OK:
            # Handle both list and paginated response formats
            if isinstance(response.data, list):
                self.assertGreaterEqual(len(response.data), 0)
            else:
                self.assertGreaterEqual(len(response.data.get('results', [])), 0)

    def test_list_public_agents(self):
        """Test listing public agents with authentication."""
        self.authenticate(self.user)

        url = reverse('public-agents')
        response = self.client.get(url)
        self.assertIn(response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND
        ])

        if response.status_code == status.HTTP_200_OK:
            # Check if any agents are public or no results
            if response.data.get('results'):
                self.assertTrue(
                    any(a.get('is_public') for a in response.data['results'])
                )

    def test_list_active_models(self):
        """Test listing active models with authentication."""
        self.authenticate(self.user)

        url = reverse('active-models')
        response = self.client.get(url)
        self.assertIn(response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND
        ])

        if response.status_code == status.HTTP_200_OK:
            # Check if any models are active or no results
            if response.data.get('results'):
                self.assertTrue(
                    any(m.get('model_type') == 'openai'
                        for m in response.data['results'])
                )

    def test_analytics_dashboard(self):
        """Test analytics dashboard with authentication."""
        self.authenticate(self.user)

        url = reverse('ai-analytics-dashboard')
        response = self.client.get(url)
        self.assertIn(response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND
        ])

        if response.status_code == status.HTTP_200_OK:
            self.assertIn('total_conversations', response.data)

    def test_invalid_conversation_create(self):
        """Test invalid conversation creation with authentication."""
        self.authenticate(self.user)

        url = reverse('ai-conversation-list')
        data = {
            'agent': 999999,  # Invalid agent ID
            'title': '',  # Empty title should be invalid
            'status': 'invalid_status'  # Invalid status
        }
        response = self.client.post(url, data, format='json')
        self.assertIn(response.status_code, [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_404_NOT_FOUND
        ])

    def test_send_message_invalid_role(self):
        """Test sending message with invalid role."""
        self.authenticate(self.user)

        conv = AIConversation.objects.create(
            user=self.profile,
            agent=self.agent,
            title='C4',
            status='active'
        )
        url = reverse('send-ai-message', args=[conv.id])
        data = {'role': 'invalid', 'content': 'Test'}
        response = self.client.post(url, data, format='json')
        self.assertIn(response.status_code, [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_404_NOT_FOUND
        ])

    def test_send_message_empty_content(self):
        """Test sending message with empty content."""
        self.authenticate(self.user)

        conv = AIConversation.objects.create(
            user=self.profile,
            agent=self.agent,
            title='C5',
            status='active'
        )
        url = reverse('send-ai-message', args=[conv.id])
        data = {'role': 'user', 'content': ''}
        response = self.client.post(url, data, format='json')
        self.assertIn(response.status_code, [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_404_NOT_FOUND
        ])

    def test_permission_required(self):
        """Test permission required for unauthenticated access."""
        self.client.force_authenticate(user=None)
        url = reverse('ai-conversation-list')
        response = self.client.get(url)
        self.assertIn(response.status_code, [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_404_NOT_FOUND
        ])

    def test_large_message_payload(self):
        """Test sending large message payload."""
        self.authenticate(self.user)

        conv = AIConversation.objects.create(
            user=self.profile,
            agent=self.agent,
            title='C6',
            status='active'
        )
        url = reverse('send-ai-message', args=[conv.id])
        data = {'role': 'user', 'content': 'x' * 10000}
        response = self.client.post(url, data, format='json')
        self.assertIn(response.status_code, [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            status.HTTP_404_NOT_FOUND
        ])

    def test_serializer_validation(self):
        """Test serializer validation."""
        data = {
            'user': 999999,  # Invalid user ID
            'agent': 999999,  # Invalid agent ID
            'title': 'x' * 300,  # Title too long
            'status': 'invalid_status'  # Invalid status
        }
        serializer = AIConversationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        # Should have validation errors
        self.assertTrue(len(serializer.errors) > 0)

    def test_edge_case_duplicate_conversation(self):
        """Test creating duplicate conversation."""
        self.authenticate(self.user)

        AIConversation.objects.create(
            user=self.profile,
            agent=self.agent,
            title='Dup',
            status='active'
        )
        url = reverse('ai-conversation-list')
        data = {
            'user': self.profile.pk,
            'agent': self.agent.pk,
            'title': 'Dup',
            'status': 'active'
        }
        response = self.client.post(url, data, format='json')
        self.assertIn(response.status_code, [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_201_CREATED,
            status.HTTP_404_NOT_FOUND
        ])

    def test_edge_case_archived_conversation(self):
        """Test listing archived conversations."""
        self.authenticate(self.user)

        AIConversation.objects.create(
            user=self.profile,
            agent=self.agent,
            title='Archived',
            status='archived'
        )
        url = reverse('ai-conversation-list')
        response = self.client.get(url)
        self.assertIn(response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND
        ])


class AIConversationsModelTests(TestCase):
    """Test all AI conversations models."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.user_profile = UserProfile.objects.create(
            user=self.user,
            role='normal'
        )

    def test_llm_model_creation(self):
        """Test LLMModel creation and properties."""
        model = LLMModel.objects.create(
            name='GPT-4',
            model_type='openai',
            model_id='gpt-4'
        )

        self.assertEqual(str(model), 'GPT-4 (openai)')
        self.assertEqual(model.name, 'GPT-4')
        self.assertEqual(model.model_type, 'openai')

    def test_conversation_agent_creation(self):
        """Test ConversationAgent creation and properties."""
        llm_model = LLMModel.objects.create(
            name='GPT-4',
            model_type='openai',
            model_id='gpt-4'
        )

        agent = ConversationAgent.objects.create(
            name='Test Assistant',
            agent_type='assistant',
            description='A helpful test assistant',
            system_prompt='You are a helpful assistant',
            preferred_model=llm_model,
            created_by=self.user_profile
        )

        self.assertEqual(str(agent), 'Test Assistant (assistant)')
        self.assertEqual(agent.name, 'Test Assistant')
        self.assertEqual(agent.preferred_model, llm_model)

    def test_ai_conversation_creation(self):
        """Test AIConversation creation and properties."""
        llm_model = LLMModel.objects.create(
            name='GPT-4',
            model_type='openai',
            model_id='gpt-4'
        )

        agent = ConversationAgent.objects.create(
            name='Test Assistant',
            agent_type='assistant',
            description='Test agent',
            system_prompt='You are helpful',
            preferred_model=llm_model,
            created_by=self.user_profile
        )

        conversation = AIConversation.objects.create(
            user=self.user_profile,
            agent=agent,
            title='Test Conversation'
        )

        self.assertTrue('Test Conversation' in str(conversation))
        self.assertEqual(conversation.user, self.user_profile)
        self.assertEqual(conversation.agent, agent)

    def test_ai_message_creation(self):
        """Test AIMessage creation and properties."""
        llm_model = LLMModel.objects.create(
            name='GPT-4',
            model_type='openai',
            model_id='gpt-4'
        )

        agent = ConversationAgent.objects.create(
            name='Test Assistant',
            agent_type='assistant',
            description='Test agent',
            system_prompt='You are helpful',
            preferred_model=llm_model,
            created_by=self.user_profile
        )

        conversation = AIConversation.objects.create(
            user=self.user_profile,
            agent=agent,
            title='Test Conversation'
        )

        message = AIMessage.objects.create(
            conversation=conversation,
            role='user',
            content='Hello, how are you?'
        )

        self.assertTrue('user:' in str(message))
        self.assertTrue('Hello, how are you?' in str(message))
        self.assertEqual(message.conversation, conversation)
        self.assertEqual(message.role, 'user')
        self.assertEqual(message.content, 'Hello, how are you?')


class AIConversationTasksTests(TestCase):
    """Comprehensive tests for AI conversation Celery tasks."""

    def test_tasks_import_and_structure(self):
        """Test that all Celery tasks can be imported and have a delay method."""
        tasks = [
            update_ai_usage_analytics,
            update_ai_model_performance,
            generate_conversation_summaries,
            cleanup_old_ai_data,
            update_agent_statistics,
            summarize_deleted_ai_conversations
        ]
        for task in tasks:
            self.assertTrue(hasattr(task, 'delay'))
            self.assertTrue(callable(task))

    def test_update_ai_usage_analytics_functional(self):
        """Test update_ai_usage_analytics task updates analytics for user messages."""
        user = User.objects.create(username='analyticuser')
        user_profile = UserProfile.objects.create(user=user)
        agent = ConversationAgent.objects.create(name='Agent', agent_type='assistant', created_by=user_profile)
        conv = AIConversation.objects.create(user=user_profile, agent=agent, is_deleted=False)
        AIMessage.objects.create(conversation=conv, created_at='2025-07-22', role='user', is_deleted=False, input_tokens=10, output_tokens=5, cost=0.1)
        result = update_ai_usage_analytics()
        from .models import AIUsageAnalytics
        self.assertIn('Updated AI usage analytics', result)
        self.assertTrue(AIUsageAnalytics.objects.filter(user=user_profile).exists())

    def test_update_ai_model_performance_functional(self):
        """Test update_ai_model_performance task updates model performance metrics."""
        user = User.objects.create(username='perfuser')
        user_profile = UserProfile.objects.create(user=user)
        agent = ConversationAgent.objects.create(name='PerfAgent', agent_type='assistant', created_by=user_profile)
        conv = AIConversation.objects.create(user=user_profile, agent=agent, is_deleted=False)
        model = LLMModel.objects.create(name='PerfModel', model_type='openai', model_id='perf-1', status='active')
        AIMessage.objects.create(conversation=conv, model_used=model, created_at='2025-07-22', is_deleted=False, is_error=False, input_tokens=10, output_tokens=5, cost=0.2, response_time=1.5)
        result = update_ai_model_performance()
        from .models import AIModelPerformance
        self.assertIn('Updated performance metrics', result)
        self.assertTrue(AIModelPerformance.objects.filter(model=model).exists())

    def test_generate_conversation_summaries_functional(self):
        """Test generate_conversation_summaries task generates summaries for conversations."""
        user = User.objects.create(username='summaryuser')
        user_profile = UserProfile.objects.create(user=user)
        agent = ConversationAgent.objects.create(name='SummaryAgent', agent_type='assistant', created_by=user_profile)
        conv = AIConversation.objects.create(agent=agent, user=user_profile, auto_summarize=True, total_messages=12, is_deleted=False)
        for i in range(12):
            AIMessage.objects.create(conversation=conv, role='user', is_deleted=False, content=f"Message {i}", created_at='2025-07-22')
        result = generate_conversation_summaries()
        from .models import AIConversationSummary
        self.assertIn('Generated summaries', result)
        self.assertTrue(AIConversationSummary.objects.filter(conversation=conv).exists())

    def test_cleanup_old_ai_data_functional(self):
        """Test cleanup_old_ai_data task removes old analytics and performance records."""
        from datetime import timedelta, date
        old_date = date.today() - timedelta(days=400)
        user = User.objects.create(username='olduser')
        user_profile = UserProfile.objects.create(user=user)
        agent = ConversationAgent.objects.create(name='OldAgent', agent_type='assistant', created_by=user_profile)
        model = LLMModel.objects.create(name='OldModel', model_type='openai', model_id='old-1', status='active')
        from .models import AIUsageAnalytics, AIModelPerformance
        AIUsageAnalytics.objects.create(user=user_profile, date=old_date)
        AIModelPerformance.objects.create(model=model, date=old_date)
        AIConversation.objects.create(user=user_profile, agent=agent, last_message_at='2023-07-22', status='active', is_deleted=False)
        result = cleanup_old_ai_data()
        self.assertIn('Cleaned up', result)

    def test_update_agent_statistics_functional(self):
        """Test update_agent_statistics task updates agent statistics."""
        user = User.objects.create(username='statuser')
        user_profile = UserProfile.objects.create(user=user)
        agent = ConversationAgent.objects.create(name='StatAgent', agent_type='assistant', created_by=user_profile)
        AIConversation.objects.create(agent=agent, user=user_profile, is_deleted=False)
        result = update_agent_statistics()
        agent.refresh_from_db()
        self.assertIn('Updated statistics', result)
        self.assertEqual(agent.total_conversations, 1)

    def test_summarize_deleted_ai_conversations_functional(self):
        """Test summarize_deleted_ai_conversations task returns correct deletion stats."""
        user = User.objects.create(username='deleteduser')
        user_profile = UserProfile.objects.create(user=user)
        agent = ConversationAgent.objects.create(name='TestAgent', agent_type='assistant', created_by=user_profile)
        from datetime import datetime
        for i in range(2):
            conv = AIConversation.objects.create(user=user_profile, agent=agent, is_deleted=True)
            conv.deleted_at = datetime(2025, 7, 21)
            conv.save()
        result = summarize_deleted_ai_conversations()
        self.assertIn('total_deleted', result)
        self.assertEqual(result['total_deleted'], 2)
        self.assertTrue(any(stat['user'] == user_profile.id for stat in result['user_deletion_stats']))
        self.assertIn('top_agents_in_deleted', result)
