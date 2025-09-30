"""
SMS Service using Twilio
"""
from django.conf import settings
import logging

try:
    from twilio.rest import Client
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    Client = None

logger = logging.getLogger(__name__)


def send_sms(phone_number, message):
    """
    Send SMS using Twilio

    Args:
        phone_number (str): Phone number in E.164 format (e.g., +1234567890)
        message (str): Message to send

    Returns:
        dict: Result with success status and message
    """
    if not TWILIO_AVAILABLE:
        logger.error("Twilio package is not installed")
        return {
            'success': False,
            'error': 'Twilio package is not installed'
        }

    try:
        # Initialize Twilio client
        client = Client(
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN
        )

        # Send SMS
        message_instance = client.messages.create(
            body=message,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=phone_number
        )

        logger.info(
            "SMS sent successfully to %s. SID: %s",
            phone_number,
            message_instance.sid
        )

        return {
            'success': True,
            'message_sid': message_instance.sid,
            'status': message_instance.status
        }

    except ImportError as e:
        logger.error("Twilio import error: %s", str(e))
        return {
            'success': False,
            'error': f'Twilio import error: {str(e)}'
        }
    except Exception as e:
        logger.error("Failed to send SMS to %s: %s", phone_number, str(e))
        return {
            'success': False,
            'error': str(e)
        }


def send_bulk_sms(phone_numbers, message):
    """
    Send SMS to multiple numbers

    Args:
        phone_numbers (list): List of phone numbers
        message (str): Message to send

    Returns:
        dict: Results for each number
    """
    results = {}

    for phone_number in phone_numbers:
        results[phone_number] = send_sms(phone_number, message)

    return results
