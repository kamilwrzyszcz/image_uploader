from rest_framework import serializers
from django.conf import settings
from django.core.files.images import get_image_dimensions
from django.core.exceptions import ValidationError 

from image.models import Image, Thumbnail


class ThumbnailSerializer(serializers.ModelSerializer):
    """Thumbnail serializer for nested relation with Image"""

    class Meta:
        model = Thumbnail
        fields = ('thmb',)


class ImageSerializer(serializers.ModelSerializer):
    """Image serializer"""
    thumbnails = ThumbnailSerializer(source='thumbnail_set', many=True, read_only=True)

    class Meta:
        model = Image
        fields = ('id', 'img', 'thumbnails')

    def validate_img(self, img):
        """
        Custom img field validation.
        Validate dimensions and file size.
        """
        image_width, image_height = get_image_dimensions(img) 
        if image_width >= settings.MAX_WIDTH or image_height >= settings.MAX_HEIGHT: 
            raise ValidationError(f'Image size must be max {settings.MAX_WIDTH}x{settings.MAX_HEIGHT}')
        if img.size > settings.MAX_SIZE_MEGABYTES*1024*1024:
                raise ValidationError("Image file too large")

        return img


class GenerateLinkSerializer(serializers.Serializer):
    """GenerateLink serializer."""
    ttl = serializers.IntegerField(min_value=300, max_value=30000)
