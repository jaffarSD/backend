Create a virtual environment:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver

-----
Comment fonctionne une participation ?:

L’équipe s’inscrit via un endpoint sécurisé.
Elle soumet sa solution (par exemple une URL GitHub ou un fichier).
Le backend analyse automatiquement la soumission, attribue un score selon les règles définies, et met immédiatement à jour le leaderboard.
Le classement est donc instantané, juste et transparent.

 3. Fonctionnalité Innovante : Vérification Automatique du Dépôt GitHub
    
L’une des fonctionnalités majeures qui distingue ce projet est la vérification automatique du repository GitHub de chaque équipe.
Cette vérification permet d’éviter qu’une équipe obtienne une position sur le podium sans avoir réellement poussé une nouvelle version de son code.

 Comment cela fonctionne techniquement ?
À chaque soumission :
L’API reçoit le lien du dépôt GitHub déclaré par l’équipe.
Elle vérifie automatiquement :
la dernière date de commit,
les modifications apportées,
la cohérence entre la soumission et le code réellement présent dans le dépôt.
Si aucun changement réel n’est détecté, alors :
la soumission n’est pas validée,
aucune mise à jour du podium n’est faite,
l'équipe ne peut pas “forcer” un meilleur classement avec une fausse soumission.
Objectif : empêcher la triche de façon 100% automatique
Grâce à cette vérification, le système garantit que :
Chaque position au podium est méritée.
Les équipes doivent réellement pousser du nouveau code pour être reclassées.
Le jury peut se fier au classement sans intervention humaine.
C'est une fonctionnalité rare, moderne et hautement valorisante, spécialement pensée pour les compétitions où le respect des règles et l’authenticité des contributions sont essentiels.
