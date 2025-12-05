from django.contrib import admin
from .models import *
@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = ['title', 'max_score', 'points_per_submission', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'description']
    ordering = ['-created_at']


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'leader', 'challenge', 'score', 'rank', 'created_at']
    list_filter = ['challenge', 'created_at']
    search_fields = ['name', 'leader__username']
    ordering = ['rank', '-score']
    readonly_fields = ['score', 'rank', 'created_at', 'updated_at']


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ['id', 'team', 'submitted_by', 'status', 'points_awarded', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['team__name', 'submitted_by__username']
    ordering = ['-created_at']
    readonly_fields = ['github_data', 'created_at', 'verified_at']


# jaffar
# 12345678