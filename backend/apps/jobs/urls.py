"""Job URL routes."""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.list_jobs),
    path('matched/', views.matched_jobs),
]
