"""API views for visitor analytics."""

import logging
from datetime import datetime
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination

from communities.models import Community, CommunityMembership
from analytics.visitor_utils import (
    VisitorAnalytics,
    get_today_visitors,
    get_weekly_visitors,
    get_monthly_visitors,
    get_visitor_growth_rate
)
from analytics.serializers import (
    VisitorStatsSerializer,
    DivisionBreakdownSerializer,
    VisitorTrendSerializer,
    ConversionMetricsSerializer,
    VisitorDemographicsSerializer,
    RealtimeVisitorsSerializer
)

logger = logging.getLogger(__name__)


class AnalyticsPagination(PageNumberPagination):
    """Custom pagination for analytics endpoints."""
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200


class VisitorAnalyticsViewSet(viewsets.ViewSet):
    """
    ViewSet for visitor analytics endpoints.
    Provides comprehensive visitor tracking and analytics.
    """
    permission_classes = [IsAuthenticated]
    pagination_class = AnalyticsPagination

    def _check_community_access(self, request, community_id):
        """
        Check if user has access to community analytics.
        Returns (community, membership, can_view_detailed).
        """
        community = get_object_or_404(
            Community,
            id=community_id,
            is_deleted=False
        )

        membership = CommunityMembership.objects.filter(
            community=community,
            user=request.user.profile,
            status='active',
            is_deleted=False
        ).first()

        if not membership:
            return None, None, False

        # Check if user can view detailed analytics
        can_view_detailed = membership.can_moderate_posts()

        return community, membership, can_view_detailed

    @action(detail=False, methods=['get'], url_path='communities/(?P<community_id>[^/.]+)/visitors')
    def unique_visitors(self, request, community_id=None):
        """
        Get unique visitor statistics for a community.

        Query params:
        - start_date: ISO format date (optional)
        - end_date: ISO format date (optional)
        """
        try:
            community, membership, can_view = self._check_community_access(
                request, community_id
            )

            if not membership:
                return Response(
                    {'error': 'You are not a member of this community'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Parse date range
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')

            if start_date:
                start_date = timezone.make_aware(
                    datetime.fromisoformat(start_date)
                )
            if end_date:
                end_date = timezone.make_aware(
                    datetime.fromisoformat(end_date)
                )

            # Get visitor statistics
            stats = VisitorAnalytics.get_unique_visitors(
                str(community_id),
                start_date=start_date,
                end_date=end_date
            )

            serializer = VisitorStatsSerializer(stats)
            return Response(serializer.data)

        except ValueError as e:
            return Response(
                {'error': f'Invalid date format: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(
                "Error getting visitors for community %s: %s",
                community_id, e
            )
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='communities/(?P<community_id>[^/.]+)/division-breakdown')
    def division_breakdown(self, request, community_id=None):
        """
        Get division breakdown of visitors.

        Query params:
        - start_date: ISO format date (optional)
        - end_date: ISO format date (optional)
        """
        try:
            community, membership, can_view = self._check_community_access(
                request, community_id
            )

            if not membership:
                return Response(
                    {'error': 'You are not a member of this community'},
                    status=status.HTTP_403_FORBIDDEN
                )

            if not can_view:
                return Response(
                    {'error': 'Insufficient permissions'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Parse date range
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')

            if start_date:
                start_date = timezone.make_aware(
                    datetime.fromisoformat(start_date)
                )
            if end_date:
                end_date = timezone.make_aware(
                    datetime.fromisoformat(end_date)
                )

            # Get division breakdown
            breakdown = VisitorAnalytics.get_division_breakdown(
                str(community_id),
                start_date=start_date,
                end_date=end_date
            )

            serializer = DivisionBreakdownSerializer(breakdown)
            return Response(serializer.data)

        except ValueError as e:
            return Response(
                {'error': f'Invalid date format: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(
                "Error getting division breakdown for community %s: %s",
                community_id, e
            )
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='communities/(?P<community_id>[^/.]+)/trends')
    def visitor_trends(self, request, community_id=None):
        """
        Get visitor trends over time.

        Query params:
        - start_date: ISO format date (optional)
        - end_date: ISO format date (optional)
        - granularity: 'hourly', 'daily', or 'weekly' (default: 'daily')
        """
        try:
            community, membership, can_view = self._check_community_access(
                request, community_id
            )

            if not membership:
                return Response(
                    {'error': 'You are not a member of this community'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Parse parameters
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
            granularity = request.query_params.get('granularity', 'daily')

            if start_date:
                start_date = timezone.make_aware(
                    datetime.fromisoformat(start_date)
                )
            if end_date:
                end_date = timezone.make_aware(
                    datetime.fromisoformat(end_date)
                )

            # Get trends
            trends = VisitorAnalytics.get_visitor_trends(
                str(community_id),
                start_date=start_date,
                end_date=end_date,
                granularity=granularity
            )

            serializer = VisitorTrendSerializer(trends, many=True)
            return Response(serializer.data)

        except ValueError as e:
            return Response(
                {'error': f'Invalid parameter: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(
                "Error getting trends for community %s: %s",
                community_id, e
            )
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='communities/(?P<community_id>[^/.]+)/conversions')
    def conversion_metrics(self, request, community_id=None):
        """
        Get anonymous-to-authenticated conversion metrics.

        Query params:
        - start_date: ISO format date (optional)
        - end_date: ISO format date (optional)
        """
        try:
            community, membership, can_view = self._check_community_access(
                request, community_id
            )

            if not membership:
                return Response(
                    {'error': 'You are not a member of this community'},
                    status=status.HTTP_403_FORBIDDEN
                )

            if not can_view:
                return Response(
                    {'error': 'Insufficient permissions'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Parse date range
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')

            if start_date:
                start_date = timezone.make_aware(
                    datetime.fromisoformat(start_date)
                )
            if end_date:
                end_date = timezone.make_aware(
                    datetime.fromisoformat(end_date)
                )

            # Get conversion metrics
            metrics = VisitorAnalytics.get_conversion_metrics(
                start_date=start_date,
                end_date=end_date,
                community_id=community_id
            )

            serializer = ConversionMetricsSerializer(metrics)
            return Response(serializer.data)

        except ValueError as e:
            return Response(
                {'error': f'Invalid date format: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(
                "Error getting conversions for community %s: %s",
                community_id, e
            )
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='communities/(?P<community_id>[^/.]+)/demographics')
    def visitor_demographics(self, request, community_id=None):
        """
        Get visitor demographics (device, browser, OS breakdown).

        Query params:
        - start_date: ISO format date (optional)
        - end_date: ISO format date (optional)
        """
        try:
            community, membership, can_view = self._check_community_access(
                request, community_id
            )

            if not membership:
                return Response(
                    {'error': 'You are not a member of this community'},
                    status=status.HTTP_403_FORBIDDEN
                )

            if not can_view:
                return Response(
                    {'error': 'Insufficient permissions'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Parse date range
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')

            if start_date:
                start_date = timezone.make_aware(
                    datetime.fromisoformat(start_date)
                )
            if end_date:
                end_date = timezone.make_aware(
                    datetime.fromisoformat(end_date)
                )

            # Get demographics
            demographics = VisitorAnalytics.get_visitor_demographics(
                str(community_id),
                start_date=start_date,
                end_date=end_date
            )

            serializer = VisitorDemographicsSerializer(demographics)
            return Response(serializer.data)

        except ValueError as e:
            return Response(
                {'error': f'Invalid date format: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(
                "Error getting demographics for community %s: %s",
                community_id, e
            )
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='communities/(?P<community_id>[^/.]+)/realtime')
    def realtime_visitors(self, request, community_id=None):
        """Get real-time visitor count from Redis."""
        try:
            community, membership, can_view = self._check_community_access(
                request, community_id
            )

            if not membership:
                return Response(
                    {'error': 'You are not a member of this community'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Get real-time count
            realtime_data = VisitorAnalytics.get_realtime_visitors(
                str(community_id)
            )

            serializer = RealtimeVisitorsSerializer(realtime_data)
            return Response(serializer.data)

        except Exception as e:
            logger.error(
                "Error getting realtime visitors for community %s: %s",
                community_id, e
            )
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# Convenience endpoints for quick access

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def community_visitors_today(request, community_id):
    """Get today's visitor statistics for a community."""
    try:
        # Check access
        community = get_object_or_404(
            Community,
            id=community_id,
            is_deleted=False
        )

        membership = CommunityMembership.objects.filter(
            community=community,
            user=request.user.profile,
            status='active',
            is_deleted=False
        ).first()

        if not membership:
            return Response(
                {'error': 'You are not a member of this community'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get today's visitors
        stats = get_today_visitors(str(community_id))
        serializer = VisitorStatsSerializer(stats)
        return Response(serializer.data)

    except Exception as e:
        logger.error(
            "Error getting today's visitors for community %s: %s",
            community_id, e
        )
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def community_visitors_weekly(request, community_id):
    """Get weekly visitor statistics for a community."""
    try:
        # Check access
        community = get_object_or_404(
            Community,
            id=community_id,
            is_deleted=False
        )

        membership = CommunityMembership.objects.filter(
            community=community,
            user=request.user.profile,
            status='active',
            is_deleted=False
        ).first()

        if not membership:
            return Response(
                {'error': 'You are not a member of this community'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get weekly visitors
        stats = get_weekly_visitors(str(community_id))
        serializer = VisitorStatsSerializer(stats)
        return Response(serializer.data)

    except Exception as e:
        logger.error(
            "Error getting weekly visitors for community %s: %s",
            community_id, e
        )
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def community_visitors_monthly(request, community_id):
    """Get monthly visitor statistics for a community."""
    try:
        # Check access
        community = get_object_or_404(
            Community,
            id=community_id,
            is_deleted=False
        )

        membership = CommunityMembership.objects.filter(
            community=community,
            user=request.user.profile,
            status='active',
            is_deleted=False
        ).first()

        if not membership:
            return Response(
                {'error': 'You are not a member of this community'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get monthly visitors
        stats = get_monthly_visitors(str(community_id))
        serializer = VisitorStatsSerializer(stats)
        return Response(serializer.data)

    except Exception as e:
        logger.error(
            "Error getting monthly visitors for community %s: %s",
            community_id, e
        )
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def community_visitor_growth(request, community_id):
    """
    Get visitor growth rate for a community.

    Query params:
    - days: Number of days to compare (default: 7)
    """
    try:
        # Check access
        community = get_object_or_404(
            Community,
            id=community_id,
            is_deleted=False
        )

        membership = CommunityMembership.objects.filter(
            community=community,
            user=request.user.profile,
            status='active',
            is_deleted=False
        ).first()

        if not membership:
            return Response(
                {'error': 'You are not a member of this community'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Parse days parameter
        days = int(request.query_params.get('days', 7))

        # Get growth rate
        growth = get_visitor_growth_rate(str(community_id), days=days)

        return Response(growth)

    except ValueError as e:
        return Response(
            {'error': f'Invalid parameter: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(
            "Error getting growth for community %s: %s",
            community_id, e
        )
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
