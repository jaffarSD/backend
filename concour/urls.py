from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework import viewsets, permissions
from .serializers import *
from .models import *
from .views import ChallengeViewSet, TeamViewSet, SubmissionViewSet, LeaderboardViewSet,register_user,MeView

router = DefaultRouter()
router.register(r'challenges', ChallengeViewSet, basename='challenge')
router.register(r'teams', TeamViewSet, basename='team')
router.register(r'submissions', SubmissionViewSet, basename='submission')
router.register(r'leaderboard', LeaderboardViewSet, basename='leaderboard')

urlpatterns = [
    path('', include(router.urls)),
    path('register/', register_user, name='register'), 
    path("me/", MeView.as_view(), name="me"),
]