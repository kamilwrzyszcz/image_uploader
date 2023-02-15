"""Tests for account app models."""
from rest_framework.test import APITestCase

from account.models import AccountTier, User


class TestAccountTierModel(APITestCase):
    """
    Test class for the AccountTier model.
    """

    def test_create_tier(self):
        """
        Test basic AccountTier creation.
        """
        name = "TestTier"
        tier = AccountTier.objects.create(name=name, keep_original=True, can_generate_link=False)

        self.assertIsInstance(tier, AccountTier)
        self.assertEqual(str(tier), name)
    
    def test_tier_keep_original_generate_link_mismatch(self):
        """
        Test creation of AccountTier with mismatched parameters that make no sense.
        AccountTier that would not allow to keep original image but allows creation of temp link to that image.
        Raises Error.
        """
        self.assertRaises(
            ValueError, 
            AccountTier.objects.create, 
            name="TestTier", 
            keep_original=False, 
            can_generate_link=True
            )
        with self.assertRaisesMessage(ValueError, "cannot set temp link generation to True when keep_original is False"):
            AccountTier.objects.create(name="TestTier", keep_original=False, can_generate_link=True)


class TestUserModel(APITestCase):
    """
    Test class for the User model.
    """

    def test_create_user(self):
        """
        Test basic user creation.
        """
        username = "user1"
        password = "password"
        tier = AccountTier.objects.create(name="TestTier", keep_original=True, can_generate_link=False)
        user = User.objects.create_user(username=username, tier=tier.id, password=password)

        self.assertIsInstance(user, User)
        self.assertEqual(user.username, username)

    def test_create_superuser(self):
        """
        Test superuser creation.
        """
        username = "admin"
        password = "password"
        tier = AccountTier.objects.create(name="TestTier", keep_original=True, can_generate_link=False)
        user = User.objects.create_superuser(username=username, tier=tier.id, password=password)

        self.assertIsInstance(user, User)
        self.assertEqual(user.username, username)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_create_user_no_password(self):
        """
        Test creation of user without a password.
        Raises error.
        """
        username = "user1"
        password = None
        tier = AccountTier.objects.create(name="TestTier", keep_original=True, can_generate_link=False)

        self.assertRaises(
            TypeError, 
            User.objects.create_user, 
            username=username, 
            tier=tier, 
            password=password
            )
        with self.assertRaisesMessage(TypeError, "No password provided"):
            User.objects.create_user(username=username, tier=tier.id, password=password)

    def test_create_user_no_tier(self):
        """
        Test user creation without account tier.
        Raises error.
        """
        username = "user1"
        password = "password"

        self.assertRaises(
            TypeError, 
            User.objects.create_user, 
            username=username, 
            tier=None, 
            password=password
            )
        with self.assertRaisesMessage(TypeError, "Users must have a tier account."):
            User.objects.create_user(username=username, tier=None, password=password)
