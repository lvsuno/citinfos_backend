"""
Script to randomly redistribute existing posts across different rubriques.
This is useful for testing and ensuring posts aren't all in "Actualités".
"""

import random
from content.models import Post
from communities.models import RubriqueTemplate

def redistribute_posts():
    """Randomly assign posts to different rubriques."""

    # Get all posts
    posts = Post.objects.all()
    print(f"Found {posts.count()} posts to redistribute")

    # Get all available rubrique templates (excluding sub-sections for simplicity)
    # We'll use top-level rubriques only (parent=None)
    rubriques = list(RubriqueTemplate.objects.filter(parent=None))
    print(f"Found {len(rubriques)} top-level rubriques:")
    for rubrique in rubriques:
        print(f"  - {rubrique.default_name} ({rubrique.template_type})")

    if not rubriques:
        print("ERROR: No rubriques found!")
        return

    # Redistribute posts
    print("\nRedistributing posts...")
    redistributed = 0

    for post in posts:
        # Skip deleted posts
        if post.is_deleted:
            continue

        # Randomly select a rubrique
        new_rubrique = random.choice(rubriques)
        old_rubrique = post.rubrique_template.default_name if post.rubrique_template else "None"

        # Assign new rubrique
        post.rubrique_template = new_rubrique
        post.save(update_fields=['rubrique_template'])

        print(f"  Post {post.id}: {old_rubrique} → {new_rubrique.default_name}")
        redistributed += 1

    print(f"\n✓ Successfully redistributed {redistributed} posts!")

    # Show distribution summary
    print("\nCurrent distribution:")
    for rubrique in rubriques:
        count = Post.objects.filter(rubrique_template=rubrique, is_deleted=False).count()
        if count > 0:
            print(f"  {rubrique.default_name}: {count} posts")

if __name__ == "__main__":
    redistribute_posts()
