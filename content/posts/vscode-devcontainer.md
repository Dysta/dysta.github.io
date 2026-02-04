---
title:  "Exploiter le potentiel des devcontainers sur vscode"
date:   2025-04-05T12:00:00+01:00
categories: "dev"
draft: true
---
Arriver sur un nouveau projet implique presque toujours la même étape critique : 
le setup de l’environnement de développement.

En théorie, Docker est censé régler le problème.
En pratique, on se retrouve souvent avec :
- plusieurs versions de Node/Python à installer localement,
- des services qui tournent en double sur la machine,
- des `.env` non versionnés et différents selon les devs,
- et un debug à base de `print()` dans un monolithe trop gros.

Résultat : onboarding lent, environnements incohérents, et le classique “chez moi ça marche”.

## Le problème avec Docker Compose en local

Docker Compose règle le problème des dépendances applicatives, mais **pas celui de l’environnement de développement**.

Dans la majorité des projets :
- le code tourne dans Docker,
- mais l’éditeur, le debugger, le linter et les extensions tournent sur l’OS hôte,
- ce qui impose quand même d’installer Node, Python, etc. localement.

On déplace le problème, on ne le supprime pas.

## Dev Containers : comment ça fonctionne réellement

Un Dev Container est une couche au-dessus de Docker :
- VS Code se connecte à un conteneur
- l’éditeur, le terminal, le debugger et les extensions s’exécutent **dans ce conteneur**
- le système hôte ne sert qu’à lancer Docker

Concrètement :
- ton `node`, ton `python`, ton `psql` ne sont plus ceux de ton OS
- ton `PATH` est celui du conteneur
- ton code est monté en volume

```json
{
  "name": "api-backend",
  "dockerFile": "Dockerfile",
  "context": "..",
  "features": {
    "ghcr.io/devcontainers/features/docker-in-docker:2": {},
    "ghcr.io/devcontainers/features/node:1": {
      "version": "20"
    }
  },
  "postCreateCommand": "npm install",
  "forwardPorts": [3000, 5432],
  "customizations": {
    "vscode": {
      "extensions": [
        "dbaeumer.vscode-eslint",
        "ms-python.python"
      ]
    }
  }
}
```

## Quand Dev Containers sont réellement pertinents

Les Dev Containers sont particulièrement adaptés si :
- le projet a plusieurs langages ou runtimes,
- l’équipe est distribuée,
- l’onboarding doit être rapide et reproductible,
- les environnements locaux sont sources de bugs.

En revanche, pour :
- un projet très léger,
- un POC court,
- ou une équipe très senior avec des setups maîtrisés,

le gain peut être marginal.
