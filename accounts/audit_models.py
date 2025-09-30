"""
Optional audit trail model for verification code deletions.
Use this only if you need compliance/audit trails for deleted codes.
"""

from django.db import models
from django.utils import timezone
import uuid


class VerificationCodeDeletionLog(models.Model):
    """Audit trail for deleted verification codes (optional)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Original code information
    original_code_id = models.UUIDField()
    user_id = models.UUIDField()
    username = models.CharField(max_length=150)
    code_hash = models.CharField(max_length=64)  # Hashed, not plaintext

    # Code lifecycle info
    code_created_at = models.DateTimeField()
    code_expires_at = models.DateTimeField()
    was_used = models.BooleanField()
    used_at = models.DateTimeField(null=True, blank=True)

    # Deletion info
    deleted_at = models.DateTimeField(default=timezone.now)
    deletion_reason = models.CharField(
        max_length=100,
        default='expired_cleanup'
    )
    deleted_by_command = models.CharField(max_length=100, default='cleanup')

    # Soft delete for audit logs (never hard delete audit trails)
    is_deleted = models.BooleanField(default=False)
    deleted_at_audit = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'verification_code_deletion_log'
        indexes = [
            models.Index(fields=['deleted_at']),
            models.Index(fields=['user_id']),
            models.Index(fields=['username']),
        ]

    def __str__(self):
        return f"Deleted code for {self.username} at {self.deleted_at}"


def log_code_deletion(verification_code, reason="expired_cleanup"):
    """Helper function to log verification code deletion."""
    import hashlib

    # Hash the code for audit (never store plaintext in logs)
    code_hash = hashlib.sha256(verification_code.code.encode()).hexdigest()

    VerificationCodeDeletionLog.objects.create(
        original_code_id=verification_code.id,
        user_id=verification_code.user.id,
        username=verification_code.user.user.username,
        code_hash=code_hash,
        code_created_at=verification_code.created_at,
        code_expires_at=verification_code.expires_at,
        was_used=verification_code.is_used,
        used_at=getattr(verification_code, 'used_at', None),
        deletion_reason=reason
    )
