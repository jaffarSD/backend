from datetime import datetime
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.db.models import Q, Count
import re
from .models import Challenge, Team, Submission
import requests
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from rest_framework.decorators import api_view, permission_classes
from .serializers import ChallengeSerializer,TeamSerializer,SubmissionSerializer,LeaderboardSerializer
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from django.utils import timezone
import re
import requests
from django.db import transaction
from rest_framework import serializers, viewsets, permissions


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
        })


class IsLeaderOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.leader == request.user
ChallengeSerializer

@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """
    Endpoint pour créer un nouvel utilisateur
    """
    username = request.data.get('username')
    password = request.data.get('password')
    email = request.data.get('email', '')
    first_name = request.data.get('first_name', '')
    last_name = request.data.get('last_name', '')
    
    # Validation
    if not username or not password:
        return Response(
            {'error': 'Username and password are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Vérifier si l'utilisateur existe déjà
    if User.objects.filter(username=username).exists():
        return Response(
            {'error': 'Username already exists'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Créer l'utilisateur
    try:
        user = User.objects.create(
            username=username,
            password=make_password(password),
            email=email,
            first_name=first_name,
            last_name=last_name
        )
        
        return Response({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'message': 'User created successfully'
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class ChallengeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Challenge.objects.filter(is_active=True)
    serializer_class = ChallengeSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class TeamViewSet(viewsets.ModelViewSet):
    serializer_class = TeamSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsLeaderOrReadOnly]
    # permission_classes = [IsAuthenticated, IsLeaderOrReadOnly]


    def get_queryset(self):
        queryset = Team.objects.all().select_related('leader', 'challenge')
        
        challenge_id = self.request.query_params.get('challenge')
        if challenge_id:
            queryset = queryset.filter(challenge_id=challenge_id)
        
        return queryset

    def perform_create(self, serializer):
        serializer.save(leader=self.request.user)



class SubmissionViewSet(viewsets.ModelViewSet):
    serializer_class = SubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Submission.objects.all().select_related('team', 'submitted_by', 'team__challenge')
        
        team_id = self.request.query_params.get('team', None)
        if team_id:
            queryset = queryset.filter(team_id=team_id)
        
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset

    def perform_create(self, serializer):
        team = serializer.validated_data['team']
        print("✅ Start perform_create")  # Débu

        # Vérifier que l'utilisateur est le leader ou membre de l'équipe
        if self.request.user != team.leader and self.request.user not in team.members.all():
            print("❌ Utilisateur non autorisé")
            raise serializers.ValidationError(
                 "Vous devez être le leader ou membre de l'équipe pour soumettre"
            )
        print("✅ Utilisateur autorisé")

        # Extraire le nom du repo depuis l'URL
        repo_url = team.github_repo_url.strip().rstrip('/')
        print(f"🔗 URL GitHub de l'équipe : {repo_url}")

        match = re.search(r'github\.com/([^/]+)/([^/]+)', repo_url)
        if not match:
            print("❌ URL GitHub invalide")
            raise serializers.ValidationError("URL GitHub invalide")

        owner, repo = match.groups()
        repo = repo.replace('.git', '')
        print(f"📝 Owner: {owner}, Repo: {repo}")

        # Construire l'URL de l'API GitHub
        github_api_url = f'https://api.github.com/repos/{owner}/{repo}'
        print(f"🌐 URL API GitHub : {github_api_url}")


        try:
            response = requests.get(github_api_url, timeout=15)
            print(f"📡 Statut réponse API : {response.status_code}")

            if response.status_code != 200:
                print(f"📡 Statut réponse API : {response.status_code}")
                raise serializers.ValidationError(
                    f"Erreur lors de la récupération des données GitHub: {response.status_code}"
                )

            github_data = response.json()
            print("✅ Données GitHub récupérées avec succès")

            # Vérifier si le repo est privé
            if github_data.get('private', False):
                print("❌ Le dépôt est privé")
                raise serializers.ValidationError("Le dépôt GitHub doit être public")

            # Extraire les dates
            repo_updated_at = github_data.get('updated_at')
            repo_pushed_at = github_data.get('pushed_at')
            print(f"🕒 Updated at: {repo_updated_at}, Pushed at: {repo_pushed_at}")

            # Vérifier s'il y a eu des changements
            last_submission = team.submissions.filter(status='approved').order_by('-created_at').first()
            has_changes = True
            if last_submission and last_submission.repo_pushed_at:
                last_pushed = last_submission.repo_pushed_at
                current_pushed = datetime.fromisoformat(repo_pushed_at.replace('Z', '+00:00'))
                if current_pushed <= last_pushed:
                    has_changes = False

            if not has_changes:
                print("❌ Aucun changement détecté depuis la dernière soumission")
                raise serializers.ValidationError(
                    "Aucun changement détecté dans le dépôt GitHub depuis la dernière soumission"
                )

            # Créer la soumission
            submission = serializer.save(
                submitted_by=self.request.user,
                status='approved',
                points_awarded=team.challenge.points_per_submission,
                github_data={
                    'full_name': github_data.get('full_name'),
                    'created_at': github_data.get('created_at'),
                    'updated_at': github_data.get('updated_at'),
                    'pushed_at': github_data.get('pushed_at'),
                    'stargazers_count': github_data.get('stargazers_count', 0),
                    'forks_count': github_data.get('forks_count', 0),
                    'html_url': github_data.get('html_url'),
                },
                repo_updated_at=datetime.fromisoformat(repo_updated_at.replace('Z', '+00:00')),
                repo_pushed_at=datetime.fromisoformat(repo_pushed_at.replace('Z', '+00:00')),
                stars_count=github_data.get('stargazers_count', 0),
                forks_count=github_data.get('forks_count', 0),
                verified_at=timezone.now(),
                verification_notes="Soumission approuvée automatiquement - Changements détectés"
            )
            print("✅ Soumission créée avec succès")

            # Mettre à jour le score de l'équipe
            with transaction.atomic():
                team.score = min(
                    team.score + team.challenge.points_per_submission,
                    team.challenge.max_score
                )
                team.save()
                self._update_rankings(team)
            print("✅ Score et rangs mis à jour")

        except requests.RequestException as e:
            print(f"❌ Erreur connexion GitHub : {str(e)}")
            raise serializers.ValidationError(f"Erreur de connexion à GitHub: {str(e)}")

    def _update_rankings(self, team):
        """Mettre à jour les rangs des équipes du même challenge"""
        # Récupérer toutes les équipes du challenge avec leurs scores
        teams = Team.objects.filter(challenge=team.challenge).order_by(
            '-score', 'created_at'
        )
        
        # Réattribuer les rangs
        for index, t in enumerate(teams, start=1):
            if t.rank != index:
                t.rank = index
                t.save(update_fields=['rank'])


class LeaderboardViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = LeaderboardSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = Team.objects.all().select_related('leader', 'challenge')
        
        challenge_id = self.request.query_params.get('challenge', None)
        if challenge_id:
            queryset = queryset.filter(challenge_id=challenge_id)
        
        return queryset.order_by('rank', '-score', 'created_at')

    @action(detail=False, methods=['get'])
    def top_teams(self, request):
        """Obtenir le top 10 des équipes"""
        limit = int(request.query_params.get('limit', 10))
        challenge_id = request.query_params.get('challenge', None)
        
        queryset = self.get_queryset()
        if challenge_id:
            queryset = queryset.filter(challenge_id=challenge_id)
        
        top_teams = queryset[:limit]
        serializer = self.get_serializer(top_teams, many=True)
        
        return Response(serializer.data)

