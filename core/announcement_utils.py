"""Utility functions for managing system announcements."""

from django.conf import settings
from .models import Announcement


class SystemAnnouncementManager:
    """Manager for creating and managing system-generated announcements."""

    @staticmethod
    def create_welcome_announcement(user_profile, custom_message=None):
        """Create a welcome announcement for a new user."""
        if custom_message:
            body_html = custom_message
        else:
            body_html = f"""
            <div class="welcome-message">
                <h3>Welcome to the Equipment Database, {user_profile.display_name}!</h3>
                <p>We're excited to have you join our community. Here are some things you can do:</p>
                <ul>
                    <li>Explore equipment listings and reviews</li>
                    <li>Join communities that match your interests</li>
                    <li>Connect with other equipment enthusiasts</li>
                    <li>Share your own equipment experiences</li>
                </ul>
                <p>If you have any questions, don't hesitate to reach out to our support team.</p>
            </div>
            """

        return Announcement.create_welcome_message(
            title=f"Welcome, {user_profile.display_name}!",
            body_html=body_html,
            target_user=user_profile
        )

    @staticmethod
    def create_role_announcement(title, message, target_roles, **kwargs):
        """Create an announcement targeted to specific user roles."""
        return Announcement.create_system_announcement(
            title=title,
            body_html=message,
            target_user_roles=target_roles if isinstance(target_roles, list) else [target_roles],
            **kwargs
        )

    @staticmethod
    def create_geographic_announcement(title, message, countries=None, timezones=None,
                                     cities=None, regions=None, **kwargs):
        """Create an announcement targeted to specific geographic areas."""
        targeting = {}
        if countries:
            targeting['target_countries'] = countries if isinstance(countries, list) else [countries]
        if timezones:
            targeting['target_timezones'] = timezones if isinstance(timezones, list) else [timezones]
        if cities:
            targeting['target_cities'] = cities if isinstance(cities, list) else [cities]
        if regions:
            targeting['target_regions'] = regions if isinstance(regions, list) else [regions]

        return Announcement.create_system_announcement(
            title=title,
            body_html=message,
            **targeting,
            **kwargs
        )

    @staticmethod
    def create_community_announcement(title, message, community, **kwargs):
        """Create a global announcement targeted to a specific community."""
        return Announcement.create_system_announcement(
            title=title,
            body_html=message,
            target_community=community,
            **kwargs
        )

    @staticmethod
    def create_maintenance_announcement(title, message, scheduled_time=None, **kwargs):
        """Create a maintenance announcement for all users."""
        if scheduled_time:
            message += f"<p><strong>Scheduled Time:</strong> {scheduled_time}</p>"

        return Announcement.create_system_announcement(
            title=title,
            body_html=message,
            is_important=True,
            banner_style='static',  # Maintenance announcements should be visible
            **kwargs
        )

    @staticmethod
    def create_feature_announcement(title, message, target_roles=None, **kwargs):
        """Create an announcement about new features."""
        targeting = {}
        if target_roles:
            targeting['target_user_roles'] = target_roles if isinstance(target_roles, list) else [target_roles]

        return Announcement.create_system_announcement(
            title=title,
            body_html=message,
            banner_style='fade',  # Feature announcements can use animation
            **targeting,
            **kwargs
        )


def send_welcome_announcement(user_profile):
    """Send a welcome announcement to a new user."""
    return SystemAnnouncementManager.create_welcome_announcement(user_profile)


def send_maintenance_notification(title, message, scheduled_time=None):
    """Send a maintenance notification to all users."""
    return SystemAnnouncementManager.create_maintenance_announcement(
        title, message, scheduled_time
    )


def send_role_based_notification(title, message, roles):
    """Send a notification to users with specific roles."""
    return SystemAnnouncementManager.create_role_announcement(title, message, roles)


def send_geographic_notification(title, message, **geographic_filters):
    """Send a notification to users in specific geographic areas."""
    return SystemAnnouncementManager.create_geographic_announcement(
        title, message, **geographic_filters
    )
