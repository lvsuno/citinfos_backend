"""
Models for handling email and phone number changes with verification.
"""

import uuid
import random
import string
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import timedelta
from accounts.models import UserProfile


class ContactChangeRequest(models.Model):
    """Base model for contact information change requests."""

    CHANGE_TYPES = [
        ('email', 'Email Change'),
        ('phone', 'Phone Change'),
    ]

    STATUS_CHOICES = [
        ('pending_current_verification', 'Pending Current Contact Verification'),
        ('current_verified', 'Current Contact Verified'),
        ('pending_new_verification', 'Pending New Contact Verification'),
        ('completed', 'Change Completed'),
        ('expired', 'Request Expired'),
        ('cancelled', 'Request Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_profile = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='contact_change_requests'
    )
    change_type = models.CharField(max_length=10, choices=CHANGE_TYPES)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES,
                            default='pending_current_verification')

    # Current contact info
    current_email = models.EmailField(blank=True, null=True)
    current_phone = models.CharField(max_length=20, blank=True, null=True)

    # New contact info
    new_email = models.EmailField(blank=True, null=True)
    new_phone = models.CharField(max_length=20, blank=True, null=True)

    # Verification codes
    current_verification_code = models.CharField(max_length=8, blank=True)
    new_verification_code = models.CharField(max_length=8, blank=True)

    # Verification status
    current_verified_at = models.DateTimeField(null=True, blank=True)
    new_verified_at = models.DateTimeField(null=True, blank=True)

    # Expiration and completion
    expires_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Attempt tracking
    current_verification_attempts = models.PositiveIntegerField(default=0)
    new_verification_attempts = models.PositiveIntegerField(default=0)
    max_attempts = models.PositiveIntegerField(default=3)

    class Meta:
        verbose_name = "Contact Change Request"
        verbose_name_plural = "Contact Change Requests"
        indexes = [
            models.Index(fields=['user_profile', 'status']),
            models.Index(fields=['change_type', 'status']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f"{self.get_change_type_display()} request for {self.user_profile.user.username}"

    def save(self, *args, **kwargs):
        # Set expiration time (24 hours from now)
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=24)
        super().save(*args, **kwargs)

    def is_expired(self):
        """Check if the request has expired."""
        return timezone.now() > self.expires_at

    def generate_current_verification_code(self):
        """Generate verification code for current contact verification."""
        self.current_verification_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        self.save(update_fields=['current_verification_code'])
        return self.current_verification_code

    def generate_new_verification_code(self):
        """Generate verification code for new contact verification."""
        self.new_verification_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        self.save(update_fields=['new_verification_code'])
        return self.new_verification_code

    def verify_current_contact(self, code):
        """Verify the current contact with the provided code."""
        if self.is_expired():
            self.status = 'expired'
            self.save()
            return False, "Request has expired"

        if self.current_verification_attempts >= self.max_attempts:
            return False, "Maximum verification attempts exceeded"

        self.current_verification_attempts += 1

        if self.current_verification_code == code:
            self.current_verified_at = timezone.now()
            self.status = 'current_verified'
            self.save()
            return True, "Current contact verified successfully"
        else:
            self.save(update_fields=['current_verification_attempts'])
            remaining = self.max_attempts - self.current_verification_attempts
            return False, f"Invalid code. {remaining} attempts remaining."

    def verify_new_contact(self, code):
        """Verify the new contact with the provided code."""
        if self.status != 'pending_new_verification':
            return False, "Not ready for new contact verification"

        if self.is_expired():
            self.status = 'expired'
            self.save()
            return False, "Request has expired"

        if self.new_verification_attempts >= self.max_attempts:
            return False, "Maximum verification attempts exceeded"

        self.new_verification_attempts += 1

        if self.new_verification_code == code:
            self.new_verified_at = timezone.now()
            self.status = 'completed'
            self.completed_at = timezone.now()

            # Apply the change to the user profile
            if self.change_type == 'email':
                self.user_profile.user.email = self.new_email
                self.user_profile.user.save()
            elif self.change_type == 'phone':
                self.user_profile.phone = self.new_phone
                self.user_profile.save()

            self.save()
            return True, "Contact information changed successfully"
        else:
            self.save(update_fields=['new_verification_attempts'])
            remaining = self.max_attempts - self.new_verification_attempts
            return False, f"Invalid code. {remaining} attempts remaining."

    def start_new_verification(self):
        """Start the new contact verification process."""
        if self.status != 'current_verified':
            return False, "Current contact must be verified first"

        self.status = 'pending_new_verification'
        self.save()
        return True, "Ready for new contact verification"

    def cancel_request(self):
        """Cancel the change request."""
        self.status = 'cancelled'
        self.save()


class ContactChangeLog(models.Model):
    """Log of all contact change attempts for audit purposes."""

    ACTION_TYPES = [
        ('request_created', 'Change Request Created'),
        ('current_code_sent', 'Current Verification Code Sent'),
        ('current_verified', 'Current Contact Verified'),
        ('new_code_sent', 'New Verification Code Sent'),
        ('new_verified', 'New Contact Verified'),
        ('change_completed', 'Contact Change Completed'),
        ('request_expired', 'Request Expired'),
        ('request_cancelled', 'Request Cancelled'),
        ('verification_failed', 'Verification Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    change_request = models.ForeignKey(
        ContactChangeRequest,
        on_delete=models.CASCADE,
        related_name='logs'
    )
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Contact Change Log"
        verbose_name_plural = "Contact Change Logs"
        indexes = [
            models.Index(fields=['change_request', 'created_at']),
            models.Index(fields=['action_type', 'created_at']),
        ]

    def __str__(self):
        return f"{self.get_action_type_display()} - {self.change_request}"
