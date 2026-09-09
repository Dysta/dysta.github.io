# dysta.github.io

Accueil Hugo alimenté par l’API GraphQL de GitHub : profil public, projets
épinglés et calendrier de contributions sur les 12 derniers mois. L’index
reprend la présentation du modèle minimal de CheckMyGit : profil centré,
statistiques, technologies et six projets triables. Les étoiles sont
additionnées sur tous les dépôts publics du compte ; les technologies
sont les huit langages principaux les plus fréquents par nombre de dépôts, hors forks.
Les contributions open source regroupent les commits et pull requests ouvertes
sur les dépôts publics externes des douze derniers mois (jusqu’à 100 dépôts
par type de contribution renvoyés par GitHub). Le blog reste accessible par le menu.
GitHub Actions synchronise ces données à chaque build et tous les jours à
05:17 UTC. Le jeton automatique `GITHUB_TOKEN` reste dans le workflow.
Si l’API échoue, le déploiement s’arrête et le site publié reste intact.

Pour prévisualiser avec les données GitHub, définir `GITHUB_TOKEN` dans
l’environnement (jeton autorisé à lire les données publiques), puis lancer :

```sh
python3 scripts/fetch-github.py
hugo server
```

Sans synchronisation, `hugo server` affiche le profil de secours.
Le fichier généré `data/github.json` n’est pas versionné.

L’accueil personnalisé se trouve dans `themes/PaperMod/layouts/index.html`.
Il réutilise les cartes, boutons, métadonnées et variables CSS de PaperMod.
Les styles spécifiques (grilles, badges et calendrier) se trouvent dans
`themes/PaperMod/assets/css/extended/github-home.css`, intégré automatiquement
au CSS du thème par Hugo.
