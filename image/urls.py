from django.urls import path

from image.views import ListCreateImageView, GetImageView, GenerateLinkView, GetImageTmpLinkView

urlpatterns = [
    path('', ListCreateImageView.as_view(), name='list-create-image'),
    path('<int:pk>/', GetImageView.as_view(), name='get-image'),
    path('<int:pk>/generate_link', GenerateLinkView.as_view(), name='generate-link'),
    path('<int:pk>/tmp/<str:token>', GetImageTmpLinkView.as_view(), name='tmp-image'),
]
