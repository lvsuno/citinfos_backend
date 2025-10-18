#!/usr/bin/env python
"""
Reclassify existing 'article' posts to proper post types.

This script converts 'article' posts that don't have article_content
(i.e., they were created before the article_content field existed)
to the appropriate post type based on their attachments:

- Posts with only image attachments → 'image'
- Posts with only video attachments → 'video'
- Posts with only audio attachments → 'audio'
- Posts with mixed media attachments → 'mixed'
- Posts with no attachments → 'text'
- Posts with article_content stay as 'article'

Usage:
    python scripts/reclassify_article_posts.py [--dry-run] [--verbose]

Options:
    --dry-run: Show what would be changed without making changes
    --verbose: Show detailed output for each post
"""

import os
import sys
import django
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'citinfos_backend.settings')
django.setup()

from content.models import Post  # noqa: E402
from django.db.models import Count, Q  # noqa: E402


def determine_post_type(post):
    """
    Determine the appropriate post type based on attachments.

    Returns:
        str: The appropriate post_type value
    """
    # If post has article_content, keep it as article
    if post.article_content and post.article_content.strip():
        return 'article'

    # Get attachment counts by type
    attachments_by_type = post.media.values('media_type').annotate(
        count=Count('id')
    )

    # Convert to dict for easier lookup
    attachment_counts = {
        item['media_type']: item['count']
        for item in attachments_by_type
    }

    total_attachments = sum(attachment_counts.values())

    # No attachments
    if total_attachments == 0:
        return 'text'

    # Single media type
    if len(attachment_counts) == 1:
        media_type = list(attachment_counts.keys())[0]
        return media_type  # 'image', 'video', 'audio', or 'file'

    # Multiple media types
    return 'mixed'


def reclassify_article_posts(dry_run=False, verbose=False):
    """
    Reclassify article posts to appropriate types.

    Args:
        dry_run (bool): If True, don't make changes,
                        just show what would happen
        verbose (bool): If True, show detailed output for each post

    Returns:
        dict: Summary of changes
    """
    # Find all article posts without article_content
    article_posts = Post.objects.filter(
        post_type='article',
        is_deleted=False
    ).filter(
        Q(article_content__isnull=True) | Q(article_content='')
    )

    total_posts = article_posts.count()

    if total_posts == 0:
        print("✓ No article posts need reclassification.")
        return {
            'total': 0,
            'reclassified': 0,
            'by_type': {}
        }

    print(f"Found {total_posts} article post(s) to reclassify...")
    print()

    changes_by_type = {}
    reclassified_count = 0

    for post in article_posts:
        old_type = post.post_type
        new_type = determine_post_type(post)

        # Track changes
        if new_type != old_type:
            changes_by_type[new_type] = changes_by_type.get(new_type, 0) + 1
            reclassified_count += 1

            if verbose:
                print(f"Post {str(post.id)[:8]}...")
                print(f"  Author: {post.author.user.username}")
                content_preview = (
                    f"{post.content[:50]}..." if post.content
                    else "(empty)"
                )
                print(f"  Content: {content_preview}")
                print(f"  Attachments: {post.attachment_count}")
                if post.attachment_count > 0:
                    for media_type, count in post.attachments_by_type.items():
                        print(f"    - {media_type}: {count}")
                print(f"  Change: {old_type} → {new_type}")
                print()

            # Apply change if not dry run
            if not dry_run:
                post.post_type = new_type
                post.save(update_fields=['post_type'])

    # Print summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total article posts found: {total_posts}")
    print(f"Posts reclassified: {reclassified_count}")
    print()

    if changes_by_type:
        print("Reclassification breakdown:")
        for post_type, count in sorted(changes_by_type.items()):
            print(f"  {post_type}: {count}")

    if dry_run:
        print()
        print("ℹ️  DRY RUN: No changes were made.")
        print("   Run without --dry-run to apply changes.")
    else:
        print()
        print("✓ Reclassification complete!")

    return {
        'total': total_posts,
        'reclassified': reclassified_count,
        'by_type': changes_by_type
    }


def main():
    """Main entry point for the script."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Reclassify article posts to appropriate types'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be changed without making changes'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed output for each post'
    )

    args = parser.parse_args()

    print("=" * 60)
    print("ARTICLE POST RECLASSIFICATION SCRIPT")
    print("=" * 60)
    print()

    if args.dry_run:
        print("🔍 Running in DRY RUN mode")
        print()

    try:
        reclassify_article_posts(
            dry_run=args.dry_run,
            verbose=args.verbose
        )
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
