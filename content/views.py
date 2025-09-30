"""Views for content app with complete CRUD operations."""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
from accounts.models import UserProfile, Follow
from accounts.permissions import NotDeletedUserPermission
from .models import Post, Comment, Like, PostMedia, Dislike, PostSee, Mention  # removed Share
from .models import (
    ContentReport,
    ModerationQueue,
    AutoModerationAction,
    ContentModerationRule,
    BotDetectionEvent,
    BotDetectionProfile,
    ContentRecommendation,
    ContentSimilarity,
    UserContentPreferences,
    RecommendationFeedback,
    DirectShare, DirectShareRecipient  # new models
)

from .permissions import IsAuthenticatedOrPublicContent  # , IsOwnerOrReadOnly
from .serializers import (
    PostSerializer,
    PostCreateUpdateSerializer,
    CommentSerializer,
    CommentCreateUpdateSerializer,
    PostMediaSerializer,
    ContentReportSerializer,
    ModerationQueueSerializer,
    AutoModerationActionSerializer,
    ContentModerationRuleSerializer,
    BotDetectionEventSerializer,
    BotDetectionProfileSerializer,
    ContentRecommendationSerializer,
    ContentSimilaritySerializer,
    UserContentPreferencesSerializer,
    RecommendationFeedbackSerializer,
    DirectShareSerializer, DirectShareCreateSerializer,
    DirectShareRecipientSerializer,
)

class ContentRecommendationViewSet(viewsets.ModelViewSet):
    queryset = ContentRecommendation.objects.filter(is_deleted=False)
    serializer_class = ContentRecommendationSerializer
    permission_classes = [IsAuthenticated, NotDeletedUserPermission]

    def perform_create(self, serializer):
        user_profile = get_object_or_404(UserProfile, user=self.request.user)
        serializer.save(user=user_profile)

class ContentSimilarityViewSet(viewsets.ModelViewSet):
    queryset = ContentSimilarity.objects.filter(is_deleted=False)
    serializer_class = ContentSimilaritySerializer

class UserContentPreferencesViewSet(viewsets.ModelViewSet):
    queryset = UserContentPreferences.objects.filter(is_deleted=False)
    serializer_class = UserContentPreferencesSerializer

    def perform_create(self, serializer):
        user_profile = get_object_or_404(UserProfile, user=self.request.user)
        serializer.save(user=user_profile)

class RecommendationFeedbackViewSet(viewsets.ModelViewSet):
    queryset = RecommendationFeedback.objects.filter(is_deleted=False)
    serializer_class = RecommendationFeedbackSerializer

    def perform_create(self, serializer):
        user_profile = get_object_or_404(UserProfile, user=self.request.user)
        serializer.save(user=user_profile)

# =====================
# MODERATION & BOT DETECTION VIEWSETS
# =====================

class ContentReportViewSet(viewsets.ModelViewSet):
    queryset = ContentReport.objects.filter(is_deleted=False)
    serializer_class = ContentReportSerializer
    permission_classes = [IsAuthenticated, NotDeletedUserPermission]

    def perform_create(self, serializer):
        user_profile = get_object_or_404(UserProfile, user=self.request.user)
        serializer.save(reporter=user_profile)

class ModerationQueueViewSet(viewsets.ModelViewSet):
    queryset = ModerationQueue.objects.filter(is_deleted=False)
    serializer_class = ModerationQueueSerializer
    permission_classes = [IsAuthenticated, NotDeletedUserPermission]

    # No perform_create: reviewed_by should not be set on create

class AutoModerationActionViewSet(viewsets.ModelViewSet):
    queryset = AutoModerationAction.objects.filter(is_deleted=False)
    serializer_class = AutoModerationActionSerializer
    permission_classes = [IsAuthenticated, NotDeletedUserPermission]

    # No perform_create: reviewed_by should not be set on create

class ContentModerationRuleViewSet(viewsets.ModelViewSet):
    queryset = ContentModerationRule.objects.filter(is_deleted=False)
    serializer_class = ContentModerationRuleSerializer
    permission_classes = [IsAuthenticated, NotDeletedUserPermission]

class BotDetectionEventViewSet(viewsets.ModelViewSet):
    queryset = BotDetectionEvent.objects.filter(is_deleted=False)
    serializer_class = BotDetectionEventSerializer
    permission_classes = [IsAuthenticated, NotDeletedUserPermission]

    def perform_create(self, serializer):
        user_profile = get_object_or_404(UserProfile, user=self.request.user)
        serializer.save(user=user_profile)

class BotDetectionProfileViewSet(viewsets.ModelViewSet):
    queryset = BotDetectionProfile.objects.filter(is_deleted=False)
    serializer_class = BotDetectionProfileSerializer
    permission_classes = [IsAuthenticated, NotDeletedUserPermission]

    def perform_create(self, serializer):
        user_profile = get_object_or_404(UserProfile, user=self.request.user)
        serializer.save(user=user_profile)


class CommentViewSet(viewsets.ModelViewSet):
    """Complete CRUD operations for Comment model."""
    queryset = Comment.objects.filter(is_deleted=False)
    permission_classes = [IsAuthenticatedOrPublicContent]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return CommentCreateUpdateSerializer
        return CommentSerializer

    def get_queryset(self):
        """Get optimized queryset with prefetched related data."""
        return Comment.objects.select_related('author', 'post', 'parent')

    def perform_create(self, serializer):
        """Set the comment author to current user."""
        user_profile = get_object_or_404(UserProfile, user=self.request.user)
        serializer.save(author=user_profile)

    def perform_update(self, serializer):
        """Only allow author to update their comments."""
        from rest_framework.exceptions import PermissionDenied

        instance = serializer.instance

        if (instance.author.user.id != self.request.user.id and
                not self.request.user.is_staff):
            raise PermissionDenied("You can only edit your own comments")

        # Track edit information
        instance.is_edited = True
        serializer.save()

    def perform_destroy(self, instance):
        """Soft delete the comment with cascading deletion of related objects."""
        from rest_framework.exceptions import PermissionDenied

        if (instance.author.user.id != self.request.user.id and
                not self.request.user.is_staff):
            raise PermissionDenied("You can only delete your own comments")

        # Cascade soft delete comment and all related objects
        from core.cascade_deletion import cascade_soft_delete_comment
        cascade_soft_delete_comment(instance)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def like(self, request, pk=None):
        """Like or unlike a comment."""
        from django.contrib.contenttypes.models import ContentType
        comment = self.get_object()
        user_profile = get_object_or_404(UserProfile, user=request.user)
        comment_content_type = ContentType.objects.get_for_model(Comment)

        like, created = Like.objects.get_or_create(
            user=user_profile,
            content_type=comment_content_type,
            object_id=comment.id
        )

        if not created:
            like.delete()
            return Response({'message': 'Comment unliked'}, status=status.HTTP_200_OK)

        return Response({'message': 'Comment liked'}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def replies(self, request, pk=None):
        """Get all replies to a comment."""
        comment = self.get_object()
        replies = Comment.objects.filter(parent=comment, is_deleted=False).order_by('created_at')
        serializer = self.get_serializer(replies, many=True)
        return Response(serializer.data)

class PostMediaViewSet(viewsets.ModelViewSet):
    """Complete CRUD operations for PostMedia model."""
    queryset = PostMedia.objects.filter(is_deleted=False)
    serializer_class = PostMediaSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        """Filter media based on user permissions."""
        if self.request.user.is_staff:
            return PostMedia.objects.all()

        if not self.request.user.is_authenticated:
            # For unauthenticated users, show media from public posts
            return PostMedia.objects.filter(post__visibility='public', is_deleted=False)

        user_profile = get_object_or_404(UserProfile, user=self.request.user)
        # For authenticated users, show their own media plus public media
        from django.db.models import Q
        return PostMedia.objects.filter(Q(post__author=user_profile, is_deleted=False) | Q(post__visibility='public'),
            is_deleted=False
        )

    def perform_create(self, serializer):
        """Validate that the user can add media to the post."""
        from rest_framework.exceptions import PermissionDenied

        post = serializer.validated_data.get('post')
        if (post and post.author.user != self.request.user and
                not self.request.user.is_staff):
            raise PermissionDenied("You can only add media to your own posts")
        serializer.save()

# =============================================================================
# A/B TESTING VIEWS FOR CONTENT RECOMMENDATION EXPERIMENTATION
# =============================================================================

class ContentExperimentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing content A/B testing experiments."""
    from content.models import ContentExperiment
    queryset = ContentExperiment.objects.filter(is_deleted=False)
    permission_classes = [IsAuthenticated, NotDeletedUserPermission]

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        from content.serializers import ContentExperimentSerializer
        return ContentExperimentSerializer

    def get_queryset(self):
        """Filter experiments based on user permissions."""
        user = self.request.user
        if user.is_staff:
            return self.queryset
        else:
            # Regular users can only see experiments they created
            return self.queryset.filter(created_by__user=user)

    def perform_create(self, serializer):
        """Set the creator when creating an experiment."""
        user_profile = get_object_or_404(UserProfile, user=self.request.user)
        serializer.save(created_by=user_profile)

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get statistical results for an experiment."""
        from content.utils import get_content_experiment_stats

        try:
            experiment = self.get_object()
            stats = get_content_experiment_stats(experiment.id)

            if stats:
                return Response({
                    'status': 'success',
                    'stats': stats
                })
            else:
                return Response({
                    'status': 'error',
                    'message': 'Unable to calculate stats for this experiment'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Start an experiment."""
        from django.utils import timezone

        try:
            experiment = self.get_object()

            if experiment.status != 'draft':
                return Response({
                'status': 'error',
                'message': 'Only draft experiments can be started'
            }, status=status.HTTP_400_BAD_REQUEST)

            experiment.status = 'active'
            experiment.start_date = timezone.now()
            experiment.save()

            return Response({
                'status': 'success',
                'message': 'Experiment started successfully'
            })

        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def stop(self, request, pk=None):
        """Stop an experiment."""
        from django.utils import timezone

        try:
            experiment = self.get_object()

            if experiment.status != 'active':
                return Response({
                    'status': 'error',
                    'message': 'Only active experiments can be stopped'
                }, status=status.HTTP_400_BAD_REQUEST)

            experiment.status = 'completed'
            experiment.end_date = timezone.now()
            experiment.save()

            return Response({
                'status': 'success',
                'message': 'Experiment stopped successfully'
            })

        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserContentExperimentAssignmentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing user experiment assignments."""
    from content.models import UserContentExperimentAssignment
    queryset = UserContentExperimentAssignment.objects.filter(is_deleted=False)
    permission_classes = [IsAuthenticated, NotDeletedUserPermission]

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        from content.serializers import UserContentExperimentAssignmentSerializer
        return UserContentExperimentAssignmentSerializer.filter(is_deleted=False)

    def get_queryset(self):
        """Filter assignments based on user permissions."""
        user = self.request.user
        if user.is_staff:
            return self.queryset.select_related('user', 'experiment')
        else:
            # Regular users can only see their own assignments
            return self.queryset.filter(
                user__user=user
            ).select_related('user', 'experiment')

class ContentExperimentMetricViewSet(viewsets.ModelViewSet):
    """ViewSet for managing experiment metrics."""
    from content.models import ContentExperimentMetric
    queryset = ContentExperimentMetric.objects.filter(is_deleted=False)
    permission_classes = [IsAuthenticated, NotDeletedUserPermission]

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        from content.serializers import ContentExperimentMetricSerializer
        return ContentExperimentMetricSerializer.filter(is_deleted=False)

    def get_queryset(self):
        """Filter metrics based on user permissions."""
        user = self.request.user
        if user.is_staff:
            return self.queryset.select_related('user', 'experiment')
        else:
            # Regular users can only see metrics for experiments they created
            return self.queryset.filter(
                experiment__created_by__user=user
            ).select_related('user', 'experiment')

class ContentExperimentResultViewSet(viewsets.ModelViewSet):
    """ViewSet for managing experiment results."""
    from content.models import ContentExperimentResult
    queryset = ContentExperimentResult.objects.filter(is_deleted=False)
    permission_classes = [IsAuthenticated, NotDeletedUserPermission]

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        from content.serializers import ContentExperimentResultSerializer
        return ContentExperimentResultSerializer.filter(is_deleted=False)

    def get_queryset(self):
        """Filter results based on user permissions."""
        user = self.request.user
        if user.is_staff:
            return self.queryset.select_related('experiment', 'analyzed_by')
        else:
            # Regular users can only see results for experiments they created
            return self.queryset.filter(
                experiment__created_by__user=user
            ).select_related('experiment', 'analyzed_by')

from rest_framework.decorators import api_view, permission_classes

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_content_experiment_assignment(request):
    """
    Get the current user's content experiment assignments.
    """
    from content.models import UserContentExperimentAssignment
    from accounts.models import UserProfile

    try:
        user_profile = get_object_or_404(UserProfile, user=request.user)

        assignments = UserContentExperimentAssignment.objects.filter(user=user_profile,
            experiment__status='active', is_deleted=False).select_related('experiment')

        assignment_data = []
        for assignment in assignments:
            assignment_data.append({
                'experiment_id': assignment.experiment.id,
                'experiment_name': assignment.experiment.name,
                'group': assignment.group,
                'algorithm': (assignment.experiment.control_algorithm
                            if assignment.group == 'control'
                            else assignment.experiment.test_algorithm),
                'assigned_at': assignment.assigned_at.isoformat()
            })

        return Response({
            'status': 'success',
            'assignments': assignment_data,
            'count': len(assignment_data)
        })

    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def content_experiment_dashboard(request):
    """
    Get overview dashboard data for content A/B testing experiments.
    """
    try:
        from content.models import (ContentExperiment,
                                  UserContentExperimentAssignment,
                                  ContentExperimentMetric)
        from django.utils import timezone
        from datetime import timedelta

        # Get active experiments
        active_experiments = ContentExperiment.objects.filter(status='active', is_deleted=False).count()

        # Get total assignments
        total_assignments = UserContentExperimentAssignment.objects.count()

        # Get recent metrics count
        recent_metrics = ContentExperimentMetric.objects.filter(
            recorded_at__gte=timezone.now() - timedelta(days=7), is_deleted=False
        ).count()

        # Get experiment summaries
        experiments = ContentExperiment.objects.all().order_by('-created_at')[:10]
        experiment_summaries = []

        for experiment in experiments:
            control_count = UserContentExperimentAssignment.objects.filter(experiment=experiment,
                group='control', is_deleted=False).count()

            test_count = UserContentExperimentAssignment.objects.filter(experiment=experiment,
                group='test', is_deleted=False).count()

            experiment_summaries.append({
                'id': experiment.id,
                'name': experiment.name,
                'status': experiment.status,
                'control_algorithm': experiment.control_algorithm,
                'test_algorithm': experiment.test_algorithm,
                'traffic_split': experiment.traffic_split,
                'control_users': control_count,
                'test_users': test_count,
                'total_users': control_count + test_count,
                'created_at': experiment.created_at.isoformat(),
                'start_date': (experiment.start_date.isoformat()
                             if experiment.start_date else None),
                'end_date': (experiment.end_date.isoformat()
                           if experiment.end_date else None)
            })

        return Response({
            'status': 'success',
            'dashboard': {
                'summary': {
                    'active_experiments': active_experiments,
                    'total_assignments': total_assignments,
                    'recent_metrics': recent_metrics
                },
                'experiments': experiment_summaries
            }
        })

    except ImportError:
        return Response({
            'status': 'error',
            'message': 'A/B Testing models not available. Please run migrations.'
        }, status=400)
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def record_content_interaction(request):
    """
    Record user interactions with content for A/B testing analysis.
    """
    from content.utils import record_content_interaction as record_interaction
    from content.models import Post, Comment
    from accounts.models import UserProfile
    from django.contrib.contenttypes.models import ContentType

    try:
        user_profile = get_object_or_404(UserProfile, user=request.user)

        interaction_type = request.data.get('type')
        content_type_name = request.data.get('content_type')
        content_id = request.data.get('content_id')
        metadata = request.data.get('metadata', {})

        # Validate interaction type
        valid_types = ['click', 'like', 'comment', 'share', 'view', 'engagement']
        if interaction_type not in valid_types:
            return Response({
                'status': 'error',
                'message': f'Invalid interaction type. Must be one of: {valid_types}'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get content object if provided
        content_object = None
        if content_type_name and content_id:
            try:
                if content_type_name == 'post':
                    content_object = Post.objects.get(id=content_id)
                elif content_type_name == 'comment':
                    content_object = Comment.objects.get(id=content_id)
                else:
                    return Response({
                        'status': 'error',
                        'message': 'Invalid content type. Must be "post" or "comment"'
                    }, status=status.HTTP_400_BAD_REQUEST)
            except (Post.DoesNotExist, Comment.DoesNotExist):
                return Response({
                    'status': 'error',
                    'message': 'Content object not found'
                }, status=status.HTTP_404_NOT_FOUND)

        # Record the interaction
        record_interaction(
            user_id=user_profile.id,
            interaction_type=interaction_type,
            content_object=content_object,
            metadata=metadata
        )

        return Response({
            'status': 'success',
            'message': 'Interaction recorded successfully'
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# =============================================================================
# INDIVIDUAL A/B TESTING API ENDPOINTS
# =============================================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_content_experiment(request, experiment_id):
    """Start a content A/B testing experiment."""
    from content.models import ContentExperiment
    from django.utils import timezone

    try:
        experiment = get_object_or_404(ContentExperiment, id=experiment_id)

        # Check permissions
        if not request.user.is_staff and experiment.created_by.user != request.user:
            return Response({
                'status': 'error',
                'message': 'Permission denied'
            }, status=status.HTTP_403_FORBIDDEN)

        if experiment.status != 'draft':
            return Response({
                'status': 'error',
                'message': 'Only draft experiments can be started'
            }, status=status.HTTP_400_BAD_REQUEST)

        experiment.status = 'active'
        experiment.start_date = timezone.now()
        experiment.save()

        return Response({
            'status': 'success',
            'message': 'Experiment started successfully',
            'experiment_id': str(experiment.id),
            'start_date': experiment.start_date.isoformat()
        })

    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def stop_content_experiment(request, experiment_id):
    """Stop a content A/B testing experiment."""
    from content.models import ContentExperiment
    from django.utils import timezone

    try:
        experiment = get_object_or_404(ContentExperiment, id=experiment_id)

        # Check permissions
        if not request.user.is_staff and experiment.created_by.user != request.user:
            return Response({
                'status': 'error',
                'message': 'Permission denied'
            }, status=status.HTTP_403_FORBIDDEN)

        if experiment.status not in ['active', 'running']:
            return Response({
                'status': 'error',
                'message': 'Only active/running experiments can be stopped'
            }, status=status.HTTP_400_BAD_REQUEST)

        experiment.status = 'completed'
        experiment.end_date = timezone.now()
        experiment.save()

        return Response({
            'status': 'success',
            'message': 'Experiment stopped successfully',
            'experiment_id': str(experiment.id),
            'end_date': experiment.end_date.isoformat()
        })

    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_content_experiment_stats(request, experiment_id):
    """Get statistics for a content A/B testing experiment."""
    from content.models import ContentExperiment
    from content.utils import get_content_experiment_stats

    try:
        experiment = get_object_or_404(ContentExperiment, id=experiment_id)

        # Check permissions
        if not request.user.is_staff and experiment.created_by.user != request.user:
            return Response({
                'status': 'error',
                'message': 'Permission denied'
            }, status=status.HTTP_403_FORBIDDEN)

        stats = get_content_experiment_stats(experiment_id)

        if stats:
            return Response({
                'status': 'success',
                'stats': stats
            })
        else:
            return Response({
                'status': 'error',
                'message': 'Unable to calculate stats for this experiment'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_algorithm(request, user_id):
    """Get the algorithm assigned to a user based on A/B testing."""
    from content.utils import get_content_algorithm_for_user
    from accounts.models import UserProfile
    from accounts.utils import get_active_profile_or_404

    try:
        # Check permissions
        if not request.user.is_staff:
            # Check if user is requesting their own algorithm
            try:
                requesting_user_profile = UserProfile.objects.get(user=request.user, is_deleted=False)
                if str(requesting_user_profile.id) != str(user_id):
                    return Response({
                        'status': 'error',
                        'message': 'Permission denied'
                    }, status=status.HTTP_403_FORBIDDEN)
            except UserProfile.DoesNotExist:
                return Response({
                    'status': 'error',
                    'message': 'User profile not found'
                }, status=status.HTTP_404_NOT_FOUND)

        user_profile = get_active_profile_or_404(id=user_id)
        algorithm = get_content_algorithm_for_user(user_profile.id)

        # Try to get the experiment info
        from content.models import UserContentExperimentAssignment
        assignment = UserContentExperimentAssignment.objects.filter(user=user_profile, is_deleted=False).first()

        response_data = {
            'status': 'success',
            'user_id': str(user_id),
            'algorithm': algorithm
        }

        if assignment:
            response_data['experiment_id'] = str(assignment.experiment.id)
            response_data['group'] = assignment.group

        return Response(response_data)

    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def content_experiment_dashboard(request):
    """Get dashboard data for content A/B testing experiments."""
    from content.models import (
        ContentExperiment, UserContentExperimentAssignment,
        ContentExperimentMetric
    )

    try:
        # Get user's experiments (if not staff, only own experiments)
        if request.user.is_staff:
            experiments = ContentExperiment.objects.all().order_by('-created_at')[:10]
        else:
            experiments = ContentExperiment.objects.filter(created_by__user=request.user, is_deleted=False).order_by('-created_at')[:10]

        experiment_data = []
        total_experiments = experiments.count()
        active_experiments = 0
        total_users_assigned = 0

        for experiment in experiments:
            if experiment.status == 'running':
                active_experiments += 1

            users_assigned = UserContentExperimentAssignment.objects.filter(experiment=experiment, is_deleted=False).count()
            total_users_assigned += users_assigned

            metrics_count = ContentExperimentMetric.objects.filter(experiment=experiment, is_deleted=False).count()

            experiment_data.append({
                'id': str(experiment.id),
                'name': experiment.name,
                'status': experiment.status,
                'control_algorithm': experiment.control_algorithm,
                'test_algorithm': experiment.test_algorithm,
                'traffic_split': experiment.traffic_split,
                'users_assigned': users_assigned,
                'metrics_recorded': metrics_count,
                'start_date': (experiment.start_date.isoformat()
                              if experiment.start_date else None),
                'end_date': (experiment.end_date.isoformat()
                            if experiment.end_date else None)
            })

        return Response({
            'status': 'success',
            'experiments': experiment_data,
            'summary': {
                'total_experiments': total_experiments,
                'active_experiments': active_experiments,
                'total_users_assigned': total_users_assigned,
                'avg_users_per_experiment': (total_users_assigned / total_experiments
                                           if total_experiments > 0 else 0)
            }
        })

    except Exception as e:
        return Response({
            'status': 'error',
            'message': 'A/B Testing models not available. Please run migrations.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DirectShareViewSet(viewsets.ModelViewSet):
    """CRUD for DirectShare model (private shares)."""
    queryset = DirectShare.objects.filter(is_deleted=False).select_related('sender__user', 'post__author__user')
    permission_classes = [IsAuthenticated, NotDeletedUserPermission]

    def get_serializer_class(self):
        return DirectShareCreateSerializer if self.action == 'create' else DirectShareSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_staff:
            return qs
        profile = self.request.user.profile
        return qs.filter(is_deleted=False, sender=profile)

    def perform_create(self, serializer):
        serializer.save()

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        share = self.get_object()
        profile = request.user.userprofile
        updated = DirectShareRecipient.objects.filter(direct_share=share, recipient=profile, is_read=False, is_deleted=False).update(is_read=True, read_at=timezone.now())
        return Response({'updated': updated})

class DirectShareDeliveryViewSet(viewsets.ReadOnlyModelViewSet):
    """List deliveries addressed to current user."""
    serializer_class = DirectShareRecipientSerializer
    permission_classes = [IsAuthenticated, NotDeletedUserPermission]

    def get_queryset(self):
        profile = self.request.user.profile
        return DirectShareRecipient.objects.filter(recipient=profile, is_deleted=False).select_related('direct_share__sender__user', 'direct_share__post')

