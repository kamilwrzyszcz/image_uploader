"""Models for image app."""
from io import BytesIO
from pathlib import Path
from PIL import Image as ImageObj
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.core.files.images import get_image_dimensions
from django.core.files.base import ContentFile
from django.db.models.signals import post_delete
from django.dispatch.dispatcher import receiver



class Resolution(models.Model):
    """Model for thumbnails resolutions."""
    width = models.IntegerField(validators=[
        MinValueValidator(settings.MIN_WIDTH),
        MaxValueValidator(settings.MAX_WIDTH)
        ]
    )
    height = models.IntegerField(validators=[
        MinValueValidator(settings.MIN_HEIGHT),
        MaxValueValidator(settings.MAX_HEIGHT)
        ]
    )

    class Meta:
        unique_together = ('width', 'height',)

    def __str__(self) -> str:
        return f"{self.width}x{self.height}"


def user_img_path(instance, filename):
    """Dynamic save path for image in Image model."""
    path = Path(f"uploads/{instance.user.id}/img/{filename}")
    return path


class Image(models.Model):
    """
    Image Model.
    Holds user relation and uploaded img itself.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    img = models.ImageField(upload_to=user_img_path)

    def save(self, *args, **kwargs):
        """
        This overriden save method sets uploaded img to None if users AccountTier
        doesn't allow keeping original uploaded image.
        It also creates thumbnails out of the uploaded img. Number of created thumbnails
        depends on number of specified Resolutions in users AccountTier.
        """
        # temp for manipulation img in thumbnail creation
        temp_img = self.img
        tier = self.user.tier
        if not tier.keep_original:
            self.img = None
        super().save(*args, **kwargs)
        # thumbnails creation
        for res in tier.resolutions.all():
            thmb_size = (res.width, res.height)
            image = ImageObj.open(temp_img)
            # create a thumbnail + use antialiasing for a smoother thumbnail
            image.thumbnail(thmb_size, ImageObj.ANTIALIAS)
            img_io = BytesIO()
            image.save(img_io, format='JPEG', quality=100)

            filename = Path(str(temp_img)).name
            img_content = ContentFile(img_io.getvalue(), filename)

            obj = Thumbnail(org_img=self, thmb=img_content)
            obj.save()

@receiver(post_delete, sender=Image)
def image_delete(sender, instance, **kwargs):
    """Post_delete image file deletion signal for Image."""
    instance.img.delete(False)


def user_thmb_path(instance, filename):
    """Dynamic save path for thumbnail in Thumbnail model."""
    path = Path(f"uploads/{instance.org_img.user.id}/thmb/{filename}")
    return path


class Thumbnail(models.Model):
    """
    Thumbnail model.
    Holds original uploaded img relationship and thumbnail file itself.
    """
    org_img = models.ForeignKey(Image, on_delete=models.CASCADE)
    thmb = models.ImageField(upload_to=user_thmb_path)

@receiver(post_delete, sender=Thumbnail)
def image_delete(sender, instance, **kwargs):
    """Post_delete image file deletion signal for Thumbnail."""
    instance.thmb.delete(False)
