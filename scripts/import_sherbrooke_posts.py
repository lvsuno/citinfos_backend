#!/usr/bin/env python
"""
Script to import Sherbrooke mock posts into the database
This converts the frontend mock data into real database records
"""
import os
import sys
import django
from datetime import datetime, timedelta

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'citinfos_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import UserProfile
from content.models import (
    Post, Comment, PostReaction, CommentReaction, PostMedia
)
from core.models import AdministrativeDivision

User = get_user_model()

# Mock posts data from sherbrookePosts.js
SHERBROOKE_POSTS = [
    {
        "id": "post-sherbrooke-1",
        "author": {
            "username": "marie.bernard",
            "name": "Marie Bernard",
            "email": "marie.bernard@example.com"
        },
        "content": "Magnifique coucher de soleil sur le lac des Nations ce soir ! 🌅 Rien de mieux qu'une promenade au centre-ville après une journée de travail. Sherbrooke nous offre vraiment de beaux paysages urbains. #LacDesNations #Sherbrooke #CoucherDeSoleil",
        "timestamp_offset_hours": -2,
        "section": "Photographie",
        "attachments": [
            {
                "type": "image",
                "url": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&h=600&fit=crop",
                "alt": "Coucher de soleil sur le lac"
            }
        ],
        "reactions": {
            "like": 24,
            "love": 8,
            "wow": 12
        },
        "comments": [
            {
                "author": {
                    "username": "jean.tremblay",
                    "name": "Jean Tremblay",
                    "email": "jean.tremblay@example.com"
                },
                "content": "Superbe photo ! J'adore me promener là-bas aussi, surtout en fin de journée.",
                "timestamp_offset_hours": -1.5,
                "reactions": {"like": 3}
            },
            {
                "author": {
                    "username": "sophie.gagnon",
                    "name": "Sophie Gagnon",
                    "email": "sophie.gagnon@example.com"
                },
                "content": "Les couleurs sont magnifiques ! 😍 Tu étais du côté du parc Jacques-Cartier ?",
                "timestamp_offset_hours": -1,
                "reactions": {"like": 2, "love": 1}
            }
        ]
    },
    {
        "id": "post-sherbrooke-2",
        "author": {
            "username": "ville.sherbrooke",
            "name": "Ville de Sherbrooke",
            "email": "info@ville.sherbrooke.qc.ca"
        },
        "content": "📢 ANNONCE IMPORTANTE\n\nLe Festival des traditions du monde de Sherbrooke revient du 15 au 17 octobre ! 🎉\n\nAu programme :\n🎵 Spectacles multiculturels\n🍽️ Délices du monde entier  \n🎨 Ateliers créatifs pour toute la famille\n🏛️ Visites du patrimoine sherbrookois\n\nRendez-vous au parc Jacques-Cartier ! Entrée gratuite.\n\n#FestivalTraditions #Sherbrooke #Culture #Gratuit",
        "timestamp_offset_hours": -6,
        "section": "Événements",
        "attachments": [
            {
                "type": "image",
                "url": "https://images.unsplash.com/photo-1533174072545-7a4b6ad7a6c3?w=800&h=600&fit=crop",
                "alt": "Festival multiculturel"
            },
            {
                "type": "image",
                "url": "https://images.unsplash.com/photo-1511795409834-ef04bbd61622?w=400&h=300&fit=crop",
                "alt": "Parc Jacques-Cartier"
            }
        ],
        "reactions": {
            "like": 89,
            "love": 34,
            "haha": 2,
            "wow": 15,
            "angry": 1
        },
        "comments": [
            {
                "author": {
                    "username": "pierre.lavoie",
                    "name": "Pierre Lavoie",
                    "email": "pierre.lavoie@example.com"
                },
                "content": "Excellent ! Mes enfants ont adoré l'année dernière. Merci à la ville pour ces beaux événements gratuits 👏",
                "timestamp_offset_hours": -4,
                "reactions": {"like": 12, "love": 3}
            },
            {
                "author": {
                    "username": "isabelle.cote",
                    "name": "Isabelle Côté",
                    "email": "isabelle.cote@example.com"
                },
                "content": "Y aura-t-il des food trucks cette année ? J'ai hâte de goûter aux spécialités internationales ! 🌮🍜",
                "timestamp_offset_hours": -3,
                "reactions": {"like": 8, "haha": 2}
            },
            {
                "author": {
                    "username": "ville.sherbrooke",
                    "name": "Ville de Sherbrooke",
                    "email": "info@ville.sherbrooke.qc.ca"
                },
                "content": "Oui Isabelle ! Plus de 15 food trucks seront présents avec des cuisines du monde entier 🍕🥟🌯",
                "timestamp_offset_hours": -2.5,
                "reactions": {"like": 15, "love": 5}
            }
        ]
    },
    {
        "id": "post-sherbrooke-3",
        "author": {
            "username": "alex.dubois",
            "name": "Alexandre Dubois",
            "email": "alex.dubois@example.com"
        },
        "content": "Quelqu'un sait-il pourquoi la rue King Ouest est fermée près du Carrefour de l'Estrie ? 🚧 J'ai dû faire un détour de 20 minutes ce matin... Y a-t-il des travaux prévus longtemps ?",
        "timestamp_offset_hours": -4,
        "section": "Transport",
        "attachments": [],
        "reactions": {
            "like": 15,
            "haha": 3,
            "wow": 2,
            "sad": 8,
            "angry": 12
        },
        "comments": [
            {
                "author": {
                    "username": "martin.roy",
                    "name": "Martin Roy",
                    "email": "martin.roy@example.com"
                },
                "content": "Réfection complète de la chaussée jusqu'à la fin octobre selon le site de la ville. Patience ! 😅",
                "timestamp_offset_hours": -3.5,
                "reactions": {"like": 8, "sad": 2}
            },
            {
                "author": {
                    "username": "julie.langlois",
                    "name": "Julie Langlois",
                    "email": "julie.langlois@example.com"
                },
                "content": "Pareil pour moi ! J'évite complètement le secteur maintenant. Heureusement que la rue Portland est encore ouverte.",
                "timestamp_offset_hours": -3,
                "reactions": {"like": 6, "angry": 1}
            }
        ]
    },
    {
        "id": "post-sherbrooke-4",
        "author": {
            "username": "cafe.local",
            "name": "Café du Coin",
            "email": "cafe@cafeducoin.com"
        },
        "content": "☕ NOUVEAU chez nous !\n\nNous avons le plaisir de vous présenter notre nouveau mélange automne : « Érable & Vanille » 🍁\n\nTorréfié localement avec des grains biologiques équitables. Le goût parfait pour accompagner ces belles journées fraîches de septembre !\n\nVenez le découvrir dès maintenant au 245 rue Wellington Nord. Première tasse offerte aux 20 premiers clients ! 🎁\n\n#CaféLocal #Sherbrooke #TorréfactionArtisanale #Automne",
        "timestamp_offset_hours": -8,
        "section": "Commerces",
        "attachments": [
            {
                "type": "image",
                "url": "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=600&h=400&fit=crop",
                "alt": "Tasse de café avec grains"
            },
            {
                "type": "image",
                "url": "https://images.unsplash.com/photo-1506619216599-9d16d0903dfd?w=400&h=300&fit=crop",
                "alt": "Intérieur chaleureux du café"
            },
            {
                "type": "image",
                "url": "https://images.unsplash.com/photo-1442550528053-c431ecb55509?w=400&h=300&fit=crop",
                "alt": "Grains de café torréfiés"
            }
        ],
        "reactions": {
            "like": 67,
            "love": 23,
            "haha": 1,
            "wow": 5
        },
        "comments": [
            {
                "author": {
                    "username": "caroline.martin",
                    "name": "Caroline Martin",
                    "email": "caroline.martin@example.com"
                },
                "content": "Miam ! J'adore vos mélanges saisonniers. Je passe demain matin avant le travail ☕😊",
                "timestamp_offset_hours": -6,
                "reactions": {"like": 5, "love": 2}
            },
            {
                "author": {
                    "username": "robert.gagne",
                    "name": "Robert Gagné",
                    "email": "robert.gagne@example.com"
                },
                "content": "Excellente initiative ! C'est important de soutenir les commerces locaux. Votre café est vraiment délicieux 👍",
                "timestamp_offset_hours": -5,
                "reactions": {"like": 8, "love": 1}
            },
            {
                "author": {
                    "username": "cafe.local",
                    "name": "Café du Coin",
                    "email": "cafe@cafeducoin.com"
                },
                "content": "Merci Caroline et Robert ! Nous sommes ravis de faire partie de la communauté sherbrookoise ❤️",
                "timestamp_offset_hours": -4.5,
                "reactions": {"like": 12, "love": 4}
            }
        ]
    }
]


def get_or_create_user(user_data):
    """Get or create a user from user data"""
    username = user_data['username']

    try:
        user = User.objects.get(username=username)
        print(f"  ✓ User '{username}' already exists")
        return user
    except User.DoesNotExist:
        # Create new user
        user = User.objects.create_user(
            username=username,
            email=user_data['email'],
            first_name=user_data['name'].split()[0] if user_data['name'] else username,
            last_name=' '.join(user_data['name'].split()[1:]) if len(user_data['name'].split()) > 1 else ''
        )
        user.set_password('TestPass123!')  # Default password
        user.is_active = True
        user.save()

        # Create user profile
        try:
            profile = UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            profile = UserProfile.objects.create(
                user=user,
                display_name=user_data['name']
            )

        print(f"  ✓ Created user '{username}' ({user_data['name']})")
        return user


def import_posts():
    """Import all Sherbrooke posts to database"""
    print("\n" + "="*60)
    print("IMPORTING SHERBROOKE POSTS TO DATABASE")
    print("="*60 + "\n")

    # Get the two real users: elvist and tite29
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
        print(f"✓ Found user: tite29 ({tite29_profile.display_name})\n")
    except (User.DoesNotExist, UserProfile.DoesNotExist):
        print("❌ ERROR: User 'tite29' not found!")
        return

    # Get Sherbrooke division
    try:
        sherbrooke = AdministrativeDivision.objects.get(
            name__icontains='sherbrooke',
            admin_level=3,
            country__iso3='CAN'
        )
        print(f"✓ Found Sherbrooke division: {sherbrooke.name}\n")
    except AdministrativeDivision.DoesNotExist:
        print("❌ ERROR: Sherbrooke division not found in database!")
        print("   Please ensure Sherbrooke municipality exists in AdministrativeDivision")
        return

    # Get or create Sherbrooke Community
    from communities.models import Community
    sherbrooke_community, created = Community.objects.get_or_create(
        slug='sherbrooke',
        defaults={
            'name': sherbrooke.name,
            'division': sherbrooke,
            'creator': elvist_profile,
            'description': f'Community for {sherbrooke.name}',
            'community_type': 'public',
            'allow_posts': True,
        }
    )
    if created:
        print(f"✓ Created Sherbrooke community: {sherbrooke_community.name} (slug: {sherbrooke_community.slug})\n")
    else:
        print(f"✓ Found existing Sherbrooke community: {sherbrooke_community.name} (slug: {sherbrooke_community.slug})\n")

    posts_created = 0
    comments_created = 0
    reactions_created = 0

    # Alternate posts between elvist and tite29
    real_users = [elvist_profile, tite29_profile]
    real_user_names = ['elvist', 'tite29']

    for post_index, post_data in enumerate(SHERBROOKE_POSTS):
        print(f"\n📝 Processing post: {post_data['id']}")
        print("-" * 60)

        # Assign post to elvist or tite29 (alternating)
        author_profile = real_users[post_index % 2]
        author_name = real_user_names[post_index % 2]
        print(f"  📌 Assigning to: {author_name}")

        # Calculate post timestamp
        post_time = datetime.now() + timedelta(hours=post_data['timestamp_offset_hours'])

        # Check if post already exists
        existing_post = Post.objects.filter(
            author=author_profile,
            content=post_data['content'][:100]  # Check first 100 chars
        ).first()

        if existing_post:
            print(f"  ⚠️  Post already exists (ID: {existing_post.id})")
            post = existing_post
        else:
            # Create post linked to Sherbrooke community
            # (community is already linked to division)
            post = Post.objects.create(
                author=author_profile,
                content=post_data['content'],
                community=sherbrooke_community,
                post_type='article',  # Sherbrooke posts are news articles
                created_at=post_time,
                updated_at=post_time
            )
            posts_created += 1
            print(f"  ✓ Created article post in {sherbrooke_community.name}")

        # Add attachments using external URLs
        if post_data.get('attachments'):
            for idx, attachment in enumerate(post_data['attachments']):
                PostMedia.objects.get_or_create(
                    post=post,
                    media_type=attachment.get('type', 'image'),
                    external_url=attachment['url'],
                    defaults={
                        'description': attachment.get('alt', ''),
                        'order': idx
                    }
                )
            print(f"  ✓ Added {len(post_data['attachments'])} media attachments (external URLs)")

        # Create emoji reactions from mock data
        reactions_data = post_data.get('reactions', {})

        for reaction_type, count in reactions_data.items():
            # Alternate reactions between elvist and tite29
            for i in range(min(count, 2)):  # Max 2 reactions per type
                # Use elvist or tite29 alternately
                reaction_profile = real_users[i % 2]

                # Create PostReaction with emoji type
                PostReaction.objects.get_or_create(
                    post=post,
                    user=reaction_profile,
                    defaults={'reaction_type': reaction_type}
                )
                reactions_created += 1

        total_reactions = sum(reactions_data.values())
        print(f"  ✓ Added {reactions_created} emoji reactions")

        # Add comments (alternate between the two users)
        for comment_index, comment_data in enumerate(post_data.get('comments', [])):
            # Alternate comment authors between elvist and tite29
            comment_author_profile = real_users[comment_index % 2]
            comment_time = datetime.now() + timedelta(hours=comment_data['timestamp_offset_hours'])

            # Check if comment already exists
            existing_comment = Comment.objects.filter(
                post=post,
                author=comment_author_profile,
                content=comment_data['content'][:50]
            ).first()

            if not existing_comment:
                comment = Comment.objects.create(
                    post=post,
                    author=comment_author_profile,
                    content=comment_data['content'],
                    created_at=comment_time,
                    updated_at=comment_time
                )
                comments_created += 1

                # Add comment reactions (alternate between elvist and tite29)
                for reaction_type, count in comment_data.get('reactions', {}).items():
                    for i in range(min(count, 2)):  # Max 2 per type
                        # Use elvist or tite29 alternately
                        reaction_profile = real_users[i % 2]
                        CommentReaction.objects.get_or_create(
                            comment=comment,
                            user=reaction_profile,
                            defaults={'reaction_type': reaction_type}
                        )

                comment_author_name = real_user_names[comment_index % 2]
                print(f"  ✓ Added comment by {comment_author_name}")

        print(f"  ✓ Added {len(post_data.get('comments', []))} comments")

    print("\n" + "="*60)
    print("IMPORT SUMMARY")
    print("="*60)
    print(f"✓ Posts created: {posts_created}")
    print(f"✓ Comments created: {comments_created}")
    print(f"✓ Reactions created: {reactions_created}")
    print("\n📊 POST DISTRIBUTION:")
    print(f"  elvist: {(posts_created + 1) // 2} posts")
    print(f"  tite29: {posts_created // 2} posts")
    print("\n✅ Import completed successfully!\n")


if __name__ == '__main__':
    import_posts()
