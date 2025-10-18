#!/usr/bin/env python
"""
Script to reassign Sherbrooke posts to existing users: elvist and tite29
This will distribute the posts between these two real users
"""
import os
import sys
import django

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'citinfos_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import UserProfile
from content.models import Post

User = get_user_model()


def reassign_posts():
    """
    Reassign Sherbrooke posts to elvist and tite29
    """
    print("\n" + "="*60)
    print("REASSIGNING SHERBROOKE POSTS TO REAL USERS")
    print("="*60 + "\n")

    # Get the two users
    try:
        elvist_user = User.objects.get(username='elvist')
        elvist_profile = UserProfile.objects.get(user=elvist_user)
        print(f"✓ Found user: elvist ({elvist_profile.display_name})")
    except (User.DoesNotExist, UserProfile.DoesNotExist):
        print("❌ ERROR: User 'elvist' not found!")
        return

    try:
        tite29_user = User.objects.get(username='tite29')
        tite29_profile = UserProfile.objects.get(user=tite29_user)
        print(f"✓ Found user: tite29 ({tite29_profile.display_name})")
    except (User.DoesNotExist, UserProfile.DoesNotExist):
        print("❌ ERROR: User 'tite29' not found!")
        return

    # Get Sherbrooke posts (posts from mock users)
    mock_usernames = [
        'marie.bernard',
        'ville.sherbrooke',
        'alex.dubois',
        'cafe.local',
        'jean.tremblay',
        'sophie.gagnon',
        'pierre.lavoie',
        'isabelle.cote',
        'martin.roy',
        'julie.langlois',
        'caroline.martin',
        'robert.gagne'
    ]

    print(f"\n📝 Finding posts from mock users...")
    mock_user_ids = User.objects.filter(username__in=mock_usernames).values_list('id', flat=True)
    mock_profile_ids = UserProfile.objects.filter(user__id__in=mock_user_ids).values_list('id', flat=True)

    posts = Post.objects.filter(author__id__in=mock_profile_ids).order_by('created_at')
    
    if not posts.exists():
        print("❌ No posts found from mock users. Please run import_sherbrooke_posts.py first!")
        return

    print(f"✓ Found {posts.count()} posts to reassign\n")

    # Distribution plan:
    # ALL posts will be distributed between elvist and tite29
    # elvist gets posts 1, 3, 5, 7... (odd numbered)
    # tite29 gets posts 2, 4, 6, 8... (even numbered)
    
    reassigned_count = 0
    elvist_count = 0
    tite29_count = 0
    
    for index, post in enumerate(posts, start=1):
        old_author = post.author.user.username
        
        # Alternate between elvist and tite29
        if index % 2 == 1:
            new_author = elvist_profile
            new_username = 'elvist'
            elvist_count += 1
        else:
            new_author = tite29_profile
            new_username = 'tite29'
            tite29_count += 1
        
        # Update post author
        post.author = new_author
        post.save()
        
        reassigned_count += 1
        
        # Show preview of content
        content_preview = (post.content[:60] + "..." 
                          if len(post.content) > 60 
                          else post.content)
        print(f"  ✓ Post #{index}: {old_author} → {new_username}")
        print(f"    Section: {post.section or 'General'}")
        print(f"    Preview: {content_preview}")
        comments_count = post.comments.count()
        reactions_count = post.reactions.count()
        print(f"    Comments: {comments_count}, Reactions: {reactions_count}")
        print()

    print("=" * 60)
    print("REASSIGNMENT SUMMARY")
    print("=" * 60)
    print(f"✓ Posts reassigned to elvist: {elvist_count}")
    print(f"✓ Posts reassigned to tite29: {tite29_count}")
    print(f"✓ Total posts reassigned: {reassigned_count}")
    print("\n✅ ALL posts reassigned successfully!\n")
    
    # Show final distribution
    print("📊 FINAL DISTRIBUTION:")
    print("-" * 60)
    elvist_posts = Post.objects.filter(author=elvist_profile).count()
    tite29_posts = Post.objects.filter(author=tite29_profile).count()
    print(f"  elvist: {elvist_posts} posts")
    print(f"  tite29: {tite29_posts} posts")
    print()


if __name__ == '__main__':
    # Confirm before proceeding
    print("\n⚠️  This will reassign Sherbrooke posts to elvist and tite29.")
    response = input("Continue? (yes/no): ").strip().lower()
    
    if response == 'yes':
        reassign_posts()
    else:
        print("❌ Operation cancelled.")
