"""Views for Image."""
import datetime
from pathlib import Path
from PIL import Image as ImageObj
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from image.models import Image
from image.serializers import ImageSerializer, GenerateLinkSerializer
from account.models import User
from utils import crypto, permissions


class ListCreateImageView(generics.ListCreateAPIView):
    """
    List or create Images with thumbnails with accordance to AccountTier specification.
    Basic Auth.
    """
    serializer_class = ImageSerializer
    permission_classes = [IsAuthenticated, permissions.IsAdminOrOwner]

    def get_queryset(self):
        return Image.objects.filter(user=self.kwargs['user_id'])

    def perform_create(self, serializer):
        return serializer.save(user=User.objects.get(id=self.kwargs['user_id']))


class GetImageView(generics.RetrieveAPIView):
    """
    Get specified Image.
    Basic Auth.
    """
    serializer_class = ImageSerializer
    permission_classes = [IsAuthenticated, permissions.IsAdminOrOwner]

    def get_queryset(self):
        return Image.objects.filter(user=self.kwargs['user_id'])


class GenerateLinkView(generics.GenericAPIView):
    """
    Generate temp link to get binary image.
    Basic Auth.
    Only users with can_generate_links=True in AccountTier can generate these links.
    """
    serializer_class = GenerateLinkSerializer
    permission_classes = [IsAuthenticated, permissions.IsAdminOrOwner, permissions.TierHaveLinks]
    
    def post(self, request, user_id, pk):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        fetched_img = get_object_or_404(Image, pk=pk)
        if fetched_img.img is None:
            return Response(data={"msg": "No original image to generate binary"}, status=status.HTTP_404_NOT_FOUND)
        # convert img to binary
        # not sure if I understood that task correctly
        image = ImageObj.open(fetched_img.img)
        bands = image.getbands()
        # don't convert if it's already in correct band
        if len(bands) != 1:
            image = image.convert('1')
        # save the converted img to temp folder
        # custom manage.py command and/or cron job to delete them after some time?
        path = Path(f"{settings.MEDIA_ROOT}/uploads/{user_id}/temp")
        path.mkdir(parents=True, exist_ok=True)
        image.save(path / f"{pk}.png")

        # define deadline for link
        ttl = timezone.now() + datetime.timedelta(seconds=serializer.validated_data['ttl'])
        # could be done with anything that creates symmetric key token with customizable payload
        encrypted = crypto.encrypt_data({"ttl": ttl})

        current_site = get_current_site(request).domain
        relative_link = reverse(
            'tmp-image',
            kwargs={"user_id": user_id, "pk": pk, "token": encrypted.decode('utf-8')}
        )
        absurl = 'http://' + current_site + relative_link

        return Response(data={"link": absurl}, status=status.HTTP_200_OK)


class GetImageTmpLinkView(generics.GenericAPIView):
    """
    Get binary image with auth token.
    Token can expire.
    No auth - anyone with a token can access.
    """
    authentication_classes = []

    def get(self, request, user_id, pk, token):
        payload = crypto.decrypt_data(token)
        
        # check if token did not expire
        if timezone.now() > payload['ttl']:
            return Response(data={"msg": "Expired"}, status=status.HTTP_403_FORBIDDEN)
        # fetch img
        path_check = Path(f"{settings.MEDIA_ROOT}/uploads/{user_id}/temp/{pk}.png")
        if not path_check.exists():
            return Response(status=status.HTTP_404_NOT_FOUND)
        path_resource = Path(f"{settings.MEDIA_URL}/uploads/{user_id}/temp/{pk}.png")
        current_site = get_current_site(request).domain
        absurl = 'http://' + current_site + str(path_resource)
        
        return Response(data={"img": absurl}, status=status.HTTP_200_OK)
