"""Admin views for managing users and system administration."""

from rest_framework import viewsets, status, permissions, filters, serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth.models import User
from django.db.models import Q, Count
from django.utils import timezone
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from datetime import timedelta, datetime
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

from .models import UserProfile, AdminProfile, SupportTicket, SupportMessage
from .serializers import UserProfileSerializer, UserDetailSerializer
from core.models import AdministrativeDivision, Country


def send_suspension_email(user, suspension_data):
    """
    Send suspension notification email to user.
    """
    try:
        # Préparer les données pour le template
        context = {
            'user_name': user.get_full_name() or user.username,
            'username': user.username,
            'user_email': user.email,
            'suspension_date': timezone.now().strftime('%d/%m/%Y à %H:%M'),
            'suspension_reason': suspension_data.get('reason', 'Non spécifiée'),
            'suspension_details': suspension_data.get('details', ''),
            'current_year': timezone.now().year,
            'terms_url': 'https://citinfos.com/terms',
            'privacy_url': 'https://citinfos.com/privacy',
        }
        
        # Calculer la durée et date de fin si applicable
        duration_days = suspension_data.get('duration', 'indefinite')
        if duration_days == 'indefinite':
            context['duration'] = 'Indéfinie'
            context['end_date'] = None
        else:
            try:
                days = int(duration_days)
                end_date = timezone.now() + timedelta(days=days)
                context['duration'] = f'{days} jour{"s" if days > 1 else ""}'
                context['end_date'] = end_date.strftime('%d/%m/%Y à %H:%M')
            except ValueError:
                context['duration'] = 'Indéfinie'
                context['end_date'] = None
        
        # Générer le contenu HTML de l'email
        html_content = render_to_string('emails/user_suspension.html', context)
        
        # Envoyer l'email
        subject = f'Suspension de votre compte CitInfos - {user.username}'
        
        send_mail(
            subject=subject,
            message=f'''
Bonjour {context['user_name']},

Votre compte a été suspendu.

Raison: {context['suspension_reason']}
Durée: {context['duration']}

Pour plus d'informations, contactez-nous à support@citinfos.com

L'équipe CitInfos
            ''',
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@citinfos.com'),
            recipient_list=[user.email],
            html_message=html_content,
            fail_silently=False,
        )
        
        return True
        
    except Exception as e:
        # Log l'erreur mais ne pas faire échouer la suspension
        print(f"Erreur lors de l'envoi de l'email de suspension: {e}")
        return False


class IsAdminUser(permissions.BasePermission):
    """
    Permission class to check if user is an admin.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user has admin role in UserProfile
        try:
            profile = request.user.profile
            if profile.role == 'admin':
                return True
        except (AttributeError, UserProfile.DoesNotExist):
            pass
        
        # Also check Django admin permissions
        return request.user.is_staff or request.user.is_superuser


# =============================================================================
# MUNICIPALITY MANAGEMENT ENDPOINTS
# =============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_municipalities_list(request):
    """
    Get list of municipalities with basic information and activity stats.
    """
    try:
        # Base queryset for municipalities (admin_level=3 or 4 depending on country)
        municipalities = AdministrativeDivision.objects.select_related('country', 'parent').filter(
            admin_level__in=[3, 4],  # Municipalities and communes
            country__isnull=False
        ).order_by('name')
        
        # Apply search filter
        search = request.query_params.get('search')
        if search:
            municipalities = municipalities.filter(
                Q(name__icontains=search) | 
                Q(parent__name__icontains=search) |
                Q(country__name__icontains=search)
            )
        
        # Apply province/country filter
        country_filter = request.query_params.get('country')
        if country_filter:
            municipalities = municipalities.filter(country__name=country_filter)
        
        # Apply province filter (for Canada, this would be Quebec)
        province_filter = request.query_params.get('province')
        if province_filter:
            municipalities = municipalities.filter(
                Q(parent__name__icontains=province_filter) |
                Q(parent__parent__name__icontains=province_filter)
            )
        
        # Pagination
        page_size = min(int(request.query_params.get('page_size', 20)), 100)
        page = int(request.query_params.get('page', 1))
        start = (page - 1) * page_size
        end = start + page_size
        
        total_count = municipalities.count()
        municipalities_page = municipalities[start:end]
        
        # Prepare municipality data with basic stats
        municipality_data = []
        for municipality in municipalities_page:
            # Get basic municipality info
            data = {
                'id': str(municipality.id),
                'name': municipality.name,
                'admin_level': municipality.admin_level,
                'admin_code': municipality.admin_code,
                'country': {
                    'name': municipality.country.name,
                    'iso3': municipality.country.iso3,
                    'iso2': municipality.country.iso2
                },
                'province': None,
                'region': None,
                'type': 'Municipalité' if municipality.admin_level == 4 else 'Commune',
                'population': None,  # TODO: Add population field if available
                'created_at': municipality.created_at,
                'updated_at': municipality.updated_at,
            }
            
            # Get parent hierarchy (region, province, etc.)
            if municipality.parent:
                if municipality.parent.admin_level == 1:  # Province level
                    data['province'] = municipality.parent.name
                elif municipality.parent.admin_level == 2:  # Region/MRC level
                    data['region'] = municipality.parent.name
                    if municipality.parent.parent and municipality.parent.parent.admin_level == 1:
                        data['province'] = municipality.parent.parent.name
                elif municipality.parent.admin_level == 3:  # MRC for level 4 municipalities
                    data['region'] = municipality.parent.name
                    if municipality.parent.parent:
                        if municipality.parent.parent.admin_level == 1:
                            data['province'] = municipality.parent.parent.name
                        elif municipality.parent.parent.admin_level == 2:
                            # Skip intermediate region level
                            if municipality.parent.parent.parent and municipality.parent.parent.parent.admin_level == 1:
                                data['province'] = municipality.parent.parent.parent.name
            
            municipality_data.append(data)
        
        return Response({
            'results': municipality_data,
            'count': len(municipality_data),
            'total': total_count,
            'page': page,
            'page_size': page_size,
            'has_next': end < total_count,
            'has_previous': page > 1,
        })
        
    except Exception as e:
        return Response(
            {'error': 'Failed to fetch municipalities', 'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_municipality_stats(request, municipality_id):
    """
    Get detailed statistics for a specific municipality.
    """
    try:
        municipality = AdministrativeDivision.objects.select_related('country', 'parent').get(
            id=municipality_id
        )
        
        # TODO: Replace with actual statistics from posts, users, etc.
        # For now, return mock data that matches the frontend expectations
        stats = {
            'posts_count': 0,  # TODO: Count posts for this municipality
            'active_users_count': 0,  # TODO: Count active users in this municipality
            'total_users_count': 0,  # TODO: Count total users in this municipality
            'last_activity': timezone.now(),  # TODO: Get last activity timestamp
            'growth_rate': 0.0,  # TODO: Calculate growth rate
            'engagement_score': 0.0,  # TODO: Calculate engagement score
            'popular_topics': [],  # TODO: Get popular topics/hashtags
            'recent_activity': [],  # TODO: Get recent activity summary
        }
        
        # Count users in this municipality (if we have location data)
        try:
            users_in_municipality = UserProfile.objects.filter(
                administrative_division=municipality,
                is_deleted=False
            )
            stats['total_users_count'] = users_in_municipality.count()
            
            # Count active users (last login within 7 days)
            seven_days_ago = timezone.now() - timedelta(days=7)
            stats['active_users_count'] = users_in_municipality.filter(
                user__last_login__gte=seven_days_ago
            ).count()
            
        except Exception as e:
            print(f"Error counting users for municipality {municipality.name}: {e}")
        
        return Response({
            'municipality': {
                'id': str(municipality.id),
                'name': municipality.name,
                'admin_level': municipality.admin_level,
                'country': municipality.country.name,
                'region': municipality.parent.name if municipality.parent else None,
            },
            'stats': stats,
            'timestamp': timezone.now().isoformat()
        })
        
    except AdministrativeDivision.DoesNotExist:
        return Response(
            {'error': 'Municipality not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': 'Failed to fetch municipality statistics', 'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_municipality_active_users(request, municipality_id):
    """
    Get most active users in a specific municipality.
    """
    try:
        municipality = AdministrativeDivision.objects.get(id=municipality_id)
        
        # Get users in this municipality
        users_in_municipality = UserProfile.objects.select_related('user').filter(
            administrative_division=municipality,
            is_deleted=False,
            user__is_active=True
        )
        
        # TODO: Order by actual activity metrics (posts count, engagement, etc.)
        # For now, order by recent activity and last login
        active_users = users_in_municipality.order_by(
            '-last_active', '-user__last_login'
        )[:10]  # Top 10 most active users
        
        users_data = []
        for user_profile in active_users:
            user = user_profile.user
            users_data.append({
                'id': user.id,
                'username': user.username,
                'full_name': f"{user.first_name} {user.last_name}".strip() or user.username,
                'profile_picture': user_profile.profile_picture.url if user_profile.profile_picture else None,
                'posts_count': 0,  # TODO: Count actual posts
                'last_active': user_profile.last_active,
                'date_joined': user.date_joined,
                'is_verified': user_profile.is_verified,
                'engagement_score': user_profile.engagement_score,
            })
        
        return Response({
            'municipality': {
                'id': str(municipality.id),
                'name': municipality.name,
            },
            'active_users': users_data,
            'count': len(users_data),
            'timestamp': timezone.now().isoformat()
        })
        
    except AdministrativeDivision.DoesNotExist:
        return Response(
            {'error': 'Municipality not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': 'Failed to fetch active users', 'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_municipalities_overview(request):
    """
    Get overview statistics for all municipalities.
    """
    try:
        # Get basic counts
        total_municipalities = AdministrativeDivision.objects.filter(
            admin_level__in=[3, 4]
        ).count()
        
        # Get municipalities by country
        by_country = AdministrativeDivision.objects.filter(
            admin_level__in=[3, 4]
        ).values('country__name', 'country__iso3').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Get total users across all municipalities
        total_users_with_location = UserProfile.objects.filter(
            administrative_division__isnull=False,
            is_deleted=False
        ).count()
        
        # Calculate coverage rate
        total_users = UserProfile.objects.filter(is_deleted=False).count()
        location_coverage = (total_users_with_location / total_users * 100) if total_users > 0 else 0
        
        return Response({
            'total_municipalities': total_municipalities,
            'by_country': list(by_country),
            'total_users_with_location': total_users_with_location,
            'location_coverage_rate': round(location_coverage, 2),
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        return Response(
            {'error': 'Failed to fetch municipalities overview', 'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# =============================================================================
# SUPPORT SYSTEM ENDPOINTS
# =============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_support_tickets_list(request):
    """
    Get list of support tickets with filtering options.
    """
    try:
        # Base queryset
        tickets = SupportTicket.objects.select_related('user', 'assigned_to').filter(
            is_deleted=False
        ).order_by('-created_at')
        
        # Apply filters
        status_filter = request.query_params.get('status')
        if status_filter:
            tickets = tickets.filter(status=status_filter)
        
        priority_filter = request.query_params.get('priority')
        if priority_filter:
            tickets = tickets.filter(priority=priority_filter)
        
        category_filter = request.query_params.get('category')
        if category_filter:
            tickets = tickets.filter(category=category_filter)
        
        assigned_filter = request.query_params.get('assigned')
        if assigned_filter == 'unassigned':
            tickets = tickets.filter(assigned_to__isnull=True)
        elif assigned_filter == 'assigned':
            tickets = tickets.filter(assigned_to__isnull=False)
        elif assigned_filter == 'me':
            tickets = tickets.filter(assigned_to=request.user)
        
        search = request.query_params.get('search')
        if search:
            tickets = tickets.filter(
                Q(ticket_number__icontains=search) |
                Q(subject__icontains=search) |
                Q(user_name__icontains=search) |
                Q(user_email__icontains=search)
            )
        
        # Pagination
        page_size = min(int(request.query_params.get('page_size', 20)), 100)
        page = int(request.query_params.get('page', 1))
        start = (page - 1) * page_size
        end = start + page_size
        
        total_count = tickets.count()
        tickets_page = tickets[start:end]
        
        # Serialize tickets
        tickets_data = []
        for ticket in tickets_page:
            # Count unread messages
            unread_count = ticket.messages.filter(
                is_read_by_admin=False,
                message_type='user_message'
            ).count()
            
            tickets_data.append({
                'id': str(ticket.id),
                'ticket_number': ticket.ticket_number,
                'subject': ticket.subject,
                'status': ticket.status,
                'priority': ticket.priority,
                'category': ticket.category,
                'user_name': ticket.user_name,
                'user_email': ticket.user_email,
                'assigned_to': {
                    'id': ticket.assigned_to.id,
                    'username': ticket.assigned_to.username,
                    'full_name': f"{ticket.assigned_to.first_name} {ticket.assigned_to.last_name}".strip()
                } if ticket.assigned_to else None,
                'created_at': ticket.created_at,
                'updated_at': ticket.updated_at,
                'is_overdue': ticket.is_overdue,
                'unread_messages': unread_count,
                'total_messages': ticket.messages.filter(is_deleted=False).count(),
            })
        
        return Response({
            'results': tickets_data,
            'count': len(tickets_data),
            'total': total_count,
            'page': page,
            'page_size': page_size,
            'has_next': end < total_count,
            'has_previous': page > 1,
        })
        
    except Exception as e:
        return Response(
            {'error': 'Failed to fetch support tickets', 'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_support_ticket_detail(request, ticket_id):
    """
    Get detailed information about a specific support ticket.
    """
    try:
        ticket = SupportTicket.objects.select_related('user', 'assigned_to').get(
            id=ticket_id, is_deleted=False
        )
        
        # Get all messages for this ticket
        messages = ticket.messages.select_related('sender').filter(
            is_deleted=False
        ).order_by('created_at')
        
        # Mark messages as read by admin
        messages.filter(is_read_by_admin=False).update(is_read_by_admin=True)
        
        # Serialize messages
        messages_data = []
        for message in messages:
            messages_data.append({
                'id': str(message.id),
                'content': message.content,
                'message_type': message.message_type,
                'is_internal': message.is_internal,
                'sender': {
                    'id': message.sender.id,
                    'username': message.sender.username,
                    'full_name': f"{message.sender.first_name} {message.sender.last_name}".strip(),
                    'is_admin': hasattr(message.sender, 'profile') and message.sender.profile.role == 'admin'
                } if message.sender else None,
                'created_at': message.created_at,
                'is_read_by_user': message.is_read_by_user,
                'is_read_by_admin': message.is_read_by_admin,
            })
        
        # Serialize ticket
        ticket_data = {
            'id': str(ticket.id),
            'ticket_number': ticket.ticket_number,
            'subject': ticket.subject,
            'description': ticket.description,
            'status': ticket.status,
            'priority': ticket.priority,
            'category': ticket.category,
            'user_name': ticket.user_name,
            'user_email': ticket.user_email,
            'user': {
                'id': ticket.user.id,
                'username': ticket.user.username,
                'full_name': f"{ticket.user.first_name} {ticket.user.last_name}".strip(),
            } if ticket.user else None,
            'assigned_to': {
                'id': ticket.assigned_to.id,
                'username': ticket.assigned_to.username,
                'full_name': f"{ticket.assigned_to.first_name} {ticket.assigned_to.last_name}".strip()
            } if ticket.assigned_to else None,
            'created_at': ticket.created_at,
            'updated_at': ticket.updated_at,
            'resolved_at': ticket.resolved_at,
            'closed_at': ticket.closed_at,
            'is_overdue': ticket.is_overdue,
            'browser_info': ticket.browser_info,
            'ip_address': ticket.ip_address,
            'messages': messages_data,
        }
        
        return Response(ticket_data)
        
    except SupportTicket.DoesNotExist:
        return Response(
            {'error': 'Support ticket not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': 'Failed to fetch ticket details', 'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_support_ticket_reply(request, ticket_id):
    """
    Add a reply to a support ticket.
    """
    try:
        ticket = SupportTicket.objects.get(id=ticket_id, is_deleted=False)
        
        content = request.data.get('content', '').strip()
        is_internal = request.data.get('is_internal', False)
        
        if not content:
            return Response(
                {'error': 'Message content is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create message
        message = SupportMessage.objects.create(
            ticket=ticket,
            sender=request.user,
            content=content,
            message_type='admin_reply',
            is_internal=is_internal,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            is_read_by_admin=True,  # Admin messages are auto-read by admin
        )
        
        # Update ticket status if it was resolved/closed
        if ticket.status in ['resolved', 'closed']:
            ticket.status = 'in_progress'
            ticket.save(update_fields=['status'])
        
        # TODO: Send email notification to user if not internal message
        
        return Response({
            'message': 'Reply added successfully',
            'message_id': str(message.id),
            'ticket_status': ticket.status,
        })
        
    except SupportTicket.DoesNotExist:
        return Response(
            {'error': 'Support ticket not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': 'Failed to add reply', 'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PATCH'])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_support_ticket_update(request, ticket_id):
    """
    Update support ticket status, priority, assignment, etc.
    """
    try:
        ticket = SupportTicket.objects.get(id=ticket_id, is_deleted=False)
        
        # Track changes for system messages
        changes = []
        
        # Update status
        new_status = request.data.get('status')
        if new_status and new_status != ticket.status:
            old_status = ticket.get_status_display()
            ticket.status = new_status
            
            # Set resolved/closed timestamps
            if new_status == 'resolved' and not ticket.resolved_at:
                ticket.resolved_at = timezone.now()
            elif new_status == 'closed' and not ticket.closed_at:
                ticket.closed_at = timezone.now()
            
            changes.append(f"Statut changé de '{old_status}' à '{ticket.get_status_display()}'")
        
        # Update priority
        new_priority = request.data.get('priority')
        if new_priority and new_priority != ticket.priority:
            old_priority = ticket.get_priority_display()
            ticket.priority = new_priority
            changes.append(f"Priorité changée de '{old_priority}' à '{ticket.get_priority_display()}'")
        
        # Update assignment
        new_assigned_to_id = request.data.get('assigned_to')
        if new_assigned_to_id is not None:
            if new_assigned_to_id == '':
                # Unassign ticket
                if ticket.assigned_to:
                    changes.append(f"Ticket désassigné de {ticket.assigned_to.username}")
                    ticket.assigned_to = None
            else:
                # Assign to admin
                try:
                    new_assignee = User.objects.get(id=new_assigned_to_id, profile__role='admin')
                    if ticket.assigned_to != new_assignee:
                        old_assignee = ticket.assigned_to.username if ticket.assigned_to else 'Non assigné'
                        ticket.assigned_to = new_assignee
                        changes.append(f"Ticket assigné de '{old_assignee}' à '{new_assignee.username}'")
                except User.DoesNotExist:
                    return Response(
                        {'error': 'Admin user not found'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
        
        ticket.save()
        
        # Create system message for changes
        if changes:
            SupportMessage.objects.create(
                ticket=ticket,
                sender=request.user,
                content='\n'.join(changes),
                message_type='status_change',
                is_internal=True,
                is_read_by_admin=True,
            )
        
        return Response({
            'message': 'Ticket updated successfully',
            'changes': changes,
        })
        
    except SupportTicket.DoesNotExist:
        return Response(
            {'error': 'Support ticket not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': 'Failed to update ticket', 'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_support_stats(request):
    """
    Get support ticket statistics for admin dashboard.
    """
    try:
        # Basic counts
        total_tickets = SupportTicket.objects.filter(is_deleted=False).count()
        open_tickets = SupportTicket.objects.filter(
            status__in=['open', 'in_progress', 'waiting_user'],
            is_deleted=False
        ).count()
        
        # Tickets by status
        status_stats = SupportTicket.objects.filter(
            is_deleted=False
        ).values('status').annotate(count=Count('id'))
        
        # Tickets by priority
        priority_stats = SupportTicket.objects.filter(
            is_deleted=False
        ).values('priority').annotate(count=Count('id'))
        
        # Overdue tickets
        overdue_tickets = []
        for ticket in SupportTicket.objects.filter(
            status__in=['open', 'in_progress', 'waiting_user'],
            is_deleted=False
        ):
            if ticket.is_overdue:
                overdue_tickets.append(ticket)
        
        # Recent activity
        recent_tickets = SupportTicket.objects.filter(
            is_deleted=False
        ).order_by('-created_at')[:5]
        
        recent_data = []
        for ticket in recent_tickets:
            recent_data.append({
                'id': str(ticket.id),
                'ticket_number': ticket.ticket_number,
                'subject': ticket.subject,
                'status': ticket.status,
                'created_at': ticket.created_at,
            })
        
        return Response({
            'total_tickets': total_tickets,
            'open_tickets': open_tickets,
            'overdue_count': len(overdue_tickets),
            'status_distribution': {item['status']: item['count'] for item in status_stats},
            'priority_distribution': {item['priority']: item['count'] for item in priority_stats},
            'recent_tickets': recent_data,
            'timestamp': timezone.now().isoformat(),
        })
        
    except Exception as e:
        return Response(
            {'error': 'Failed to fetch support statistics', 'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# =============================================================================
# PUBLIC SUPPORT ENDPOINTS
# =============================================================================

@api_view(['POST'])
@permission_classes([])  # No authentication required
def public_create_support_ticket(request):
    """
    Create a support ticket from public contact form.
    """
    try:
        # Extract data from request
        user_name = request.data.get('name', '').strip()
        user_email = request.data.get('email', '').strip()
        subject = request.data.get('subject', '').strip()
        description = request.data.get('message', '').strip()
        category = request.data.get('category', 'other')
        
        # Validation
        if not all([user_name, user_email, subject, description]):
            return Response(
                {'error': 'Tous les champs sont requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate email format
        try:
            validate_email(user_email)
        except ValidationError:
            return Response(
                {'error': 'Format d\'email invalide'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user exists
        user = None
        try:
            user = User.objects.get(email=user_email)
        except User.DoesNotExist:
            pass  # Anonymous ticket
        
        # Create support ticket
        ticket = SupportTicket.objects.create(
            user=user,
            user_email=user_email,
            user_name=user_name,
            subject=subject,
            description=description,
            category=category,
            priority='medium',  # Default priority for public tickets
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            browser_info={
                'remote_addr': request.META.get('REMOTE_ADDR'),
                'http_user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'http_referer': request.META.get('HTTP_REFERER', ''),
            }
        )
        
        # Create initial system message
        SupportMessage.objects.create(
            ticket=ticket,
            sender=None,  # System message
            content=f"Ticket créé via le formulaire de contact public.",
            message_type='system_note',
            is_internal=True,
            is_read_by_admin=False,
        )
        
        # TODO: Send confirmation email to user
        # TODO: Send notification email to admins
        
        return Response({
            'message': 'Votre demande de support a été créée avec succès',
            'ticket_number': ticket.ticket_number,
            'ticket_id': str(ticket.id),
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response(
            {'error': 'Erreur lors de la création du ticket', 'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    """
    Send suspension notification email to user.
    """
    try:
        # Préparer les données pour le template
        context = {
            'user_name': user.get_full_name() or user.username,
            'username': user.username,
            'user_email': user.email,
            'suspension_date': timezone.now().strftime('%d/%m/%Y à %H:%M'),
            'suspension_reason': suspension_data.get('reason', 'Non spécifiée'),
            'suspension_details': suspension_data.get('details', ''),
            'current_year': timezone.now().year,
            'terms_url': 'https://citinfos.com/terms',
            'privacy_url': 'https://citinfos.com/privacy',
        }
        
        # Calculer la durée et date de fin si applicable
        duration_days = suspension_data.get('duration', 'indefinite')
        if duration_days == 'indefinite':
            context['duration'] = 'Indéfinie'
            context['end_date'] = None
        else:
            try:
                days = int(duration_days)
                end_date = timezone.now() + timedelta(days=days)
                context['duration'] = f'{days} jour{"s" if days > 1 else ""}'
                context['end_date'] = end_date.strftime('%d/%m/%Y à %H:%M')
            except ValueError:
                context['duration'] = 'Indéfinie'
                context['end_date'] = None
        
        # Générer le contenu HTML de l'email
        html_content = render_to_string('emails/user_suspension.html', context)
        
        # Envoyer l'email
        subject = f'Suspension de votre compte CitInfos - {user.username}'
        
        send_mail(
            subject=subject,
            message=f'''
Bonjour {context['user_name']},

Votre compte a été suspendu.

Raison: {context['suspension_reason']}
Durée: {context['duration']}

Pour plus d'informations, contactez-nous à support@citinfos.com

L'équipe CitInfos
            ''',
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@citinfos.com'),
            recipient_list=[user.email],
            html_message=html_content,
            fail_silently=False,
        )
        
        return True
        
    except Exception as e:
        # Log l'erreur mais ne pas faire échouer la suspension
        print(f"Erreur lors de l'envoi de l'email de suspension: {e}")
        return False


class IsAdminUser(permissions.BasePermission):
    """
    Permission class to check if user is an admin.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user has admin role in UserProfile
        try:
            profile = request.user.profile
            if profile.role == 'admin':
                return True
        except (AttributeError, UserProfile.DoesNotExist):
            pass
        
        # Also check Django admin permissions
        return request.user.is_staff or request.user.is_superuser


class AdminUserProfileSerializer(serializers.ModelSerializer):
    """Custom serializer for admin user management."""
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    date_joined = serializers.DateTimeField(source='user.date_joined', read_only=True)
    last_login = serializers.DateTimeField(source='user.last_login', read_only=True)
    is_active = serializers.BooleanField(source='user.is_active', read_only=True)
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'user_id', 'username', 'email', 'first_name', 'last_name', 
            'full_name', 'date_joined', 'last_login', 'is_active',
            'role', 'is_verified', 'is_suspended', 'phone_number',
            'created_at', 'updated_at', 'last_active'
        ]
    
    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip()


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_test(request):
    """Simple test endpoint to verify admin routing works."""
    return Response({
        'message': 'Admin endpoint is working!',
        'user': request.user.username if request.user.is_authenticated else 'Anonymous',
        'timestamp': timezone.now().isoformat()
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_users_list(request):
    """Simple admin users list endpoint with filtering support."""
    try:
        # Paramètres de requête
        search = request.GET.get('search', '').strip()
        role = request.GET.get('role', '').strip()
        page = int(request.GET.get('page', 1))
        page_size = min(int(request.GET.get('page_size', 10)), 100)  # Max 100 par page
        
        # Base queryset
        queryset = User.objects.select_related('profile').filter(profile__is_deleted=False)
        
        # Filtrage par recherche (username, email, nom, prénom)
        if search:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
        
        # Filtrage par rôle
        if role:
            queryset = queryset.filter(profile__role=role)
        
        # Ordre par date de création (plus récents en premier)
        queryset = queryset.order_by('-date_joined')
        
        # Compter le total sur le queryset filtré
        total_count = queryset.count()
        
        # Pagination
        start = (page - 1) * page_size
        end = start + page_size
        users_page = queryset[start:end]
        
        user_data = []
        
        for user in users_page:
            user_data.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'date_joined': user.date_joined.isoformat(),
                'is_active': user.is_active,
                'role': user.profile.role if hasattr(user, 'profile') else 'normal',
                'is_verified': user.profile.is_verified if hasattr(user, 'profile') else False,
                'phone_number': user.profile.phone_number if hasattr(user, 'profile') else '',
                'location': user.profile.location if hasattr(user, 'profile') else None,
                'last_active': user.profile.last_active.isoformat() if hasattr(user, 'profile') and user.profile.last_active else None,
            })
        
        return Response({
            'results': user_data,
            'count': total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': (total_count + page_size - 1) // page_size,
            'debug': {
                'search': search,
                'role': role,
                'filters_applied': bool(search or role)
            }
        })
        
    except Exception as e:
        return Response(
            {'error': 'Failed to fetch users', 'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class AdminUserPagination(PageNumberPagination):
    """Custom pagination for admin user list."""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class AdminUserListViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Admin-only viewset for managing users.
    Provides list and detail views with filtering and searching.
    """
    serializer_class = AdminUserProfileSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    pagination_class = AdminUserPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name']
    ordering_fields = ['user__date_joined', 'user__last_login', 'updated_at']
    ordering = ['-user__date_joined']  # Default ordering

    def get_queryset(self):
        """Get all user profiles with related data."""
        queryset = UserProfile.objects.select_related('user').filter(is_deleted=False)
        
        # Filter by role if specified
        role = self.request.query_params.get('role')
        if role:
            queryset = queryset.filter(role=role)
        
        # Filter by verification status
        is_verified = self.request.query_params.get('is_verified')
        if is_verified is not None:
            is_verified_bool = is_verified.lower() in ['true', '1', 'yes']
            queryset = queryset.filter(is_verified=is_verified_bool)
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from:
            queryset = queryset.filter(user__date_joined__gte=date_from)
        if date_to:
            queryset = queryset.filter(user__date_joined__lte=date_to)
        
        return queryset

    def list(self, request, *args, **kwargs):
        """List all users with admin permissions."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """Get detailed information about a specific user."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_user_stats(request):
    """
    Get user statistics for admin dashboard.
    """
    try:
        # Basic counts
        total_users = UserProfile.objects.filter(is_deleted=False).count()
        verified_users = UserProfile.objects.filter(
            is_deleted=False, is_verified=True
        ).count()
        
        # Users by role
        role_stats = UserProfile.objects.filter(
            is_deleted=False
        ).values('role').annotate(count=Count('id'))
        
        # New users in last 30 days
        thirty_days_ago = timezone.now() - timedelta(days=30)
        new_users_30d = UserProfile.objects.filter(
            is_deleted=False,
            user__date_joined__gte=thirty_days_ago
        ).count()
        
        # Active users (users who logged in within last 7 days)
        seven_days_ago = timezone.now() - timedelta(days=7)
        active_users = User.objects.filter(
            last_login__gte=seven_days_ago,
            profile__is_deleted=False
        ).count()
        
        # Prepare role statistics
        role_data = {item['role']: item['count'] for item in role_stats}
        
        return Response({
            'total_users': total_users,
            'verified_users': verified_users,
            'verification_rate': (verified_users / total_users * 100) if total_users > 0 else 0,
            'new_users_30d': new_users_30d,
            'active_users_7d': active_users,
            'activity_rate': (active_users / total_users * 100) if total_users > 0 else 0,
            'role_distribution': role_data,
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        return Response(
            {'error': 'Failed to fetch user statistics', 'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_user_detail_by_user_id(request, user_id):
    """
    Get detailed user information by User ID (not UserProfile UUID).
    """
    try:
        user = User.objects.select_related('profile').get(
            id=user_id, profile__is_deleted=False
        )
        
        # Serialize the user data manually for now
        user_data = {
            'id': user.profile.id,  # UUID du profil
            'user_id': user.id,     # ID numérique de l'utilisateur
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': f"{user.first_name} {user.last_name}".strip(),
            'date_joined': user.date_joined,
            'last_login': user.last_login,
            'is_active': user.is_active,
            'role': user.profile.role,
            'is_verified': user.profile.is_verified,
            'is_suspended': user.profile.is_suspended,
            'phone_number': user.profile.phone_number,
            'bio': user.profile.bio,
            'profile_picture': user.profile.profile_picture.url if user.profile.profile_picture else None,
            'created_at': user.profile.created_at,
            'updated_at': user.profile.updated_at,
            'last_active': user.profile.last_active,
        }
        
        return Response(user_data)
        
    except User.DoesNotExist:
        return Response(
            {'error': 'User not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': 'Failed to fetch user details', 'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_user_detail_stats(request, user_id):
    """
    Get detailed statistics for a specific user by User ID.
    """
    try:
        user = User.objects.select_related('profile').get(
            id=user_id, profile__is_deleted=False
        )
        user_profile = user.profile
        
        # Basic user stats (placeholder for now)
        stats = {
            'posts_count': 0,  # TODO: Intégrer avec le système de posts
            'followers_count': 0,  # TODO: Intégrer avec le système de followers
            'following_count': 0,  # TODO: Intégrer avec le système de following
            'engagement_score': user_profile.engagement_score,
            'content_quality_score': user_profile.content_quality_score,
            'interaction_frequency': user_profile.interaction_frequency,
            'account_age_days': (timezone.now() - user.date_joined).days,
            'last_active': user_profile.last_active,
            'is_verified': user_profile.is_verified,
            'is_suspended': user_profile.is_suspended,
            'suspension_reason': user_profile.suspension_reason if user_profile.is_suspended else None,
        }
        
        return Response(stats)
        
    except User.DoesNotExist:
        return Response(
            {'error': 'User not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': 'Failed to fetch user statistics', 'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_user_action(request, user_id):
    """
    Perform admin actions on a user (suspend, verify, etc.) by User ID.
    """
    try:
        user = User.objects.select_related('profile').get(
            id=user_id, profile__is_deleted=False
        )
        user_profile = user.profile
        action = request.data.get('action')
        
        if action == 'verify':
            user_profile.is_verified = True
            user_profile.last_verified_at = timezone.now()
            user_profile.save(update_fields=['is_verified', 'last_verified_at'])
            
            return Response({
                'message': f'User {user.username} has been verified.',
                'user_id': user.id,
                'action': 'verify'
            })
            
        elif action == 'unverify':
            user_profile.is_verified = False
            user_profile.save(update_fields=['is_verified'])
            
            return Response({
                'message': f'User {user.username} verification has been removed.',
                'user_id': user.id,
                'action': 'unverify'
            })
            
        elif action == 'suspend':
            # Récupérer toutes les données de suspension
            suspension_data = {
                'reason': request.data.get('reason', 'Admin action'),
                'details': request.data.get('details', ''),
                'duration': request.data.get('duration', 'indefinite'),
                'notifyUser': request.data.get('notifyUser', True)
            }
            
            # Suspendre l'utilisateur
            user_profile.is_suspended = True
            user_profile.suspended_at = timezone.now()
            user_profile.suspension_reason = suspension_data['reason']
            
            # Ajouter les détails à la raison si fournis
            if suspension_data['details']:
                user_profile.suspension_reason += f"\n\nDétails: {suspension_data['details']}"
            
            user_profile.save(update_fields=[
                'is_suspended', 'suspended_at', 'suspension_reason'
            ])
            
            # Envoyer l'email de notification si demandé
            email_sent = False
            if suspension_data['notifyUser']:
                email_sent = send_suspension_email(user, suspension_data)
            
            response_data = {
                'message': f'User {user.username} has been suspended.',
                'user_id': user.id,
                'action': 'suspend',
                'reason': suspension_data['reason'],
                'duration': suspension_data['duration'],
                'email_sent': email_sent
            }
            
            return Response(response_data)
            
        elif action == 'unsuspend':
            user_profile.is_suspended = False
            user_profile.suspended_at = None
            user_profile.suspension_reason = ''
            user_profile.save(update_fields=['is_suspended', 'suspended_at', 'suspension_reason'])
            
            return Response({
                'message': f'User {user.username} suspension has been lifted.',
                'user_id': user.id,
                'action': 'unsuspend'
            })
            
        else:
            return Response(
                {'error': f'Unknown action: {action}'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except User.DoesNotExist:
        return Response(
            {'error': 'User not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': 'Failed to perform user action', 'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# =============================================================================
# USER CREATION ENDPOINTS (Admin and Moderator)
# =============================================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_create_user(request):
    """
    Create a new admin or moderator user.
    Only accessible by admin users.
    """
    try:
        data = request.data
        
        # Validation des données requises
        required_fields = ['username', 'email', 'password', 'first_name', 'last_name', 'role', 'phone_number', 'date_of_birth']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return Response(
                {'error': 'Missing required fields', 'missing_fields': missing_fields},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validation du rôle
        role = data.get('role')
        if role not in ['admin', 'moderator']:
            return Response(
                {'error': 'Invalid role. Must be "admin" or "moderator"'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validation de l'email
        email = data.get('email')
        try:
            validate_email(email)
        except ValidationError:
            return Response(
                {'error': 'Invalid email address'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Vérifier si l'email ou le nom d'utilisateur existe déjà
        if User.objects.filter(email=email).exists():
            return Response(
                {'error': 'A user with this email already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if User.objects.filter(username=data.get('username')).exists():
            return Response(
                {'error': 'A user with this username already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from django.db import transaction
        
        # Utiliser une transaction atomique pour éviter les conflits
        with transaction.atomic():
            # Créer l'utilisateur Django
            user = User.objects.create_user(
                username=data.get('username'),
                email=email,
                password=data.get('password'),
                first_name=data.get('first_name'),
                last_name=data.get('last_name')
            )
            
            # Récupérer ou créer le profil utilisateur
            user_profile, profile_created = UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'role': role,
                    'phone_number': data.get('phone_number'),
                    'date_of_birth': data.get('date_of_birth'),
                    'is_verified': True,
                    'bio': data.get('bio', ''),
                }
            )
            
            # Si le profil existait déjà, mettre à jour les champs
            if not profile_created:
                user_profile.role = role
                user_profile.phone_number = data.get('phone_number')
                user_profile.date_of_birth = data.get('date_of_birth')
                user_profile.is_verified = True
                user_profile.bio = data.get('bio', '')
                
            if data.get('administrative_division'):
                user_profile.administrative_division_id = data.get('administrative_division')
            user_profile.save()
        
        # Créer le profil spécialisé selon le rôle
        if role == 'admin':
            AdminProfile.objects.create(
                profile=user_profile,
                admin_level=data.get('admin_level', 'system_admin'),
                department=data.get('department', ''),
                employee_id=data.get('employee_id', ''),
                can_manage_users=data.get('can_manage_users', True),
                can_manage_content=data.get('can_manage_content', True),
                can_view_analytics=data.get('can_view_analytics', True),
                access_level=data.get('access_level', 5),
                is_active=True
            )
        elif role == 'moderator':
            from .models import ModeratorProfile
            ModeratorProfile.objects.create(
                profile=user_profile,
                moderator_level=data.get('moderator_level', 'junior'),
                specialization=data.get('specialization', 'general'),
                can_remove_posts=data.get('can_remove_posts', True),
                can_remove_comments=data.get('can_remove_comments', True),
                can_ban_users=data.get('can_ban_users', False),
                can_suspend_users=data.get('can_suspend_users', False),
                can_manage_reports=data.get('can_manage_reports', True),
                is_active=True
            )
        
        # Préparer la réponse avec les données utilisateur
        response_data = {
            'message': f'{role.capitalize()} user created successfully',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': role,
                'is_active': user.is_active,
                'date_joined': user.date_joined.isoformat(),
                'profile': {
                    'id': str(user_profile.id),
                    'phone_number': user_profile.phone_number,
                    'is_verified': user_profile.is_verified,
                    'bio': user_profile.bio
                }
            }
        }
        
        # Envoyer un email de bienvenue (optionnel)
        if data.get('send_welcome_email', True):
            try:
                send_welcome_email(user, role, data.get('temporary_password', False))
                response_data['email_sent'] = True
            except Exception as e:
                response_data['email_sent'] = False
                response_data['email_error'] = str(e)
        
        return Response(response_data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response(
            {'error': 'Failed to create user', 'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def send_welcome_email(user, role, is_temporary_password=False):
    """
    Send welcome email to newly created admin/moderator user.
    """
    try:
        role_display = 'Administrateur' if role == 'admin' else 'Modérateur'
        
        context = {
            'user_name': user.get_full_name() or user.username,
            'username': user.username,
            'role_display': role_display,
            'is_temporary_password': is_temporary_password,
            'login_url': f'{settings.FRONTEND_URL}/login',
            'dashboard_url': f'{settings.FRONTEND_URL}/{role}/dashboard',
            'current_year': timezone.now().year,
        }
        
        subject = f'Bienvenue sur CitInfos - Compte {role_display}'
        
        # Message texte simple
        message = f'''
Bonjour {context['user_name']},

Votre compte {role_display} a été créé avec succès sur CitInfos.

Nom d'utilisateur: {user.username}
Email: {user.email}
Rôle: {role_display}

Vous pouvez vous connecter à l'adresse: {context['login_url']}

Votre tableau de bord: {context['dashboard_url']}

Cordialement,
L'équipe CitInfos
        '''
        
        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@citinfos.com'),
            recipient_list=[user.email],
            fail_silently=False,
        )
        
        return True
        
    except Exception as e:
        print(f"Erreur lors de l'envoi de l'email de bienvenue: {e}")
        return False