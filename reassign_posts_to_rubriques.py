"""
Reassign existing posts to appropriate rubriques based on their content.

This script analyzes post content and assigns them to the most relevant rubrique.
For now, we'll do manual assignment based on content keywords.
Later, we'll use a recommendation system for the "Accueil" rubrique.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'citinfos_backend.settings')
django.setup()

from content.models import Post
from communities.models import RubriqueTemplate
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Keyword-based rubrique mapping
RUBRIQUE_KEYWORDS = {
    'actualites': ['annonce', 'nouveau', 'important', 'information', 'actualité'],
    'evenements': ['festival', 'événement', 'spectacle', 'concert', 'fête'],
    'commerces': ['restaurant', 'café', 'boutique', 'magasin', 'commerce'],
    'questions': ['pourquoi', 'comment', 'qui', 'quoi', 'où', 'quand', 'sait-il'],
    'photos': ['photo', 'image', 'coucher de soleil', 'magnifique', 'vue'],
}


def get_rubrique_from_content(content):
    """Determine the most appropriate rubrique based on content keywords."""
    content_lower = content.lower()

    # Score each rubrique
    scores = {}
    for rubrique_type, keywords in RUBRIQUE_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in content_lower)
        if score > 0:
            scores[rubrique_type] = score

    # Return the highest scoring rubrique
    if scores:
        return max(scores.items(), key=lambda x: x[1])[0]

    # Default to actualites if no keywords match
    return 'actualites'


def reassign_posts():
    """Reassign all posts without rubriques to appropriate rubriques."""

    print("=" * 80)
    print("REASSIGNING POSTS TO RUBRIQUES")
    print("=" * 80)

    # Get posts without rubriques
    posts_without_rubrique = Post.objects.filter(
        is_deleted=False,
        thread__isnull=True,  # Only standalone posts
        rubrique_template__isnull=True
    ).select_related('community')

    total_posts = posts_without_rubrique.count()
    print(f"\nFound {total_posts} posts without rubriques\n")

    if total_posts == 0:
        print("✅ All posts already have rubriques assigned!")
        return

    reassigned = 0
    errors = 0

    for i, post in enumerate(posts_without_rubrique, 1):
        try:
            # Get content to analyze (use title if it's an article, otherwise content)
            content_to_analyze = post.title if (post.post_type == 'article' and post.title) else post.content

            # Determine rubrique from content
            rubrique_type = get_rubrique_from_content(content_to_analyze)

            # Get the rubrique template
            rubrique = RubriqueTemplate.objects.filter(
                template_type=rubrique_type,
                is_active=True
            ).first()

            if not rubrique:
                print(f"  [{i}/{total_posts}] ⚠️  Rubrique '{rubrique_type}' not found")
                rubrique = RubriqueTemplate.objects.filter(
                    template_type='actualites',
                    is_active=True
                ).first()

            if rubrique:
                # Check if rubrique is enabled for community
                if post.community:
                    enabled = post.community.enabled_rubriques or []
                    if str(rubrique.id) not in enabled:
                        print(f"  [{i}/{total_posts}] ⚠️  Rubrique not enabled, skipping")
                        continue

                # Assign rubrique
                post.rubrique_template = rubrique
                post.save(update_fields=['rubrique_template'])

                # Display preview
                if post.post_type == 'article' and post.title:
                    preview = f"[Article] {post.title[:50]}"
                else:
                    preview = post.content[:50] + "..." if len(post.content) > 50 else post.content

                print(f"  [{i}/{total_posts}] ✅ '{rubrique.default_name}' → {preview}")
                reassigned += 1
            else:
                print(f"  [{i}/{total_posts}] ❌ No rubrique found")
                errors += 1

        except Exception as e:
            print(f"  [{i}/{total_posts}] ❌ Error: {str(e)}")
            logger.error(f"Failed to reassign post {post.id}: {str(e)}", exc_info=True)
            errors += 1

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✅ Successfully reassigned: {reassigned}")
    print(f"❌ Errors: {errors}")
    print(f"📌 Total processed: {total_posts}")
    print("=" * 80)


if __name__ == '__main__':
    reassign_posts()
