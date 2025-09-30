"""Comprehensive tests for all communities app tasks and CRUD operations."""

from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User


from accounts.models import UserProfile
from analytics.models import SystemMetric
from communities.models import (
    Community, CommunityMembership, CommunityInvitation,
    CommunityJoinRequest, CommunityRole, CommunityModeration
)
from communities.tasks import (
    cleanup_expired_community_invitations,
    update_community_member_counts, cleanup_inactive_communities,
    process_community_join_requests, validate_community_access_rules
)


class ComprehensiveCommunitiesTestCase(TestCase):
    """Comprehensive test case for all communities functionality."""

    def setUp(self):
        """Set up test data."""
        # Create test users
        self.user1 = User.objects.create_user(
            username='creator',
            email='creator@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='member',
            email='member@example.com',
            password='testpass123'
        )
        self.user3 = User.objects.create_user(
            username='applicant',
            email='applicant@example.com',
            password='testpass123'
        )

        # Create or ensure user profiles (safe pattern)
        self.creator_profile, _ = UserProfile.objects.get_or_create(user=self.user1)
        UserProfile.objects.filter(user=self.user1).update(
            role='creator',
            bio='Community creator',
            phone_number='+1111111000',
            date_of_birth='1990-01-01',
            is_verified=True,
            last_verified_at=timezone.now()
        )
        self.creator_profile.refresh_from_db()

        self.member_profile, _ = UserProfile.objects.get_or_create(user=self.user2)
        UserProfile.objects.filter(user=self.user2).update(
            role='member',
            bio='Community member',
            phone_number='+1111111001',
            date_of_birth='1990-01-01',
            is_verified=True,
            last_verified_at=timezone.now()
        )
        self.member_profile.refresh_from_db()

        self.applicant_profile, _ = UserProfile.objects.get_or_create(user=self.user3)
        UserProfile.objects.filter(user=self.user3).update(
            role='applicant',
            bio='Community applicant',
            phone_number='+1111111002',
            date_of_birth='1990-01-01',
            is_verified=True,
            last_verified_at=timezone.now()
        )
        self.applicant_profile.refresh_from_db()

        # Create public/private/restricted communities
        self.public_community = Community.objects.create(
            name='Public Community',
            slug='public-community',
            description='A public community',
            creator=self.creator_profile,
            community_type='public'
        )

        self.private_community = Community.objects.create(
            name='Private Community',
            slug='private-community',
            description='A private community',
            creator=self.creator_profile,
            community_type='private'
        )

        self.restricted_community = Community.objects.create(
            name='Restricted Community',
            slug='restricted-community',
            description='A restricted community',
            creator=self.creator_profile,
            community_type='restricted'
        )

        # Create community roles
        self.admin_role = CommunityRole.objects.create(
            community=self.public_community,
            name='Admin',
            permissions={
                'can_post': True,
                'can_moderate': True,
                'can_manage_members': True,
                'can_manage_community': True
            },
            color='#FF0000',
            is_default=False
        )

        self.member_role = CommunityRole.objects.create(
            community=self.public_community,
            name='Member',
            permissions={'can_post': True, 'can_comment': True},
            color='#0000FF',
            is_default=True
        )

        # Create similar roles for other communities
        for community in [self.private_community, self.restricted_community]:
            CommunityRole.objects.create(
                community=community,
                name='Member',
                permissions={'can_post': True, 'can_comment': True},
                is_default=True
            )

    def test_crud_operations_community(self):
        """Test CRUD operations for Community model."""
        print("\n=== Testing Community CRUD Operations ===")

        # CREATE
        community = Community.objects.create(
            name='CRUD Test Community',
            slug='crud-test-community',
            description='Testing CRUD operations',
            creator=self.creator_profile,
            community_type='public',
            rules='Be nice to each other',
            tags=['test', 'crud']
        )
        print(f"✓ Created community: {community.name}")

        # READ
        retrieved_community = Community.objects.get(slug='crud-test-community')
        self.assertEqual(retrieved_community.name, 'CRUD Test Community')
        self.assertEqual(retrieved_community.creator, self.creator_profile)
        print(f"✓ Retrieved community: {retrieved_community.name}")

        # UPDATE
        retrieved_community.description = 'Updated description'
        retrieved_community.tags = ['test', 'crud', 'updated']
        retrieved_community.save()

        updated_community = Community.objects.get(slug='crud-test-community')
        self.assertEqual(updated_community.description, 'Updated description')
        self.assertIn('updated', updated_community.tags)
        print(f"✓ Updated community: {updated_community.description}")

        # DELETE
        community_id = updated_community.id
        updated_community.delete()

        with self.assertRaises(Community.DoesNotExist):
            Community.objects.get(id=community_id)
        print(f"✓ Deleted community successfully")

    def test_crud_operations_membership(self):
        """Test CRUD operations for CommunityMembership model."""
        print("\n=== Testing CommunityMembership CRUD Operations ===")

        # CREATE
        membership = CommunityMembership.objects.create(
            community=self.public_community,
            user=self.member_profile,
            role=self.member_role,
            status='active'
        )
        print(f"✓ Created membership for: {membership.user.user.username}")

        # READ
        retrieved_membership = CommunityMembership.objects.get(
            community=self.public_community,
            user=self.member_profile
        )
        self.assertEqual(retrieved_membership.role, self.member_role)
        self.assertEqual(retrieved_membership.status, 'active')
        print(f"✓ Retrieved membership: {retrieved_membership.role.name}")

        # UPDATE
        retrieved_membership.role = self.admin_role
        retrieved_membership.notifications_enabled = False
        retrieved_membership.save()

        updated_membership = CommunityMembership.objects.get(
            community=self.public_community,
            user=self.member_profile
        )
        self.assertEqual(updated_membership.role, self.admin_role)
        self.assertFalse(updated_membership.notifications_enabled)
        print(f"✓ Updated membership role to: {updated_membership.role.name}")

        # DELETE
        membership_id = updated_membership.id
        updated_membership.delete()

        with self.assertRaises(CommunityMembership.DoesNotExist):
            CommunityMembership.objects.get(id=membership_id)
        print(f"✓ Deleted membership successfully")

    def test_crud_operations_invitation(self):
        """Test CRUD operations for CommunityInvitation model."""
        print("\n=== Testing CommunityInvitation CRUD Operations ===")

        # CREATE
        invitation = CommunityInvitation.objects.create(
            community=self.private_community,
            inviter=self.creator_profile,
            invitee=self.applicant_profile,
            message='Join our private community!',
            expires_at=timezone.now() + timedelta(days=7)
        )
        print(f"✓ Created invitation from {invitation.inviter.user.username} to {invitation.invitee.user.username}")

        # READ
        retrieved_invitation = CommunityInvitation.objects.get(
            community=self.private_community,
            invitee=self.applicant_profile
        )
        self.assertEqual(retrieved_invitation.status, 'pending')
        self.assertEqual(retrieved_invitation.message, 'Join our private community!')
        print(f"✓ Retrieved invitation: {retrieved_invitation.status}")

        # UPDATE
        retrieved_invitation.status = 'accepted'
        retrieved_invitation.responded_at = timezone.now()
        retrieved_invitation.save()

        updated_invitation = CommunityInvitation.objects.get(
            community=self.private_community,
            invitee=self.applicant_profile
        )
        self.assertEqual(updated_invitation.status, 'accepted')
        self.assertIsNotNone(updated_invitation.responded_at)
        print(f"✓ Updated invitation status to: {updated_invitation.status}")

        # DELETE
        invitation_id = updated_invitation.id
        updated_invitation.delete()

        with self.assertRaises(CommunityInvitation.DoesNotExist):
            CommunityInvitation.objects.get(id=invitation_id)
        print(f"✓ Deleted invitation successfully")

    def test_crud_operations_join_request(self):
        """Test CRUD operations for CommunityJoinRequest model."""
        print("\n=== Testing CommunityJoinRequest CRUD Operations ===")

        # CREATE
        join_request = CommunityJoinRequest.objects.create(
            community=self.restricted_community,
            user=self.applicant_profile,
            message='I would like to join this community',
            status='pending'
        )
        print(f"✓ Created join request from {join_request.user.user.username}")

        # READ
        retrieved_request = CommunityJoinRequest.objects.get(
            community=self.restricted_community,
            user=self.applicant_profile
        )
        self.assertEqual(retrieved_request.status, 'pending')
        self.assertEqual(retrieved_request.message, 'I would like to join this community')
        print(f"✓ Retrieved join request: {retrieved_request.status}")

        # UPDATE
        retrieved_request.status = 'approved'
        retrieved_request.reviewed_at = timezone.now()
        retrieved_request.review_message = 'Welcome to the community!'
        retrieved_request.reviewed_by = self.creator_profile
        retrieved_request.save()

        updated_request = CommunityJoinRequest.objects.get(
            community=self.restricted_community,
            user=self.applicant_profile
        )
        self.assertEqual(updated_request.status, 'approved')
        self.assertEqual(updated_request.reviewed_by, self.creator_profile)
        print(f"✓ Updated join request status to: {updated_request.status}")

        # DELETE
        request_id = updated_request.id
        updated_request.delete()

        with self.assertRaises(CommunityJoinRequest.DoesNotExist):
            CommunityJoinRequest.objects.get(id=request_id)
        print(f"✓ Deleted join request successfully")

    def test_crud_operations_role(self):
        """Test CRUD operations for CommunityRole model."""
        print("\n=== Testing CommunityRole CRUD Operations ===")

        # CREATE
        role = CommunityRole.objects.create(
            community=self.public_community,
            name='Moderator',
            permissions={
                'can_post': True,
                'can_moderate': True,
                'can_delete_posts': True
            },
            color='#00FF00',
            is_default=False
        )
        print(f"✓ Created role: {role.name}")

        # READ
        retrieved_role = CommunityRole.objects.get(
            community=self.public_community,
            name='Moderator'
        )
        self.assertEqual(retrieved_role.permissions['can_moderate'], True)
        self.assertEqual(retrieved_role.color, '#00FF00')
        print(f"✓ Retrieved role: {retrieved_role.name}")

        # UPDATE
        retrieved_role.permissions['can_ban_users'] = True
        retrieved_role.color = '#FFFF00'
        retrieved_role.save()

        updated_role = CommunityRole.objects.get(
            community=self.public_community,
            name='Moderator'
        )
        self.assertTrue(updated_role.permissions['can_ban_users'])
        self.assertEqual(updated_role.color, '#FFFF00')
        print(f"✓ Updated role permissions and color to: {updated_role.color}")

        # DELETE
        role_id = updated_role.id
        updated_role.delete()

        with self.assertRaises(CommunityRole.DoesNotExist):
            CommunityRole.objects.get(id=role_id)
        print(f"✓ Deleted role successfully")

    def test_crud_operations_moderation(self):
        """Test CRUD operations for CommunityModeration model."""
        print("\n=== Testing CommunityModeration CRUD Operations ===")

        # CREATE
        moderation = CommunityModeration.objects.create(
            community=self.public_community,
            moderator=self.creator_profile,
            target=self.member_profile,
            action_type='warning',
            reason='Inappropriate language'
        )
        print(f"✓ Created moderation action: {moderation.action_type}")

        # READ
        retrieved_moderation = CommunityModeration.objects.get(
            community=self.public_community,
            target=self.member_profile
        )
        self.assertEqual(retrieved_moderation.action_type, 'warning')
        self.assertEqual(retrieved_moderation.reason, 'Inappropriate language')
        print(f"✓ Retrieved moderation: {retrieved_moderation.action_type}")

        # UPDATE
        retrieved_moderation.action_type = 'temporary_ban'
        # retrieved_moderation.duration = 24  # 24 hours
        retrieved_moderation.expires_at = timezone.now() + timedelta(hours=24)
        retrieved_moderation.save()

        updated_moderation = CommunityModeration.objects.get(
            community=self.public_community,
            target=self.member_profile
        )
        self.assertEqual(updated_moderation.action_type, 'temporary_ban')
        self.assertEqual(updated_moderation.duration.total_seconds() // 3600, 24)
        print(f"✓ Updated moderation to: {updated_moderation.action_type}")

        # DELETE
        moderation_id = updated_moderation.id
        updated_moderation.delete()

        with self.assertRaises(CommunityModeration.DoesNotExist):
            CommunityModeration.objects.get(id=moderation_id)
        print(f"✓ Deleted moderation action successfully")

    def test_task_update_community_analytics(self):
        """Test update_community_analytics task."""
        print("\n=== Testing update_community_analytics Task ===")

        # Create some memberships
        CommunityMembership.objects.create(
            community=self.public_community,
            user=self.member_profile,
            role=self.member_role,
            status='active',
            last_active=timezone.now()
        )

        # Run the task
        result = update_community_analytics()

        print(f"✓ Task result: {result}")
        self.assertIn('Updated analytics for', result)

        # Check that metrics were created
        metrics = SystemMetric.objects.filter(
            metric_type='community_engagement'
        )
        self.assertGreater(metrics.count(), 0)
        print(f"✓ Created {metrics.count()} analytics metrics")

    def test_task_cleanup_expired_invitations(self):
        """Test cleanup_expired_community_invitations task."""
        print("\n=== Testing cleanup_expired_community_invitations Task ===")

        # Create expired invitation
        expired_invitation = CommunityInvitation.objects.create(
            community=self.private_community,
            inviter=self.creator_profile,
            invitee=self.member_profile,
            expires_at=timezone.now() - timedelta(days=1),
            status='pending'
        )

        # Create valid invitation
        valid_invitation = CommunityInvitation.objects.create(
            community=self.private_community,
            inviter=self.creator_profile,
            invitee=self.applicant_profile,
            expires_at=timezone.now() + timedelta(days=7),
            status='pending'
        )

        # Run the task
        result = cleanup_expired_community_invitations()

        print(f"✓ Task result: {result}")
        self.assertIn('Marked 1 community invitations as expired', result)

        # Check invitation statuses
        expired_invitation.refresh_from_db()
        valid_invitation.refresh_from_db()

        self.assertEqual(expired_invitation.status, 'expired')
        self.assertEqual(valid_invitation.status, 'pending')
        print(f"✓ Expired invitation marked as expired, valid invitation unchanged")

    def test_task_update_member_counts(self):
        """Test update_community_member_counts task."""
        print("\n=== Testing update_community_member_counts Task ===")

        # Create memberships
        CommunityMembership.objects.create(
            community=self.public_community,
            user=self.member_profile,
            role=self.member_role,
            status='active'
        )
        CommunityMembership.objects.create(
            community=self.public_community,
            user=self.applicant_profile,
            role=self.member_role,
            status='inactive'
        )

        # Manually set incorrect count
        self.public_community.members_count = 0
        self.public_community.save()

        # Run the task
        result = update_community_member_counts()

        print(f"✓ Task result: {result}")
        self.assertIn('Updated member counts for', result)

        # Check count was updated
        self.public_community.refresh_from_db()
        self.assertEqual(self.public_community.members_count, 1)  # Only active members
        print(f"✓ Member count updated to: {self.public_community.members_count}")

    def test_task_cleanup_inactive_communities(self):
        """Test cleanup_inactive_communities task."""
        print("\n=== Testing cleanup_inactive_communities Task ===")

        # Create old community
        old_community = Community.objects.create(
            name='Old Community',
            slug='old-community',
            creator=self.creator_profile,
            is_active=True
        )

        # Manually set old updated_at date
        Community.objects.filter(id=old_community.id).update(
            updated_at=timezone.now() - timedelta(days=100)
        )

        # Run the task
        result = cleanup_inactive_communities()

        print(f"✓ Task result: {result}")
        self.assertIn('communities as inactive', result)

        # Check community was marked inactive
        old_community.refresh_from_db()
        self.assertFalse(old_community.is_active)
        print(f"✓ Old community marked as inactive")

    def test_task_process_join_requests(self):
        """Test process_community_join_requests task."""
        print("\n=== Testing process_community_join_requests Task ===")

        # Create invalid join request for public community
        invalid_request = CommunityJoinRequest.objects.create(
            community=self.public_community,
            user=self.applicant_profile,
            status='pending'
        )

        # Create valid old join request for restricted community
        valid_request = CommunityJoinRequest.objects.create(
            community=self.restricted_community,
            user=self.applicant_profile,
            status='pending'
        )

        # Manually set old created_at date
        CommunityJoinRequest.objects.filter(id=valid_request.id).update(
            created_at=timezone.now() - timedelta(days=8)
        )

        # Run the task
        result = process_community_join_requests()

        print(f"✓ Task result: {result}")
        self.assertIn('Rejected', result)
        self.assertIn('auto-approved', result)

        # Check request statuses
        invalid_request.refresh_from_db()
        valid_request.refresh_from_db()

        self.assertEqual(invalid_request.status, 'rejected')
        self.assertEqual(valid_request.status, 'approved')
        print(f"✓ Invalid request rejected, valid request approved")

    def test_task_validate_access_rules(self):
        """Test validate_community_access_rules task."""
        print("\n=== Testing validate_community_access_rules Task ===")

        # Create invalid join request
        invalid_request = CommunityJoinRequest.objects.create(
            community=self.private_community,
            user=self.applicant_profile,
            status='pending'
        )

        # Create expired invitation
        expired_invitation = CommunityInvitation.objects.create(
            community=self.private_community,
            inviter=self.creator_profile,
            invitee=self.member_profile,
            expires_at=timezone.now() - timedelta(hours=1),
            status='pending'
        )

        # Run the task
        result = validate_community_access_rules()

        print(f"✓ Task result: {result}")
        self.assertIn('Rejected', result)
        self.assertIn('expired', result)

        # Check statuses
        invalid_request.refresh_from_db()
        expired_invitation.refresh_from_db()

        self.assertEqual(invalid_request.status, 'rejected')
        self.assertEqual(expired_invitation.status, 'expired')
        print(f"✓ Invalid request rejected, expired invitation marked as expired")

    def test_comprehensive_workflow(self):
        """Test a comprehensive workflow."""
        print("\n=== Testing Comprehensive Workflow ===")

        # 1. Create a new community
        workflow_community = Community.objects.create(
            name='Workflow Test Community',
            slug='workflow-test',
            description='Testing complete workflow',
            creator=self.creator_profile,
            community_type='restricted'
        )

        # 2. Create roles
        admin_role = CommunityRole.objects.create(
            community=workflow_community,
            name='Admin',
            permissions={'can_post': True, 'can_moderate': True},
            is_default=False
        )

        member_role = CommunityRole.objects.create(
            community=workflow_community,
            name='Member',
            permissions={'can_post': True},
            is_default=True
        )

        # 3. Create memberships
        creator_membership = CommunityMembership.objects.create(
            community=workflow_community,
            user=self.creator_profile,
            role=admin_role,
            status='active'
        )

        # 4. Create join request
        join_request = CommunityJoinRequest.objects.create(
            community=workflow_community,
            user=self.member_profile,
            message='I want to join this community',
            status='pending'
        )

        # 5. Approve join request manually
        join_request.status = 'approved'
        join_request.reviewer = self.creator_profile
        join_request.reviewed_at = timezone.now()
        join_request.save()

        # 6. Create membership for approved user
        member_membership = CommunityMembership.objects.create(
            community=workflow_community,
            user=self.member_profile,
            role=member_role,
            status='active'
        )

        # 7. Create moderation action
        moderation = CommunityModeration.objects.create(
            community=workflow_community,
            moderator=self.creator_profile,
            target=self.member_profile,
            action_type='warning',
            reason='Test moderation'
        )

        # 8. Run all tasks
        analytics_result = update_community_analytics()
        member_count_result = update_community_member_counts()

        print(f"✓ Created complete workflow with community, roles, memberships, and moderation")
        print(f"✓ Analytics task: {analytics_result}")
        print(f"✓ Member count task: {member_count_result}")

        # Verify final state
        workflow_community.refresh_from_db()
        self.assertEqual(workflow_community.members_count, 2)  # Creator + member
        self.assertTrue(
            CommunityMembership.objects.filter(
                community=workflow_community,
                status='active'
            ).count() == 2
        )
        print("✓ Workflow completed successfully")

    def run_all_tests(self):
        """Run all tests in sequence."""
        print("\n" + "="*50)
        print("STARTING COMPREHENSIVE COMMUNITIES TESTING")
        print("="*50)

        try:
            self.test_crud_operations_community()
            self.test_crud_operations_membership()
            self.test_crud_operations_invitation()
            self.test_crud_operations_join_request()
            self.test_crud_operations_role()
            self.test_crud_operations_moderation()

            self.test_task_update_community_analytics()
            self.test_task_cleanup_expired_invitations()
            self.test_task_update_member_counts()
            self.test_task_cleanup_inactive_communities()
            self.test_task_process_join_requests()
            self.test_task_validate_access_rules()

            self.test_comprehensive_workflow()

            print("\n" + "="*50)
            print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
            print("="*50)

        except Exception as e:
            print(f"\n❌ TEST FAILED: {str(e)}")
            raise


def run_comprehensive_test():
    """Function to run comprehensive test from command line."""
    from django.test.utils import setup_test_environment, teardown_test_environment
    # from django.test.runner import DiscoverRunner
    # from django.conf import settings

    # Set up test environment
    setup_test_environment()

    # Create test case instance
    test_case = ComprehensiveCommunitiesTestCase()
    test_case.setUp()

    # Run all tests
    test_case.run_all_tests()

    # Clean up
    teardown_test_environment()


if __name__ == '__main__':
    run_comprehensive_test()
