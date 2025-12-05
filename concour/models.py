from django.db import models
from django.contrib.auth.models import User
from django.core.validators import URLValidator, MinValueValidator, MaxValueValidator
from django.utils import timezone
import random
class Challenge(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    max_score = models.IntegerField(default=100, validators=[MinValueValidator(0)])
    points_per_submission = models.IntegerField(default=25, validators=[MinValueValidator(1)])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Team(models.Model):
    name = models.CharField(max_length=100, unique=True)
    leader = models.ForeignKey(User, on_delete=models.CASCADE, related_name='led_teams')
    members = models.ManyToManyField(User, related_name='teams', blank=True)
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE, related_name='teams')
    github_repo_url = models.URLField(validators=[URLValidator()])
    score = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    rank = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['rank', '-score', 'created_at']
        unique_together = ['name', 'challenge']

    def __str__(self):
        return f"{self.name} - {self.challenge.title}"

    def save(self, *args, **kwargs):
        if not self.pk and self.rank is None:
            # Assigner un rang aléatoire initial
            existing_ranks = list(Team.objects.filter(
                challenge=self.challenge
            ).values_list('rank', flat=True))
            
            if existing_ranks:
                max_rank = max(existing_ranks)
                available_ranks = list(range(1, max_rank + 2))
                for rank in existing_ranks:
                    if rank in available_ranks:
                        available_ranks.remove(rank)
                self.rank = random.choice(available_ranks) if available_ranks else max_rank + 1
            else:
                self.rank = 1
        
        super().save(*args, **kwargs)


class Submission(models.Model):
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('approved', 'Approuvé'),
        ('rejected', 'Rejeté'),
    ]

    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='submissions')
    submitted_by = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    points_awarded = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    
    # Données GitHub capturées
    github_data = models.JSONField(default=dict, blank=True)
    repo_updated_at = models.DateTimeField(null=True, blank=True)
    repo_pushed_at = models.DateTimeField(null=True, blank=True)
    stars_count = models.IntegerField(default=0)
    forks_count = models.IntegerField(default=0)
    
    verification_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Submission {self.id} - {self.team.name} - {self.status}"

