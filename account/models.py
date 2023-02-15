"""Models for account app."""
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager

from image.models import Resolution

class AccountTier(models.Model):
    """
    Tier of the account that will dictate whether or not user can keep original resolution of the uploaded picture,
    can he generate temp link to the binary picture and with what resoultion will thumbnails be created.
    """
    name = models.CharField(max_length=50, unique=True, help_text="Name/Title of the account tier")
    keep_original = models.BooleanField(help_text="Whether or not keep the originally uploaded image")
    can_generate_link = models.BooleanField(help_text="Whether or not can create temp link to the original image")
    resolutions = models.ManyToManyField(Resolution)

    def save(self, *args, **kwargs):
        if self.can_generate_link and not self.keep_original:
            raise ValueError("cannot set temp link generation to True when keep_original is False")
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name


class UserManager(BaseUserManager):
    """Custom UserManager."""

    def create_user(self, username: str, tier: int, password: str):
        if password is None:
            raise TypeError('No password provided')
        if tier is None:
            raise TypeError('Users must have a tier account.')

        user = self.model()
        user.username = username
        user.set_password(password)
        # with id instead of object we can use default createsuperuser command
        user.tier = AccountTier.objects.get(id=tier)
        user.save()

        return user

    def create_superuser(self, username: str, tier: int, password: str):

        user = self.create_user(username, tier, password)
        user.is_superuser = True
        user.is_staff = True
        user.save()

        return user


class User(AbstractUser):
    """
    Custom user model to accomodate AccountTier relationship
    """
    tier = models.ForeignKey(AccountTier, on_delete=models.PROTECT)
    objects = UserManager()
    

    REQUIRED_FIELDS = ['tier']
