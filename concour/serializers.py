from rest_framework import serializers
from django.contrib.auth.models import User
import requests
from datetime import datetime
from django.db.models import Max
from .models import *

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class ChallengeSerializer(serializers.ModelSerializer):
    teams_count = serializers.SerializerMethodField()

    class Meta:
        model = Challenge
        fields = ['id', 'title', 'description', 'max_score', 'points_per_submission', 
                  'is_active', 'teams_count', 'created_at', 'updated_at']

    def get_teams_count(self, obj):
        return obj.teams.count()


class TeamSerializer(serializers.ModelSerializer):
    leader = UserSerializer(read_only=True)
    leader_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), 
        source='leader', 
        write_only=True
    )
    challenge_title = serializers.CharField(source='challenge.title', read_only=True)
    submissions_count = serializers.SerializerMethodField()
    latest_submission = serializers.SerializerMethodField()

    class Meta:
        model = Team
        fields = ['id', 'name', 'leader', 'leader_id', 'challenge', 'challenge_title',
                  'github_repo_url', 'score', 'rank', 'submissions_count', 
                  'latest_submission', 'created_at', 'updated_at']
        read_only_fields = ['score', 'rank']

    def get_submissions_count(self, obj):
        return obj.submissions.filter(status='approved').count()

    def get_latest_submission(self, obj):
        latest = obj.submissions.order_by('-created_at').first()
        if latest:
            return {
                'id': latest.id,
                'status': latest.status,
                'created_at': latest.created_at
            }
        return None

    def validate_github_repo_url(self, value):
        if not ('github.com' in value):
            raise serializers.ValidationError("L'URL doit être un dépôt GitHub valide")
        return value


class SubmissionSerializer(serializers.ModelSerializer):
    team_name = serializers.CharField(source='team.name', read_only=True)
    submitted_by_username = serializers.CharField(source='submitted_by.username', read_only=True)
    challenge_title = serializers.CharField(source='team.challenge.title', read_only=True)

    class Meta:
        model = Submission
        fields = ['id', 'team', 'team_name', 'submitted_by', 'submitted_by_username',
                  'challenge_title', 'status', 'points_awarded', 'github_data',
                  'repo_updated_at', 'repo_pushed_at', 'stars_count', 'forks_count',
                  'verification_notes', 'created_at', 'verified_at']
        read_only_fields = ['status', 'points_awarded', 'github_data', 'submitted_by',
                            'repo_updated_at', 'repo_pushed_at', 'stars_count',
                            'forks_count', 'verified_at']


class LeaderboardSerializer(serializers.ModelSerializer):
    leader = UserSerializer(read_only=True)
    challenge_title = serializers.CharField(source='challenge.title', read_only=True)
    submissions_count = serializers.SerializerMethodField()
    progress_percentage = serializers.SerializerMethodField()

    class Meta:
        model = Team
        fields = ['id', 'name', 'leader', 'challenge_title', 'score', 'rank',
                  'submissions_count', 'progress_percentage', 'github_repo_url', 
                  'created_at', 'updated_at']

    def get_submissions_count(self, obj):
        return obj.submissions.filter(status='approved').count()

    def get_progress_percentage(self, obj):
        if obj.challenge.max_score > 0:
            return min(100, (obj.score / obj.challenge.max_score) * 100)
        return 0
