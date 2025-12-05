from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Submission, Team

@receiver(post_save, sender=Submission)
def update_team_score_on_approval(sender, instance, created, **kwargs):
    """Signal pour mettre à jour le score de l'équipe lors de l'approbation"""
    if instance.status == 'approved' and instance.points_awarded > 0:
        # Le score est déjà mis à jour dans la vue, mais on peut ajouter
        # d'autres logiques ici (notifications, webhooks, etc.)
        pass