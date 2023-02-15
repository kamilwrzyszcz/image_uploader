"""Tests for views."""
import base64
import shutil
from pathlib import Path
from django.conf import settings
from django.urls import reverse
from django.test import override_settings
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework import HTTP_HEADER_ENCODING, status

from image.models import Resolution, Image
from account.models import AccountTier, User
from utils.img import generate_img

FAKE_MEDIA = Path(settings.BASE_DIR / "fixtures" / "fake_media")

class TestImageViews(APITestCase):
    """Test class for list, create and get views."""
    @override_settings(MEDIA_ROOT=FAKE_MEDIA)
    def setUp(self):
        """
        Setup fake media dir and some data for testing purposes.
        """
        FAKE_MEDIA.mkdir(parents=True, exist_ok=True)

        width = 200
        height = 200

        res1 = Resolution.objects.create(width=width, height=height)
        res2 = Resolution.objects.create(width=width + 1, height=height + 1)

        tier1 = AccountTier.objects.create(name="TestTier1", keep_original=True, can_generate_link=False)
        tier1.resolutions.add(res1, res2)
        tier2 = AccountTier.objects.create(name="TestTier2", keep_original=False, can_generate_link=False)
        tier2.resolutions.add(res1)

        # credentials for Basic Auth
        user1_username, user1_password = "user1", "password"
        self.user1 = User.objects.create_user(username=user1_username, tier=tier1.id, password=user1_password)
        credentials_user1 = f"{user1_username}:{user1_password}"
        self.base64_credentials_user1 = base64.b64encode(
            credentials_user1.encode(HTTP_HEADER_ENCODING)
        ).decode(HTTP_HEADER_ENCODING)

        user2_username, user2_password = "user2", "password"
        self.user2 = User.objects.create_user(username=user2_username, tier=tier2.id, password=user2_password)
        credentials_user2 = f"{user2_username}:{user2_password}"
        self.base64_credentials_user2 = base64.b64encode(
            credentials_user2.encode(HTTP_HEADER_ENCODING)
        ).decode(HTTP_HEADER_ENCODING)

        image_name = "test_img.png"

        generated_img = generate_img(width, height)
        img = ContentFile(generated_img, image_name)

        self.image1 = Image.objects.create(user=self.user1, img=img)
        Image.objects.create(user=self.user2, img=img)

    def tearDown(self):
        """
        Remove fake media dir and its contents after each test.
        """
        shutil.rmtree(FAKE_MEDIA)
        return super().tearDown()

    @override_settings(MEDIA_ROOT=FAKE_MEDIA)
    def test_list(self):
        """
        Test list.
        Test basic list functionality.
        """
        resp = self.client.get(
            reverse('list-create-image', kwargs={"user_id": self.user1.id}),
            HTTP_AUTHORIZATION=f"Basic {self.base64_credentials_user1}"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # Presence dictated by keep_original in AccountTier
        self.assertTrue(resp.data[0]['img'] is not None)
        # Number dictated by number of resolutions in AccountTier
        self.assertTrue(len(resp.data[0]['thumbnails']) == 2)

        resp = self.client.get(
            reverse('list-create-image', kwargs={"user_id": self.user2.id}),
            HTTP_AUTHORIZATION=f"Basic {self.base64_credentials_user2}"
        )
        self.assertTrue(resp.data[0]['img'] is None)

    @override_settings(MEDIA_ROOT=FAKE_MEDIA)
    def test_list_wrong_user(self):
        """
        Attempt to fetch list loged in as a wrong user.
        """
        resp = self.client.get(
            reverse('list-create-image', kwargs={"user_id": self.user1.id}),
            HTTP_AUTHORIZATION=f"Basic {self.base64_credentials_user2}"
        )

        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
    
    @override_settings(MEDIA_ROOT=FAKE_MEDIA)
    def test_create(self):
        """
        Test basic creation.
        """
        data = {
            "img": SimpleUploadedFile(name='created_image.png',
            content=generate_img(200,200),
            content_type='image/jpeg')
        }
        resp = self.client.post(
            reverse('list-create-image', kwargs={"user_id": self.user1.id}),
            data=data,
            HTTP_AUTHORIZATION=f"Basic {self.base64_credentials_user1}"
        )
        
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    @override_settings(MEDIA_ROOT=FAKE_MEDIA)
    def test_create_too_large(self):
        """
        Test creation with too large image.
        """
        data = {
            "img": SimpleUploadedFile(name='created_image.png',
            content=generate_img(settings.MAX_WIDTH + 1, settings.MAX_HEIGHT + 1),
            content_type='image/jpeg')
        }
        resp = self.client.post(
            reverse('list-create-image', kwargs={"user_id": self.user1.id}),
            data=data,
            HTTP_AUTHORIZATION=f"Basic {self.base64_credentials_user1}"
        )

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    @override_settings(MEDIA_ROOT=FAKE_MEDIA)
    def test_get(self):
        """
        Test basic get functionality.
        """
        resp = self.client.get(
            reverse('get-image', kwargs={"user_id": self.user1.id, "pk": self.image1.id}),
            HTTP_AUTHORIZATION=f"Basic {self.base64_credentials_user1}"
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(Path(self.image1.img.url).name, Path(resp.data['img']).name)

    @override_settings(MEDIA_ROOT=FAKE_MEDIA)
    def test_get_wrong_user(self):
        """
        Attempt to fetch Image loged in as a wrong user.
        """
        resp = self.client.get(
            reverse('get-image', kwargs={"user_id": self.user1.id, "pk": self.image1.id}),
            HTTP_AUTHORIZATION=f"Basic {self.base64_credentials_user2}"
        )

        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


class TestLinksViews(APITestCase):
    """
    Test class link-ralated views.
    """
    @override_settings(MEDIA_ROOT=FAKE_MEDIA)
    def setUp(self):
        """
        Setup fake media dir and some data for testing purposes.
        """
        FAKE_MEDIA.mkdir(parents=True, exist_ok=True)

        width, height = 200, 200

        res = Resolution.objects.create(width=width, height=height)

        tier1 = AccountTier.objects.create(name="TestTier1", keep_original=True, can_generate_link=True)
        tier1.resolutions.add(res)
        tier2 = AccountTier.objects.create(name="TestTier2", keep_original=True, can_generate_link=False)
        tier2.resolutions.add(res)

        # credentials for Basic Auth
        user1_username, user1_password = "user1", "password"
        self.user1 = User.objects.create_user(username=user1_username, tier=tier1.id, password=user1_password)
        credentials_user1 = f"{user1_username}:{user1_password}"
        self.base64_credentials_user1 = base64.b64encode(
            credentials_user1.encode(HTTP_HEADER_ENCODING)
        ).decode(HTTP_HEADER_ENCODING)

        user2_username, user2_password = "user2", "password"
        self.user2 = User.objects.create_user(username=user2_username, tier=tier2.id, password=user2_password)
        credentials_user2 = f"{user2_username}:{user2_password}"
        self.base64_credentials_user2 = base64.b64encode(
            credentials_user2.encode(HTTP_HEADER_ENCODING)
        ).decode(HTTP_HEADER_ENCODING)

        image_name = "test_img.png"

        generated_img = generate_img(width, height)
        img = ContentFile(generated_img, image_name)

        self.image1 = Image.objects.create(user=self.user1, img=img)
        self.image2 = Image.objects.create(user=self.user2, img=img)

        return super().setUp()

    def tearDown(self):
        """
        Remove fake media dir and its contents after each test.
        """
        shutil.rmtree(FAKE_MEDIA)
        return super().tearDown()

    @override_settings(MEDIA_ROOT=FAKE_MEDIA)
    def test_create_link_wrong_ttl(self):
        """
        Test creation of link to the binary image with wrong ttl.
        """
        data = {
            "ttl": 200 
        }
        resp = self.client.post(
            reverse('generate-link', kwargs={"user_id": self.user1.id, "pk": self.image1.id}),
            data=data,
            HTTP_AUTHORIZATION=f"Basic {self.base64_credentials_user1}"
        )

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    @override_settings(MEDIA_ROOT=FAKE_MEDIA)
    def test_create_link_wrong_user(self):
        """
        Test creation of link to the binary image with wrong user.
        This user does not have permission to generate temp links.
        """
        data = {
            "ttl": 300 
        }
        resp = self.client.post(
            reverse('generate-link', kwargs={"user_id": self.user2.id, "pk": self.image2.id}),
            data=data,
            HTTP_AUTHORIZATION=f"Basic {self.base64_credentials_user2}"
        )
        
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    @override_settings(MEDIA_ROOT=FAKE_MEDIA)
    def test_create_link(self):
        """
        Test creation of link to the binary image.
        """
        data = {
            "ttl": 300 
        }
        resp = self.client.post(
            reverse('generate-link', kwargs={"user_id": self.user1.id, "pk": self.image1.id}),
            data=data,
            HTTP_AUTHORIZATION=f"Basic {self.base64_credentials_user1}"
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    @override_settings(MEDIA_ROOT=FAKE_MEDIA)
    def test_can_access_img(self):
        """
        Test access to the generated binary image.
        """
        data = {
            "ttl": 300 
        }
        resp = self.client.post(
            reverse('generate-link', kwargs={"user_id": self.user1.id, "pk": self.image1.id}),
            data=data,
            HTTP_AUTHORIZATION=f"Basic {self.base64_credentials_user1}"
        )

        resp = self.client.get(resp.data['link'])
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(Path(f"{FAKE_MEDIA}/uploads/{self.user1.id}/temp/{self.image1.id}.png").is_file())
