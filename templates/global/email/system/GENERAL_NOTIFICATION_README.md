# General Notification Email Template

The `general_notification.html` template provides a flexible, reusable template for all types of system notifications, alerts, and general purpose emails across the platform.

## Template Path
```
templates/global/email/system/general_notification.html
```

## Usage with NotificationService

```python
from notifications.utils import NotificationService

# Basic notification
NotificationService.send_email_notification(
    recipient=user_profile,
    subject="Important Update",
    template='global/email/system/general_notification.html',
    context={
        'notification_title': 'System Update',
        'notification_message': 'Your account settings have been updated successfully.',
    }
)
```

## Context Variables

### Required Variables
- `notification_title` - Main title shown in header and email subject
- `notification_message` - Main message content

### Optional Variables

#### Header & Title
- `notification_icon` - Emoji/icon for the header (default: "📧")
- `notification_heading` - Subtitle under the header (default: "You have a new notification")

#### Alert Box
- `alert_message` - Important message in colored box
- `alert_type` - Alert style: 'warning', 'error', 'success', 'info' (default: 'info')

#### Details Section
- `details` - Dictionary of key-value pairs to display
- `notification_details` - List of objects with 'label' and 'value' properties

#### Action Items
- `action_items` - List of action items/steps for the user
- `action_items_title` - Title for action items section (default: "What you can do")

#### Buttons
- `primary_action_url` - URL for main action button
- `primary_action_text` - Text for main button (default: "Take Action")
- `button_color` - Hex color for primary button (default: "#007bff")
- `secondary_action_url` - URL for secondary button
- `secondary_action_text` - Text for secondary button (default: "Learn More")

#### Footer & Metadata
- `show_timestamp` - Show timestamp and reference ID (boolean)
- `notification_id` - Reference ID for the notification
- `additional_notes` - Additional notes in footer area
- `footer_message` - Custom footer message

## Example Usage Scenarios

### 1. Simple System Notification
```python
context = {
    'notification_title': 'Account Verified',
    'notification_icon': '✅',
    'notification_message': 'Your account has been successfully verified.',
    'show_timestamp': True,
}
```

### 2. Alert with Action Required
```python
context = {
    'notification_title': 'Action Required',
    'notification_icon': '⚠️',
    'notification_message': 'Your password will expire in 3 days.',
    'alert_message': 'Please update your password to maintain account security.',
    'alert_type': 'warning',
    'primary_action_url': 'https://example.com/change-password',
    'primary_action_text': 'Change Password',
    'action_items': [
        'Click the button above to change your password',
        'Choose a strong password with at least 8 characters',
        'Avoid using common words or personal information'
    ]
}
```

### 3. Detailed Information Notification
```python
context = {
    'notification_title': 'Equipment Warranty Update',
    'notification_message': 'Your equipment warranty information has been updated.',
    'details': {
        'Equipment': 'Samsung TV Model XYZ123',
        'Warranty Period': '2 years',
        'Expiry Date': 'December 31, 2025',
        'Coverage': 'Full replacement coverage'
    },
    'primary_action_url': 'https://example.com/warranties',
    'primary_action_text': 'View All Warranties',
    'additional_notes': 'Keep this email for your records.'
}
```

### 4. System Maintenance Notification
```python
context = {
    'notification_title': 'Scheduled Maintenance',
    'notification_icon': '🔧',
    'notification_heading': 'System maintenance scheduled',
    'notification_message': 'We will be performing system maintenance on Saturday, August 28th from 2:00 AM to 4:00 AM EST.',
    'alert_message': 'The platform will be temporarily unavailable during this time.',
    'alert_type': 'info',
    'action_items': [
        'Save any work before the maintenance window',
        'Plan alternative access if needed',
        'Check our status page for real-time updates'
    ],
    'secondary_action_url': 'https://status.example.com',
    'secondary_action_text': 'View Status Page'
}
```

## Integration Examples

### In Task Functions
```python
@shared_task
def send_system_notification(user_ids, title, message, alert_type=None):
    from notifications.utils import NotificationService
    from accounts.models import UserProfile

    users = UserProfile.objects.filter(id__in=user_ids, is_deleted=False)

    for user in users:
        context = {
            'notification_title': title,
            'notification_message': message,
            'show_timestamp': True
        }

        if alert_type:
            context['alert_message'] = message
            context['alert_type'] = alert_type

        NotificationService.send_email_notification(
            recipient=user,
            subject=title,
            template='global/email/system/general_notification.html',
            context=context
        )
```

### In Views
```python
def send_user_notification(request):
    context = {
        'notification_title': 'Profile Updated',
        'notification_message': 'Your profile information has been updated successfully.',
        'details': {
            'Updated': timezone.now().strftime('%B %d, %Y at %I:%M %p'),
            'Changes': 'Email address, phone number'
        }
    }

    NotificationService.send_email_notification(
        recipient=request.user.userprofile,
        subject='Profile Updated Successfully',
        template='global/email/system/general_notification.html',
        context=context
    )
```

## Template Features

- **Responsive Design**: Works on all email clients and mobile devices
- **Consistent Branding**: Uses global base template for consistent styling
- **Flexible Layout**: Supports various content types and structures
- **Accessibility**: Proper color contrast and readable fonts
- **Email Client Compatible**: Uses table-based layout for maximum compatibility

## Best Practices

1. **Keep messages concise**: Email content should be scannable and brief
2. **Use clear action items**: When actions are required, make them specific
3. **Include relevant details**: Provide enough context without overwhelming
4. **Test with different content**: Ensure template works with various content lengths
5. **Use appropriate alert types**: Match alert colors to the message urgency
6. **Include timestamps for important notifications**: Helps with record-keeping

This template centralizes email notification styling and provides a consistent user experience across all platform communications.
