# SMS Service Setup and Usage Guide

## Installation

1. Install Twilio:
```bash
pip install twilio
```

2. Add Twilio credentials to your `.env` file:
```
TWILIO_ACCOUNT_SID=your_account_sid_here
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=+1234567890
```

## Usage Examples

### Basic SMS Sending
```python
from accounts.sms_service import send_sms

# Send a single SMS
result = send_sms('+1234567890', 'Hello from Django!')

if result['success']:
    print(f"SMS sent successfully. SID: {result['message_sid']}")
else:
    print(f"Failed to send SMS: {result['error']}")
```

### Bulk SMS Sending
```python
from accounts.sms_service import send_bulk_sms

phone_numbers = ['+1234567890', '+0987654321']
message = 'Hello everyone!'

results = send_bulk_sms(phone_numbers, message)

for phone_number, result in results.items():
    if result['success']:
        print(f"SMS sent to {phone_number}: {result['message_sid']}")
    else:
        print(f"Failed to send SMS to {phone_number}: {result['error']}")
```

### In Django Views
```python
from django.http import JsonResponse
from accounts.sms_service import send_sms

def send_notification_sms(request):
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        message = request.POST.get('message')

        result = send_sms(phone_number, message)

        return JsonResponse(result)
```

### With User Authentication
```python
from django.contrib.auth.decorators import login_required
from accounts.sms_service import send_sms

@login_required
def send_user_sms(request):
    user = request.user
    if hasattr(user, 'phone_number') and user.phone_number:
        result = send_sms(user.phone_number, 'Welcome to our service!')
        return JsonResponse(result)
    return JsonResponse({'success': False, 'error': 'No phone number found'})
```

## Error Handling

The SMS service returns a dictionary with the following structure:

**Success Response:**
```python
{
    'success': True,
    'message_sid': 'SM1234567890abcdef',
    'status': 'queued'  # or 'sending', 'sent', 'delivered', etc.
}
```

**Error Response:**
```python
{
    'success': False,
    'error': 'Error message here'
}
```

## Phone Number Format

Always use E.164 format for phone numbers:
- ✅ Correct: `+1234567890`
- ❌ Wrong: `123-456-7890` or `(123) 456-7890`

## Getting Twilio Credentials

1. Sign up at https://www.twilio.com
2. Go to Console Dashboard
3. Copy your Account SID and Auth Token
4. Get a Twilio phone number from the Console
