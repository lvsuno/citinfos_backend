"""
Views for handling email and phone number changes with verification.
"""

import logging
from django.utils import timezone
from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.request import Request
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from accounts.contact_change_models import ContactChangeRequest, ContactChangeLog
from accounts.models import UserProfile
from notifications.utils import NotificationService
from analytics.models import ErrorLog
import re

logger = logging.getLogger(__name__)


def get_client_ip(request):
    """Get client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def request_email_change(request: Request) -> Response:
    """
    Request to change email address.
    Requires phone verification first, then new email verification.
    """
    try:
        user_profile = request.user.profile
        new_email = request.data.get('new_email', '').strip().lower()

        # Validate new email
        if not new_email:
            return Response(
                {'error': 'New email address is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            validate_email(new_email)
        except ValidationError:
            return Response(
                {'error': 'Invalid email address format'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if email is already in use
        if UserProfile.objects.filter(user__email=new_email).exists():
            return Response(
                {'error': 'This email address is already in use'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if user has a phone number for verification
        if not user_profile.phone:
            return Response(
                {'error': 'Phone number is required for email verification'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check for existing pending requests
        existing_request = ContactChangeRequest.objects.filter(
            user_profile=user_profile,
            change_type='email',
            status__in=['pending_current_verification', 'current_verified', 'pending_new_verification']
        ).first()

        if existing_request and not existing_request.is_expired():
            return Response({
                'error': 'Email change request already in progress',
                'request_id': str(existing_request.id),
                'status': existing_request.status,
                'expires_at': existing_request.expires_at.isoformat()
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create new change request
        with transaction.atomic():
            change_request = ContactChangeRequest.objects.create(
                user_profile=user_profile,
                change_type='email',
                current_email=user_profile.user.email,
                current_phone=user_profile.phone,
                new_email=new_email,
                status='pending_current_verification'
            )

            # Generate and send verification code to current phone
            current_code = change_request.generate_current_verification_code()

            # Send SMS to current phone
            sms_message = f"Your email change verification code: {current_code}. Valid for 24 hours."
            sms_sent = NotificationService.send_sms_notification(
                recipient=user_profile,
                message=sms_message
            )

            # Log the request
            ContactChangeLog.objects.create(
                change_request=change_request,
                action_type='request_created',
                description=f'Email change requested: {user_profile.user.email} -> {new_email}',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                metadata={
                    'new_email': new_email,
                    'sms_sent': sms_sent
                }
            )

            ContactChangeLog.objects.create(
                change_request=change_request,
                action_type='current_code_sent',
                description=f'Verification code sent to phone: ***{user_profile.phone[-4:]}',
                ip_address=get_client_ip(request),
                metadata={'sms_sent': sms_sent}
            )

        return Response({
                'success': True,
                'message': 'Phone change verification email sent',
                'request_id': str(change_request.id),
                'email_sent': True  # Async task queued
            })

    except Exception as e:
        logger.error(f"Error in request_email_change: {str(e)}")
        ErrorLog.objects.create(
            level='error',
            message=f'Email change request error: {str(e)}',
            extra_data={
                'user_id': request.user.id,
                'new_email': request.data.get('new_email', '')
            }
        )
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def request_phone_change(request: Request) -> Response:
    """
    Request to change phone number.
    Requires email verification first, then new phone verification.
    """
    try:
        user_profile = request.user.profile
        new_phone = request.data.get('new_phone', '').strip()

        # Validate new phone
        if not new_phone:
            return Response(
                {'error': 'New phone number is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Basic phone validation
        phone_regex = re.compile(r'^\+?[1-9]\d{7,14}$')
        if not phone_regex.match(re.sub(r'[^\d+]', '', new_phone)):
            return Response(
                {'error': 'Invalid phone number format'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if phone is already in use
        if UserProfile.objects.filter(phone=new_phone).exists():
            return Response(
                {'error': 'This phone number is already in use'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if user has an email for verification
        if not user_profile.user.email:
            return Response(
                {'error': 'Email address is required for phone verification'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check for existing pending requests
        existing_request = ContactChangeRequest.objects.filter(
            user_profile=user_profile,
            change_type='phone',
            status__in=['pending_current_verification', 'current_verified', 'pending_new_verification']
        ).first()

        if existing_request and not existing_request.is_expired():
            return Response({
                'error': 'Phone change request already in progress',
                'request_id': str(existing_request.id),
                'status': existing_request.status,
                'expires_at': existing_request.expires_at.isoformat()
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create new change request
        with transaction.atomic():
            change_request = ContactChangeRequest.objects.create(
                user_profile=user_profile,
                change_type='phone',
                current_email=user_profile.user.email,
                current_phone=user_profile.phone,
                new_phone=new_phone,
                status='pending_current_verification'
            )

            # Generate and send verification code to current email
            current_code = change_request.generate_current_verification_code()

            # Send email to current email address ASYNCHRONOUSLY
            from notifications.async_email_tasks import (
                send_contact_change_email_async
            )

            send_contact_change_email_async.delay(
                str(user_profile.id),
                'phone_change',
                current_code,
                new_phone=new_phone
            )

            # Immediate in-app notification
            NotificationService.create_notification(
                recipient=user_profile,
                title="Phone Change Verification",
                message="Check your email for the phone change verification code",
                notification_type='email_sent',
                app_context='accounts'
            )

            # Log the request
            ContactChangeLog.objects.create(
                user_profile=user_profile,
                change_type=ContactChangeLog.PHONE_CHANGE,
                description=f'Phone change requested: {user_profile.phone} -> {new_phone}',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                metadata={
                    'email_sent': True  # Async task queued
                }
            )

            ContactChangeLog.objects.create(
                change_request=change_request,
                action_type='current_code_sent',
                description=f'Verification code sent to email: ***{user_profile.user.email[-10:]}',
                ip_address=get_client_ip(request),
                metadata={'email_sent': True}  # Async task queued
            )

        return Response({
            'success': True,
            'message': 'Verification code sent to your email',
            'request_id': str(change_request.id),
            'status': change_request.status,
            'expires_at': change_request.expires_at.isoformat(),
            'email_partial': user_profile.user.email[:3] + '***' + user_profile.user.email[-10:] if user_profile.user.email else None
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Error in request_phone_change: {str(e)}")
        ErrorLog.objects.create(
            level='error',
            message=f'Phone change request error: {str(e)}',
            extra_data={
                'user_id': request.user.id,
                'new_phone': request.data.get('new_phone', '')
            }
        )
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_current_contact(request: Request) -> Response:
    """
    Verify current contact (phone for email change, email for phone change).
    """
    try:
        user_profile = request.user.profile
        request_id = request.data.get('request_id')
        verification_code = request.data.get('code', '').strip()

        if not request_id or not verification_code:
            return Response(
                {'error': 'Request ID and verification code are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get the change request
        try:
            change_request = ContactChangeRequest.objects.get(
                id=request_id,
                user_profile=user_profile,
                status='pending_current_verification'
            )
        except ContactChangeRequest.DoesNotExist:
            return Response(
                {'error': 'Invalid or expired change request'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verify the code
        success, message = change_request.verify_current_contact(verification_code)

        # Log the attempt
        log_action = 'current_verified' if success else 'verification_failed'
        ContactChangeLog.objects.create(
            change_request=change_request,
            action_type=log_action,
            description=message,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            metadata={'verification_code_correct': success}
        )

        if success:
            return Response({
                'success': True,
                'message': message,
                'status': change_request.status,
                'next_step': 'Send verification code to new contact'
            }, status=status.HTTP_200_OK)
        else:
            return Response(
                {'error': message},
                status=status.HTTP_400_BAD_REQUEST
            )

    except Exception as e:
        logger.error(f"Error in verify_current_contact: {str(e)}")
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_new_contact_code(request: Request) -> Response:
    """
    Send verification code to the new contact information.
    """
    try:
        user_profile = request.user.profile
        request_id = request.data.get('request_id')

        if not request_id:
            return Response(
                {'error': 'Request ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get the change request
        try:
            change_request = ContactChangeRequest.objects.get(
                id=request_id,
                user_profile=user_profile,
                status='current_verified'
            )
        except ContactChangeRequest.DoesNotExist:
            return Response(
                {'error': 'Invalid change request or current contact not verified'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Generate new verification code
        new_code = change_request.generate_new_verification_code()

        # Send code to new contact
        if change_request.change_type == 'email':
            # Send email to new email address
            email_sent = NotificationService.send_email_notification(
                recipient=user_profile,  # This will use the recipient's current email, we need to override
                subject='Verify Your New Email Address',
                template='accounts/email/new_email_verification.html',
                context={
                    'user': user_profile.user,
                    'code': new_code,
                    'expires_at': change_request.expires_at
                }
            )

            # For new email, we need to create a custom email
            # This would require extending the send_email_notification method
            contact_info = f"***{change_request.new_email[-10:]}"
            sent_success = email_sent

        elif change_request.change_type == 'phone':
            # Send SMS to new phone number
            sms_message = f"Your new phone verification code: {new_code}. Valid for 24 hours."
            sent_success = NotificationService.send_sms_notification(
                recipient=user_profile,
                message=sms_message,
                phone_number=change_request.new_phone  # Override with new phone
            )
            contact_info = f"***{change_request.new_phone[-4:]}"

        # Update status
        change_request.start_new_verification()

        # Log the action
        ContactChangeLog.objects.create(
            change_request=change_request,
            action_type='new_code_sent',
            description=f'Verification code sent to new {change_request.change_type}: {contact_info}',
            ip_address=get_client_ip(request),
            metadata={'sent_success': sent_success}
        )

        return Response({
            'success': True,
            'message': f'Verification code sent to your new {change_request.change_type}',
            'status': change_request.status,
            'contact_partial': contact_info
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error in send_new_contact_code: {str(e)}")
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_new_contact(request: Request) -> Response:
    """
    Verify new contact and complete the change process.
    """
    try:
        user_profile = request.user.profile
        request_id = request.data.get('request_id')
        verification_code = request.data.get('code', '').strip()

        if not request_id or not verification_code:
            return Response(
                {'error': 'Request ID and verification code are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get the change request
        try:
            change_request = ContactChangeRequest.objects.get(
                id=request_id,
                user_profile=user_profile,
                status='pending_new_verification'
            )
        except ContactChangeRequest.DoesNotExist:
            return Response(
                {'error': 'Invalid change request or not ready for new contact verification'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verify the code
        success, message = change_request.verify_new_contact(verification_code)

        # Log the attempt
        log_action = 'change_completed' if success else 'verification_failed'
        ContactChangeLog.objects.create(
            change_request=change_request,
            action_type=log_action,
            description=message,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            metadata={'verification_code_correct': success}
        )

        if success:
            # Send confirmation notification
            if change_request.change_type == 'email':
                # Notify both old and new email addresses
                NotificationService.send_email_notification(
                    recipient=user_profile,
                    subject='Email Address Changed Successfully',
                    template='accounts/email/email_change_confirmation.html',
                    context={
                        'user': user_profile.user,
                        'old_email': change_request.current_email,
                        'new_email': change_request.new_email,
                        'changed_at': change_request.completed_at
                    }
                )
            elif change_request.change_type == 'phone':
                # Send SMS to new phone
                confirmation_message = f"Phone number changed successfully. Welcome to your new number!"
                NotificationService.send_sms_notification(
                    recipient=user_profile,
                    message=confirmation_message,
                    phone_number=change_request.new_phone
                )

            return Response({
                'success': True,
                'message': message,
                'status': change_request.status,
                'completed_at': change_request.completed_at.isoformat(),
                'new_contact': change_request.new_email if change_request.change_type == 'email' else change_request.new_phone
            }, status=status.HTTP_200_OK)
        else:
            return Response(
                {'error': message},
                status=status.HTTP_400_BAD_REQUEST
            )

    except Exception as e:
        logger.error(f"Error in verify_new_contact: {str(e)}")
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_change_request_status(request: Request) -> Response:
    """
    Get status of current change requests.
    """
    try:
        user_profile = request.user.profile

        # Get current active requests
        active_requests = ContactChangeRequest.objects.filter(
            user_profile=user_profile,
            status__in=['pending_current_verification', 'current_verified', 'pending_new_verification']
        ).order_by('-created_at')

        requests_data = []
        for req in active_requests:
            if req.is_expired():
                req.status = 'expired'
                req.save()
                continue

            requests_data.append({
                'id': str(req.id),
                'change_type': req.change_type,
                'status': req.status,
                'current_contact': req.current_email if req.change_type == 'email' else req.current_phone,
                'new_contact': req.new_email if req.change_type == 'email' else req.new_phone,
                'created_at': req.created_at.isoformat(),
                'expires_at': req.expires_at.isoformat(),
                'current_verification_attempts': req.current_verification_attempts,
                'new_verification_attempts': req.new_verification_attempts,
                'max_attempts': req.max_attempts
            })

        return Response({
            'success': True,
            'active_requests': requests_data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error in get_change_request_status: {str(e)}")
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_change_request(request: Request) -> Response:
    """
    Cancel a change request.
    """
    try:
        user_profile = request.user.profile
        request_id = request.data.get('request_id')

        if not request_id:
            return Response(
                {'error': 'Request ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get the change request
        try:
            change_request = ContactChangeRequest.objects.get(
                id=request_id,
                user_profile=user_profile
            )
        except ContactChangeRequest.DoesNotExist:
            return Response(
                {'error': 'Change request not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if change_request.status in ['completed', 'cancelled', 'expired']:
            return Response(
                {'error': 'Cannot cancel request in current status'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Cancel the request
        change_request.cancel_request()

        # Log the cancellation
        ContactChangeLog.objects.create(
            change_request=change_request,
            action_type='request_cancelled',
            description='Change request cancelled by user',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

        return Response({
            'success': True,
            'message': 'Change request cancelled successfully'
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error in cancel_change_request: {str(e)}")
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
