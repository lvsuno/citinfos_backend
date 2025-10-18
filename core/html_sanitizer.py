"""HTML sanitization utilities for user-generated content."""

import bleach
from bleach.css_sanitizer import CSSSanitizer


# Define allowed HTML tags for announcements
ANNOUNCEMENT_ALLOWED_TAGS = [
    # Text formatting
    'p', 'br', 'strong', 'b', 'em', 'i', 'u', 'span', 'div',

    # Headers
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',

    # Lists
    'ul', 'ol', 'li',

    # Links
    'a',

    # Media (for announcements with images/videos)
    'img',

    # Tables (for structured announcement content)
    'table', 'thead', 'tbody', 'tr', 'th', 'td',

    # Quotes and code
    'blockquote', 'code', 'pre',

    # Line breaks and separators
    'hr',
]

# Define allowed HTML attributes
ANNOUNCEMENT_ALLOWED_ATTRIBUTES = {
    '*': ['class', 'id', 'style'],
    'a': ['href', 'title', 'target', 'rel'],
    'img': ['src', 'alt', 'title', 'width', 'height', 'class'],
    'table': ['class', 'border', 'cellpadding', 'cellspacing'],
    'th': ['colspan', 'rowspan', 'scope'],
    'td': ['colspan', 'rowspan'],
    'blockquote': ['cite'],
}

# Define allowed CSS properties for style attributes
ANNOUNCEMENT_ALLOWED_STYLES = [
    'color', 'background-color', 'font-weight', 'font-style', 'text-decoration',
    'text-align', 'margin', 'padding', 'border', 'border-radius',
    'font-size', 'line-height', 'max-width', 'width', 'height',
]

# CSS sanitizer for style attributes
css_sanitizer = CSSSanitizer(allowed_css_properties=ANNOUNCEMENT_ALLOWED_STYLES)


def sanitize_announcement_html(html_content):
    """
    Sanitize HTML content for announcements.

    This function removes potentially dangerous HTML/CSS while preserving
    formatting that's useful for announcements.

    Args:
        html_content (str): Raw HTML content from user input

    Returns:
        str: Sanitized HTML content safe for display
    """
    if not html_content:
        return ""

    # Use bleach to sanitize the HTML
    sanitized = bleach.clean(
        html_content,
        tags=ANNOUNCEMENT_ALLOWED_TAGS,
        attributes=ANNOUNCEMENT_ALLOWED_ATTRIBUTES,
        css_sanitizer=css_sanitizer,
        strip=True,  # Strip disallowed tags instead of escaping
        strip_comments=True,  # Remove HTML comments
    )

    # Additional security: ensure all links open in new window and are nofollow
    sanitized = bleach.linkify(
        sanitized,
        callbacks=[
            lambda attrs, new=False: attrs.update({'target': '_blank', 'rel': 'nofollow noopener'}) or attrs
        ]
    )

    return sanitized


def sanitize_basic_html(html_content):
    """
    Sanitize HTML content with basic formatting only.

    This is a more restrictive version for sensitive content.

    Args:
        html_content (str): Raw HTML content from user input

    Returns:
        str: Sanitized HTML content with basic formatting only
    """
    if not html_content:
        return ""

    # More restrictive tag set
    basic_tags = ['p', 'br', 'strong', 'b', 'em', 'i', 'ul', 'ol', 'li']
    basic_attributes = {
        '*': ['class'],
    }

    sanitized = bleach.clean(
        html_content,
        tags=basic_tags,
        attributes=basic_attributes,
        strip=True,
        strip_comments=True,
    )

    return sanitized


# Define allowed HTML tags for rich article content (TipTap editor)
ARTICLE_ALLOWED_TAGS = [
    # Text formatting
    'p', 'br', 'strong', 'b', 'em', 'i', 'u', 'span', 'div',

    # Headers
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',

    # Lists
    'ul', 'ol', 'li',

    # Links
    'a',

    # Media (embedded content from TipTap editor)
    'img', 'video', 'audio', 'source',

    # Tables
    'table', 'thead', 'tbody', 'tr', 'th', 'td',

    # Quotes and code
    'blockquote', 'code', 'pre',

    # Figures and captions
    'figure', 'figcaption',

    # Line breaks and separators
    'hr',
]

# Define allowed HTML attributes for article content
ARTICLE_ALLOWED_ATTRIBUTES = {
    '*': ['class', 'id', 'style'],
    'a': ['href', 'title', 'target', 'rel'],
    'img': ['src', 'alt', 'title', 'width', 'height', 'class'],
    'video': ['src', 'controls', 'width', 'height', 'poster', 'preload', 'class'],
    'audio': ['src', 'controls', 'preload', 'class'],
    'source': ['src', 'type'],
    'table': ['class', 'border', 'cellpadding', 'cellspacing'],
    'th': ['colspan', 'rowspan', 'scope'],
    'td': ['colspan', 'rowspan'],
    'blockquote': ['cite'],
}


def sanitize_article_content(html_content):
    """
    Sanitize rich HTML content for article posts.

    This function allows TipTap editor output including embedded media
    (images, videos, audio) while removing dangerous HTML/JavaScript.

    Args:
        html_content (str): Raw HTML content from TipTap editor

    Returns:
        str: Sanitized HTML content safe for display
    """
    if not html_content:
        return ""

    # Use bleach to sanitize the HTML
    sanitized = bleach.clean(
        html_content,
        tags=ARTICLE_ALLOWED_TAGS,
        attributes=ARTICLE_ALLOWED_ATTRIBUTES,
        css_sanitizer=css_sanitizer,
        strip=True,  # Strip disallowed tags instead of escaping
        strip_comments=True,  # Remove HTML comments
    )

    # Additional security: ensure all links open in new window and are nofollow
    sanitized = bleach.linkify(
        sanitized,
        callbacks=[
            lambda attrs, new=False: attrs.update({'target': '_blank', 'rel': 'nofollow noopener'}) or attrs
        ]
    )

    return sanitized


def strip_all_html(html_content):
    """
    Strip all HTML tags and return plain text.

    This is useful for length validation and plain text previews.

    Args:
        html_content (str): HTML content

    Returns:
        str: Plain text with HTML tags removed
    """
    if not html_content:
        return ""

    # Use bleach to strip all HTML
    plain_text = bleach.clean(html_content, tags=[], strip=True)

    # Clean up whitespace
    import re
    plain_text = re.sub(r'\s+', ' ', plain_text).strip()

    return plain_text


def validate_html_length(html_content, max_length, field_name="content"):
    """
    Validate that the plain text version of HTML content doesn't exceed max length.

    Args:
        html_content (str): HTML content to validate
        max_length (int): Maximum allowed length for plain text
        field_name (str): Name of the field for error messages

    Returns:
        tuple: (is_valid, error_message)
    """
    if not html_content:
        return True, None

    plain_text = strip_all_html(html_content)

    if len(plain_text) > max_length:
        return False, (
            f"{field_name} is too long. Plain text length is {len(plain_text)} "
            f"characters, but maximum allowed is {max_length} characters."
        )

    return True, None
