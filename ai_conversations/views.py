"""Refactored views for ai_conversations app (aligned with current models)."""

from datetime import timedelta
from django.db import models
from django.db.models import Count, Avg, Sum
from django.utils import timezone
from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)

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
from .serializers import (
    LLMModelSerializer,
    ConversationAgentSerializer,
    AIConversationSerializer,
    AIMessageSerializer,
    AIMessageRatingUpsertSerializer,
    AIMessageRatingSerializer,
    AIMessageFlagSerializer,
    AIMessageFlagDetailSerializer,
    AIUsageAnalyticsSerializer,
    AIModelPerformanceSerializer,
    AIConversationSummarySerializer,
)

# --------------------------------------------------
# LLM Models
# --------------------------------------------------
class LLMModelViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LLMModel.objects.filter(is_deleted=False).order_by('name')
    serializer_class = LLMModelSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):  # noqa: D401
        qs = super().get_queryset()
        model_type = self.request.query_params.get('model_type')
        status_filter = self.request.query_params.get('status')
        if model_type:
            qs = qs.filter(model_type=model_type)
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs.filter(is_deleted=False)


# --------------------------------------------------
# Conversation Agents
# --------------------------------------------------
class ConversationAgentViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationAgentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):  # noqa: D401
        user_profile = self.request.user.profile
        return (
            ConversationAgent.objects.filter(models.Q(created_by=user_profile, is_deleted=False) | models.Q(is_public=True)
            )
            .filter(is_deleted=False)
            .select_related('preferred_model', 'created_by')
            .order_by('-created_at')
        )

    def perform_create(self, serializer):  # noqa: D401
        serializer.save(created_by=self.request.user.profile)

    @action(detail=False, methods=['get'])
    def mine(self, request):  # noqa: D401
        qs = self.get_queryset().filter(created_by=request.user.profile)
        ser = self.get_serializer(qs, many=True)
        return Response(ser.data)


# --------------------------------------------------
# Conversations
# --------------------------------------------------
class AIConversationViewSet(viewsets.ModelViewSet):
    serializer_class = AIConversationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):  # noqa: D401
        return (
            AIConversation.objects.filter(user=self.request.user.profile, is_deleted=False)
            .select_related('agent', 'user')
            .order_by('-updated_at')
        )

    def perform_create(self, serializer):  # noqa: D401
        serializer.save(user=self.request.user.profile)

    def perform_destroy(self, instance):  # noqa: D401
        instance.is_deleted = True
        instance.save(update_fields=['is_deleted'])
        instance.messages.update(is_deleted=True)

    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):  # noqa: D401
        convo = self.get_object()
        msgs = convo.messages.filter(is_deleted=False).order_by('created_at')
        ser = AIMessageSerializer(msgs, many=True)
        return Response(ser.data)


# --------------------------------------------------
# Messages
# --------------------------------------------------
class AIMessageViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = AIMessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):  # noqa: D401
        return (
            AIMessage.objects.filter(conversation__user=self.request.user.profile,
                is_deleted=False)
            .select_related('conversation', 'model_used')
            .order_by('-created_at')
        )

    def perform_create(self, serializer):  # noqa: D401
        conversation = serializer.validated_data['conversation']
        if conversation.user != self.request.user.profile:
            raise PermissionError('Forbidden')
        serializer.save()

    @action(detail=False, methods=['get'])
    def by_conversation(self, request):  # noqa: D401
        cid = request.query_params.get('conversation_id')
        if not cid:
            return Response({'error': 'conversation_id required'}, status=400)
        msgs = (
            self.get_queryset()
            .filter(conversation_id=cid)
            .order_by('created_at')
        )
        ser = self.get_serializer(msgs, many=True)
        return Response(ser.data)


# --------------------------------------------------
# Ratings
# --------------------------------------------------
class AIMessageRatingViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):  # noqa: D401
        return (
            AIMessageRating.objects.filter(user=self.request.user.profile, is_deleted=False)
            .filter(is_deleted=False)
            .select_related('message', 'user')
            .order_by('-created_at')
        )

    def get_serializer_class(self):  # noqa: D401
        if self.action in ['create', 'update', 'partial_update']:
            return AIMessageRatingUpsertSerializer
        return AIMessageRatingSerializer

    def perform_create(self, serializer):  # noqa: D401
        serializer.save(user=self.request.user.profile)

    @action(detail=False, methods=['get'])
    def by_message(self, request):  # noqa: D401
        mid = request.query_params.get('message_id')
        if not mid:
            return Response({'error': 'message_id required'}, status=400)
        ratings = AIMessageRating.objects.filter(message_id=mid, is_deleted=False)
        ser = self.get_serializer(ratings, many=True)
        return Response(ser.data)

    @action(detail=False, methods=['get'])
    def summary(self, request):  # noqa: D401
        mid = request.query_params.get('message_id')
        if not mid:
            return Response({'error': 'message_id required'}, status=400)
        qs = AIMessageRating.objects.filter(message_id=mid, is_deleted=False)
        agg = qs.aggregate(avg=Avg('score'), count=Count('id'))
        user_row = qs.filter(user=request.user.profile).first()
        user = None
        if user_row:
            user = {'id': str(user_row.id), 'score': user_row.score}
        return Response({'helpful': agg, 'user': user})


# --------------------------------------------------
# Flags
# --------------------------------------------------
class AIMessageFlagViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):  # noqa: D401
        return (
            AIMessageFlag.objects.filter(user=self.request.user.profile, is_deleted=False)
            .filter(is_deleted=False)
            .select_related('message', 'user')
            .order_by('-created_at')
        )

    def get_serializer_class(self):  # noqa: D401
        if self.action in ['create', 'update', 'partial_update']:
            return AIMessageFlagSerializer
        return AIMessageFlagDetailSerializer

    def perform_create(self, serializer):  # noqa: D401
        serializer.save(user=self.request.user.profile)

    @action(detail=False, methods=['post'])
    def toggle(self, request):  # noqa: D401
        mid = request.data.get('message')
        flag_type = request.data.get('flag_type')
        if not mid or not flag_type:
            return Response({'error': 'message & flag_type required'}, status=400)
        existing = AIMessageFlag.objects.filter(message_id=mid,
            user=request.user.profile,
            flag_type=flag_type, is_deleted=False).first()
        comment = request.data.get('comment')
        if existing and not comment:
            existing.delete()
            return Response({'toggled_off': True})
        if existing:
            existing.comment = comment or existing.comment
            existing.save(update_fields=['comment'])
            return Response({'updated': True, 'id': existing.id})
        flag = AIMessageFlag.objects.create(
            message_id=mid,
            user=request.user.profile,
            flag_type=flag_type,
            comment=comment or '',
        )
        return Response({'created': True, 'id': flag.id}, status=201)

    @action(detail=False, methods=['get'])
    def by_message(self, request):  # noqa: D401
        mid = request.query_params.get('message_id')
        if not mid:
            return Response({'error': 'message_id required'}, status=400)
        flags = AIMessageFlag.objects.filter(message_id=mid, is_deleted=False)
        ser = self.get_serializer(flags, many=True)
        return Response(ser.data)

    @action(detail=False, methods=['get'])
    def summary(self, request):  # noqa: D401
        mid = request.query_params.get('message_id')
        if not mid:
            return Response({'error': 'message_id required'}, status=400)
        qs = AIMessageFlag.objects.filter(message_id=mid, is_deleted=False)
        counts = qs.values('flag_type').annotate(count=Count('id'))
        data = {r['flag_type']: r['count'] for r in counts}
        user_flags = list(
            qs.filter(user=request.user.profile).values_list(
                'flag_type', flat=True
            )
        )
        return Response({'flags': data, 'user_flags': user_flags})


# --------------------------------------------------
# Usage Analytics
# --------------------------------------------------
class AIUsageAnalyticsViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AIUsageAnalyticsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):  # noqa: D401
        return AIUsageAnalytics.objects.filter(is_deleted=False,
            user=self.request.user.profile).order_by('-date')

    @action(detail=False, methods=['get'])
    def summary(self, request):  # noqa: D401
        days = int(request.query_params.get('days', 30))
        start = timezone.now().date() - timedelta(days=days)
        qs = self.get_queryset().filter(date__gte=start)
        agg = qs.aggregate(
            conversations_started=Sum('conversations_started'),
            messages_sent=Sum('messages_sent'),
            tokens_consumed=Sum('tokens_consumed'),
            total_cost=Sum('total_cost'),
            image_analysis_requests=Sum('image_analysis_requests'),
            code_generation_requests=Sum('code_generation_requests'),
            web_browsing_requests=Sum('web_browsing_requests'),
        )
        return Response(agg)

    @action(detail=False, methods=['get'])
    def daily(self, request):  # noqa: D401
        days = int(request.query_params.get('days', 14))
        start = timezone.now().date() - timedelta(days=days)
        qs = self.get_queryset().filter(date__gte=start)
        data = {}
        for rec in qs:
            data[rec.date.isoformat()] = {
                'conversations_started': rec.conversations_started,
                'messages_sent': rec.messages_sent,
                'tokens_consumed': rec.tokens_consumed,
                'total_cost': float(rec.total_cost),
            }
        return Response(data)


# --------------------------------------------------
# Model Performance
# --------------------------------------------------
class AIModelPerformanceViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AIModelPerformanceSerializer
    permission_classes = [IsAuthenticated]
    queryset = AIModelPerformance.objects.filter(is_deleted=False).order_by('-date')

    def get_queryset(self):  # noqa: D401
        qs = super().get_queryset()
        model_id = self.request.query_params.get('model_id')
        if model_id:
            qs = qs.filter(model_id=model_id)
        return qs.filter(is_deleted=False)


# --------------------------------------------------
# Conversation Summaries
# --------------------------------------------------
class AIConversationSummaryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AIConversationSummarySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):  # noqa: D401
        return (
            AIConversationSummary.objects.filter(conversation__user=self.request.user.profile, is_deleted=False)
            .filter(is_deleted=False)
            .select_related('conversation')
            .order_by('-updated_at')
        )

    @action(detail=False, methods=['get'])
    def by_conversation(self, request):  # noqa: D401
        cid = request.query_params.get('conversation_id')
        if not cid:
            return Response({'error': 'conversation_id required'}, status=400)
        qs = self.get_queryset().filter(conversation_id=cid)
        ser = self.get_serializer(qs, many=True)
        return Response(ser.data)
