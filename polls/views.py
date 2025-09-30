"""Views for polls app with complete CRUD operations."""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q, Prefetch
from django.utils import timezone
from .models import Poll, PollOption, PollVote, PollVoter
from content.models import Post
from accounts.models import UserProfile
from .serializers import (
    PollSerializer,
    PollCreateUpdateSerializer,
    PollOptionSerializer,
    PollOptionCreateUpdateSerializer,
    PollVoteSerializer,
    PollVoteCreateSerializer,
    PollVoterSerializer
)


class PollViewSet(viewsets.ModelViewSet):
    """Complete CRUD operations for Poll model."""
    queryset = Poll.objects.filter(is_deleted=False)
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return PollCreateUpdateSerializer
        return PollSerializer

    def get_queryset(self):
        """Get queryset with optimized data loading, excluding soft-deleted polls."""
        return Poll.objects.select_related('post__author').prefetch_related(
            Prefetch('options', queryset=PollOption.objects.filter(is_deleted=False)),
            'votes'
        ).filter(is_deleted=False).annotate(
            calculated_votes=Count('votes'),
            calculated_voters=Count('votes__voter', distinct=True)
        )

    def perform_create(self, serializer):
        """Create poll and associated post if needed."""
        # If no post is provided, create one
        if 'post' not in serializer.validated_data:
            user_profile = get_object_or_404(UserProfile, user=self.request.user)
            post = Post.objects.create(
                author=user_profile,
                content=serializer.validated_data.get('question', 'Poll'),
                post_type='poll'
            )
            serializer.save(post=post)
        else:
            serializer.save()

    def perform_update(self, serializer):
        """Only allow post author to update poll."""
        poll = serializer.instance
        if poll.post.author.user != self.request.user and not self.request.user.is_staff:
            raise PermissionError("You can only edit your own polls")
        serializer.save()

    def perform_destroy(self, instance):
        """Only allow post author to delete poll."""
        if instance.post.author.user != self.request.user and not self.request.user.is_staff:
            raise PermissionError("You can only delete your own polls")

        # Soft delete the poll instead of hard delete
        instance.is_deleted = True
        instance.save()

        # Also soft delete all poll options
        instance.options.update(is_deleted=True)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def vote(self, request, pk=None):
        """Vote in a poll."""
        poll = self.get_object()
        option_id = request.data.get('option_id')

        if not option_id:
            return Response(
                {'error': 'option_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            option = PollOption.objects.get(id=option_id, poll=poll)
        except PollOption.DoesNotExist:
            return Response(
                {'error': 'Invalid option'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if user already voted for this option
        existing_vote = PollVote.objects.filter(poll=poll,
            option=option,
            voter=request.user, is_deleted=False).first()

        if existing_vote:
            return Response(
                {'error': 'You have already voted for this option'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # For single-choice polls, check if user has voted for any option
        if not poll.multiple_choice:
            existing_any_vote = PollVote.objects.filter(poll=poll,
                voter=request.user, is_deleted=False).first()

            if existing_any_vote:
                return Response(
                    {'error': 'You have already voted in this poll. This poll allows only one vote per user.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Create vote using serializer for validation
        vote_data = {'poll': poll.id, 'option': option.id}
        vote_serializer = PollVoteCreateSerializer(
            data=vote_data,
            context={'request': request}
        )

        if vote_serializer.is_valid():
            try:
                # Get IP and user agent
                ip_address = request.META.get('REMOTE_ADDR')
                user_agent = request.META.get('HTTP_USER_AGENT', '')

                vote = vote_serializer.save(
                    voter=request.user,
                    ip_address=ip_address,
                    user_agent=user_agent
                )

                # Update vote counts
                option.votes_count += 1
                option.save()

                poll.total_votes += 1
                poll.save()

                # Update or create voter record
                voter, created = PollVoter.objects.get_or_create(
                    poll=poll,
                    voter=request.user,
                    defaults={'votes_count': 1}
                )
                if not created:
                    voter.votes_count += 1
                    voter.save()

                # Update unique voters count
                poll.voters_count = poll.unique_voters.count()
                poll.save()

                return Response(
                    {'message': 'Vote recorded successfully'},
                    status=status.HTTP_201_CREATED
                )

            except Exception as e:
                return Response(
                    {'error': f'Failed to record vote: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response(vote_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['delete'], permission_classes=[IsAuthenticated])
    def remove_vote(self, request, pk=None):
        """Remove a vote from a poll."""
        poll = self.get_object()
        option_id = request.data.get('option_id')

        if not option_id:
            return Response(
                {'error': 'option_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            vote = PollVote.objects.get(
                poll=poll,
                option_id=option_id,
                voter=request.user
            )
            option = vote.option

            # Remove vote
            vote.delete()

            # Update counts
            option.votes_count -= 1
            option.save()

            poll.total_votes -= 1
            poll.save()

            # Update voter record
            try:
                voter = PollVoter.objects.get(poll=poll, voter=request.user, is_deleted=False)
                voter.votes_count -= 1
                if voter.votes_count <= 0:
                    voter.delete()
                else:
                    voter.save()
            except PollVoter.DoesNotExist:
                pass

            # Update unique voters count
            poll.voters_count = poll.unique_voters.count()
            poll.save()

            return Response(
                {'message': 'Vote removed successfully'},
                status=status.HTTP_200_OK
            )

        except PollVote.DoesNotExist:
            return Response(
                {'error': 'Vote not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def close(self, request, pk=None):
        """Close a poll (only by poll creator or admin)."""
        poll = self.get_object()

        if poll.post.author.user != request.user and not request.user.is_staff:
            return Response(
                {'error': 'You can only close your own polls'},
                status=status.HTTP_403_FORBIDDEN
            )

        poll.is_closed = True
        poll.is_active = False
        poll.save()

        return Response(
            {'message': 'Poll closed successfully'},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['get'])
    def results(self, request, pk=None):
        """Get detailed poll results."""
        poll = self.get_object()

        # If poll is anonymous and user is not the creator, hide voter details
        if poll.anonymous_voting and poll.post.author.user != request.user:
            options_data = []
            for option in poll.options.all():
                options_data.append({
                    'id': option.id,
                    'text': option.text,
                    'votes_count': option.votes_count,
                    'vote_percentage': option.vote_percentage
                })
        else:
            options_data = PollOptionSerializer(
                poll.options.all(),
                many=True,
                context={'request': request}
            ).data

        return Response({
            'poll': self.get_serializer(poll).data,
            'options': options_data,
            'total_votes': poll.total_votes,
            'voters_count': poll.voters_count
        })

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_polls(self, request):
        """Get current user's polls."""
        user_profile = get_object_or_404(UserProfile, user=request.user)
        polls = Poll.objects.filter(post__author=user_profile, is_deleted=False).order_by('-created_at')
        serializer = self.get_serializer(polls, many=True)
        return Response(serializer.data)


class PollOptionViewSet(viewsets.ModelViewSet):
    """Complete CRUD operations for PollOption model."""
    queryset = PollOption.objects.filter(is_deleted=False)
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        """Get queryset excluding soft-deleted options."""
        return PollOption.objects.filter(is_deleted=False)

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return PollOptionCreateUpdateSerializer
        return PollOptionSerializer

    def perform_create(self, serializer):
        """Only allow poll creator to add options."""
        poll = serializer.validated_data.get('poll')
        if poll and poll.post.author.user != self.request.user and not self.request.user.is_staff:
            raise PermissionError("You can only add options to your own polls")
        serializer.save()

    def perform_update(self, serializer):
        """Only allow poll creator to update options."""
        option = serializer.instance
        if option.poll.post.author.user != self.request.user and not self.request.user.is_staff:
            raise PermissionError("You can only edit options in your own polls")
        serializer.save()

    def perform_destroy(self, instance):
        """Only allow poll creator to delete options."""
        if instance.poll.post.author.user != self.request.user and not self.request.user.is_staff:
            raise PermissionError("You can only delete options from your own polls")

        # Soft delete the option instead of hard delete
        instance.is_deleted = True
        instance.save()


class PollVoteViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only operations for PollVote model."""
    queryset = PollVote.objects.filter(is_deleted=False)
    serializer_class = PollVoteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter votes based on user permissions and poll anonymity."""
        if self.request.user.is_staff:
            return PollVote.objects.all()

        # Users can only see their own votes and votes in non-anonymous polls
        return PollVote.objects.filter(Q(voter=self.request.user, is_deleted=False) |
            Q(poll__anonymous_voting=False)
        ).distinct()


class PollVoterViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only operations for PollVoter model."""
    queryset = PollVoter.objects.filter(is_deleted=False)
    serializer_class = PollVoterSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter voters based on user permissions."""
        if self.request.user.is_staff:
            return PollVoter.objects.all()

        # Users can see voters in their own polls and non-anonymous polls
        user_profile = get_object_or_404(UserProfile, user=self.request.user)
        return PollVoter.objects.filter(Q(poll__post__author=user_profile, is_deleted=False) |
            Q(poll__anonymous_voting=False)
        ).distinct()
