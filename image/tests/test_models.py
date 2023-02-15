"""Tests for image app models."""
import os
import shutil
from pathlib import Path
from django.conf import settings
from django.test import override_settings
from django.core.files.base import ContentFile
from rest_framework.test import APITestCase

from image.models import Resolution, Image
from account.models import AccountTier, User
from utils.img import generate_img

FAKE_MEDIA = Path(settings.BASE_DIR / "fixtures" / "fake_media")


class TestResolutionModel(APITestCase):
    """
    Test class for the Resolution model.
    """

    def test_resolution_creation(self):
        """
        Test basic resolution creation
        """
        width = 200
        height = 200
        name = "{}x{}".format(width, height)
        res = Resolution.objects.create(width=width, height=height)

        self.assertIsInstance(res, Resolution)
        self.assertEqual(str(res), name)


class TestImageModel(APITestCase):
    """
    Test class for the Image model.
    """

    def setUp(self):
        """
        Setup fake media dir for testing purposes.
        """
        FAKE_MEDIA.mkdir(parents=True, exist_ok=True)

        self.width = 200
        self.height = 200
        self.image_name = "test_img.png"

        self.img = ContentFile(generate_img(self.width, self.height), self.image_name)

        return super().setUp()

    def tearDown(self):
        """
        Remove fake media dir and its contents after each test.
        """
        shutil.rmtree(FAKE_MEDIA)
        return super().tearDown()

    @override_settings(MEDIA_ROOT=FAKE_MEDIA)
    def test_create_image(self):
        """
        Test basic image creation.
        Tier account with one resolution, keep_original=True and can_generate_link=False.
        """
        res = Resolution.objects.create(width=self.width, height=self.height)

        tier = AccountTier.objects.create(name="TestTier", keep_original=True, can_generate_link=False)
        tier.resolutions.add(res)

        user = User.objects.create_user(username="user", tier=tier.id, password="password")

        image = Image.objects.create(user=user, img=self.img)

        self.assertIsInstance(image, Image)
        self.assertTrue(Path(f"{FAKE_MEDIA}/uploads/{user.id}/img/{self.image_name}").is_file())
        self.assertTrue(Path(f"{FAKE_MEDIA}/uploads/{user.id}/thmb/{self.image_name}").is_file())

    @override_settings(MEDIA_ROOT=FAKE_MEDIA)
    def test_create_image_keep_original_false(self):
        """
        Test basic image creation.
        Tier account with one resolution, keep_original=False and can_generate_link=False.
        """
        res = Resolution.objects.create(width=self.width, height=self.height)

        tier = AccountTier.objects.create(name="TestTier", keep_original=False, can_generate_link=False)
        tier.resolutions.add(res)

        user = User.objects.create_user(username="user", tier=tier.id, password="password")

        image = Image.objects.create(user=user, img=self.img)

        self.assertIsInstance(image, Image)
        self.assertFalse(Path(f"{FAKE_MEDIA}/uploads/{user.id}/img/{self.image_name}").is_file())
        self.assertTrue(Path(f"{FAKE_MEDIA}/uploads/{user.id}/thmb/{self.image_name}").is_file())

    @override_settings(MEDIA_ROOT=FAKE_MEDIA)
    def test_create_image_multiple_res(self):
        """
        Test basic image creation.
        Tier account with two resolutions, keep_original=True and can_generate_link=False.
        """
        res1 = Resolution.objects.create(width=self.width, height=self.height)
        res2 = Resolution.objects.create(width=self.width + 1, height=self.height + 1)

        tier = AccountTier.objects.create(name="TestTier", keep_original=True, can_generate_link=False)
        tier.resolutions.add(res1, res2)

        user = User.objects.create_user(username="user", tier=tier.id, password="password")

        image = Image.objects.create(user=user, img=self.img)

        self.assertIsInstance(image, Image)
        self.assertTrue(Path(f"{FAKE_MEDIA}/uploads/{user.id}/img/{self.image_name}").is_file())
        self.assertTrue(Path(f"{FAKE_MEDIA}/uploads/{user.id}/thmb/{self.image_name}").is_file())

        thmb_path = f"{FAKE_MEDIA}/uploads/{user.id}/thmb"
        count_files = len([name for name in os.listdir(thmb_path) if Path(f"{thmb_path}/{name}").is_file()])

        self.assertEqual(2, count_files)
