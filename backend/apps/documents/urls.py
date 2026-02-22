# """Document URL routes."""
# from django.urls import path
# from . import views

# urlpatterns = [
#     path('presigned/', views.get_presigned_upload_url),
#     path('confirm/', views.confirm_upload),
#     path('', views.list_documents),
# ]

from django.urls import path
from .views import ResumeUploadView

urlpatterns = [
    path("", ResumeUploadView.as_view(), name="resume-upload"),
]
