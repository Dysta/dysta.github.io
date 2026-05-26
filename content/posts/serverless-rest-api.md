---
title:  "Une API REST statique gratuitement"
date:   2025-03-30T12:00:00+01:00
categories: "dev"
---
# Une API REST statique : définition, cas d’usage et mise en place  

Aujourd’hui, je vais vous présenter une façon simple et gratuite de concevoir une API REST statique, hébergée via un simple repository GitHub.

___

## Qu'est-ce qu'une API REST statique ?  

Je définis une API REST statique comme une API qui respecte trois principes fondamentaux :  

- **Serverless** : elle ne dépend d’aucun cloud provider (AWS, GCP, Azure, etc..).  
- **Stateless** : elle ne conserve aucun état entre les requêtes.  
- **Scalable** : elle peut être mise à l’échelle facilement, sans contrainte d’infrastructure.  

En pratique, il s'agit d'une API qui expose des données sous forme de fichiers JSON statiques, accessibles via des requêtes HTTP, sans traitement côté serveur. Autrement dit, elle est **entièrement en lecture seule**.  

## Un cas concret : l’open data de l’Assemblée nationale  

Mon objectif était de rendre accessibles des informations sur les députés : leurs votes, leur présence et les amendements adoptés ou non. Le tout dans un format réutilisable pour divers projets : bots, sites web, applications mobiles…  

### Récupération des données  

Le format JSON étant le plus adapté, il était évident que mes données seraient sauvegardées sous cette forme. Pour les obtenir, j'ai écrit un script en **Python**, utilisant la bibliothèque [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) pour scraper et parser le site de l’Assemblée nationale.  

### Rendre les données accessibles  

JSON étant omniprésent dans le développement web, une **API REST** était la solution la plus naturelle pour exposer ces données. Mais héberger une API implique généralement :  

- Un **serveur backend** pour traiter les requêtes,  
- Un **bucket de stockage** pour les données,  
- Une **infrastructure** à maintenir et sécuriser.  

Tout cela a un **coût** en temps et en argent… alors j’ai cherché une solution **gratuite et sans serveur**.  

## Solution mise en place  

L'idée m'est venue en explorant mon repository GitHub : son arborescence ressemblait étrangement à une API ! Et GitHub propose une fonctionnalité clé : le bouton **"View raw"**, qui permet d’accéder directement au contenu brut des fichiers via une URL.  

J’ai donc remplacé **le backend et le bucket** par un simple repository GitHub en me reposant sur ce principe.  

### Architecture finale  

1. **Scraping et parsing** : un script récupère les données publiques de l’Assemblée nationale.  
2. **Génération de fichiers JSON** : les données sont transformées et classées dans les bons dossiers.  
3. **Hébergement sur GitHub** : les fichiers sont accessibles via un lien brut.  

Cette approche me permet de fournir des données **gratuitement**, sans aucune complexité technique ni infrastructure coûteuse.  

## Pourquoi ce choix ?  

Ce modèle présente plusieurs **avantages majeurs** :  

- **Simplicité** : pas de backend, pas de base de données, pas de gestion de serveur.  
- **Scalabilité automatique** : GitHub gère la distribution des fichiers.  
- **Coût nul** : aucun frais d’hébergement ou d’infrastructure.  
- **Disponibilité** : GitHub garantit une bonne disponibilité des fichiers.  

## Automatisation des mises à jour  

### Le problème  

À ce stade, je devais encore **mettre à jour les fichiers manuellement** :  

- **Lancer** le script sur mon ordinateur,  
- **Pusher** les nouvelles données sur GitHub,  
- **Répéter** tous les X jours ou heures.  

Une tâche répétitive… et donc **automatisable**.  

### La solution : GitHub Actions  

Heureusement pour moi, GitHub propose un système d’automatisation similaire aux tâches **Cron** : lorsqu'on crée un workflow **GitHub Actions**, nous avons la possibilité de le déclencher automatiquement via un [schedule](https://docs.github.com/en/actions/writing-workflows/choosing-when-your-workflow-runs/events-that-trigger-workflows#schedule).  

J’ai donc mis en place un workflow qui :  

1. **Exécute mon script** de scraping toutes les 6 heures,  
2. **Met à jour les fichiers JSON**,  
3. **Commit automatiquement** les nouvelles données sur le repository.  

Résultat : plus besoin d’intervenir manuellement, mes données sont mises à jour **en continu** !  

## Amélioration de l’accessibilité avec GitHub Pages  

Quand on accède aux données via le lien brut, les URLs générées par **raw.githubusercontent.com** sont longues et peu élégantes. Encore une fois, GitHub nous sauve la mise avec son service gratuit : **GitHub Pages**.

En activant GitHub Pages sur le repository, mon URL d'API passe de :  

```
https://raw.githubusercontent.com/Dysta/ANDataParser/refs/heads/main/
```

à  

```
https://dysta.github.io/ANDataParser/
```

Beaucoup plus propre et facile à retenir !  


## Les limites d’une API REST statique  
Dans ce ticket, je vous ai présenté une façon de mettre à disposition ses données via une API REST statique.  
Cependant, il est important de garder à l'esprit que cette approche, bien que très efficace, **n’est pas adaptée à tous les cas d’usage**.  

- **Pas de données en temps réel** : les mises à jour sont périodiques et dépendent de la réussite de votre workflow.  
- **Aucune requête dynamique** : impossible de filtrer ou trier les données à la volée, tout se fait côté client. La taille des JSONs transmis peut vite devenir très importante.  
- **Dépendance à GitHub** : une modification des règles d’hébergement pourrait poser problème.  
- **Peu de personnalisation** : on ne contrôle pas la vitesse, le cache ou les limitations de requêtes.  

---

## Conclusion  

Une API REST statique est une solution idéale pour :  

- Exposer des données **publiques** et **en lecture seule**.  
- Éviter toute gestion **d’infrastructure**.  
- **Réduire les coûts** au maximum : hébergement gratuit, peu de maintenance.  
- Rendre des données accessibles en **quelques minutes**.  

Si votre projet ne nécessite **ni requêtes dynamiques ni mises à jour en temps réel**, c'est une solution simple, scalable et efficace.  