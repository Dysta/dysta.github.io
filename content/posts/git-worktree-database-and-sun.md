---
title: "Git + JSON + worktree = petite base de données partagée"
date: 2026-05-26T12:00:00+01:00
categories: "dev"
---

# Du stockage simple, sans frais et sans maintenance
Cela fait un an depuis le dernier post où je vous présentais un petit hack GitHub pour avoir une API sans payer. Je vous avais fièrement présenté mon idée et les retours avaient été plutôt positifs. Devinez quoi ? Aujourd'hui, on remet ça !

___

## Contexte
Dans mon travail actuel, nous écrivons des documents référencés. Une référence est définie par un code unique issu d'une combinaison de trois éléments :
- le type de projet, souvent un trigramme ;
- le type de document, souvent le nom du projet utilisé en interne auquel on rattache le document en cours de rédaction ;
- un identifiant unique, choisi par l'auteur du document.

Lorsqu'on calcule la référence, on prend ces trois éléments que l'on relie avec un `-`. Cela peut donner par exemple `POP-DOC1234-TI99902`.
Ces références sont partagées dans toute l'entreprise par l'ensemble des collaborateurs, car elles permettent d'identifier les documents créés et signés.

Avant mon arrivée, aucun outil ne permettait de vérifier les références autrement que localement. La seule façon de faire était de générer l'ensemble des documents et c'était pendant cette génération qu'était vérifiée l'absence de duplication. Autant vous dire que personne ne prenait le temps de faire ça sur son PC. Sinon, une pipeline GitHub s'en chargeait. Mais bien souvent, la pipeline était lancée en fin de rédaction et révélait donc le problème trop tard.

Dernier point, et pas des moindres : avec le temps, différents projets se sont constitués au sein de l'entreprise. Le système de vérification des doublons n'était pas prévu pour aller chercher dans les autres projets. Il était donc possible que des références soient dupliquées entre plusieurs projets, ce que nous voulions éviter.

J'ai donc été missionné pour trouver une solution.

## Les bases
Pour répondre à ce besoin, j'ai eu l'idée d'utiliser une base de données alimentée pendant l'exécution d'un pre-commit hook.

Pourquoi un pre-commit hook ? Parce que le lancement des hooks était déjà paramétré chez l'ensemble des collaborateurs. Je n'avais donc rien à faire hormis ajouter le mien. De plus, cela permettait de garantir que notre script serait lancé correctement, toujours au même moment.

Pour le stockage, l'idée de paramétrer et d'héberger une base de données dans le cloud ne me plaisait pas. Le ratio entre maintenir à jour plusieurs outils décentralisés pour simplement stocker des chaînes de caractères me paraissait complètement déséquilibré.
Puis, d'expérience, je savais que ce genre d'outil finit souvent oublié jusqu'au jour où il cesse de fonctionner. On se rend alors compte qu'on a ignoré des warnings involontairement pendant des mois et qu'il faut tout mettre à jour en urgence, bloquant au passage l'ensemble des collaborateurs pendant plusieurs heures.

Je voulais une solution simple, évolutive et demandant très peu, voire aucune, maintenance humaine.

Dans la continuité de mon ancien projet d'API REST sur GitHub, j'ai eu l'idée d'utiliser une branche dédiée sur le dépôt GitHub pour stocker nos données. En plus, tout le monde pouvait consulter cette branche et vérifier les références avec un simple Ctrl + F. Et bonus supplémentaire : grâce à mon ancien projet d'API REST sur GitHub, je savais qu'une lecture des références pouvait facilement être mise en place via une simple requête HTTPS depuis un script ou un frontend prévu pour l'occasion.

Pour la mise en place des bases, c'était plutôt simple :
- configurer une branche orpheline du projet (sans historique) ;
- y stocker un unique fichier JSON ;
- récupérer rapidement cette branche légère ;
- ajouter les références ;
- pousser les modifications sur la branche.

Le tout de manière totalement transparente pour l'utilisateur.

Pour le format du JSON, rien de compliqué :
- en clé : notre référence ;
- en valeur : tout ce qui peut nous servir maintenant ou plus tard.

Un peu comme une petite base de données NoSQL.

Après une rapide présentation de l'idée à mon collègue, il a immédiatement adoré et validé le concept. Me voilà donc parti pour mettre en place mon pre-commit hook, ma branche dédiée et mon fichier JSON.

# De l'idée à la pratique
## Mise en place
Pour commencer, il fallait créer notre branche orpheline qui servirait de base de données. Dans mon cas, j'ai appliqué la convention `registry/*` afin de pouvoir mettre en place des règles de protection sur GitHub et protéger ma branche des pull requests ou des merges accidentels dans une autre branche. En plus, cela me permettait de l'identifier rapidement dans la masse de branches non supprimées après une pull request approuvée. (Supprimez vos branches, s'il vous plaît.)

Pour le setup, cela donne :
```bash
git checkout --orphan registry/references # création de la branche sans historique
git rm -rf . # suppression de l'intégralité des fichiers
echo "[]" >> references.json # liste vide servant de stockage
git add references.json
git commit -m "first commit"
git push
```

Pas plus compliqué que ça. On a initialisé une branche sur notre dépôt qui ne possède aucun historique et ne contient qu'un unique fichier.

## Utilisation dans notre pre-commit
Au vu de la simplicité de notre branche, elle est extrêmement rapide à récupérer.

Cependant, cette stratégie pose un nouveau problème : il est compliqué de basculer dessus de manière traditionnelle avec un `checkout`, car la différence d'historique et la quantité de modifications détectées rendent l'opération lente et peu stable pour un script lancé en arrière-plan sans intervention humaine.

## Les worktrees à la rescousse
Heureusement pour nous, Git possède un système de worktree. Pour faire simple, un worktree permet de partager le même `.git` dans plusieurs dossiers différents, ce qui permet d'avoir plusieurs branches simultanément sans devoir faire de checkout en permanence. Il suffit simplement de changer de worktree. Cela répond parfaitement à notre besoin.

Voici mon approche : créer un worktree, checkout la branche `registry`, effectuer les modifications, puis les pousser sur la branche distante, le tout en arrière-plan, sans que l'utilisateur s'en rende compte.

# Vous avez des problèmes ? J'ai des solutions.
Je vous épargne l'implémentation complète, mais de mon côté je l'ai réalisée en **Python**.

Voici le workflow adopté dans le script et exécuté à chaque pre-commit :
- vérifier que la branche `registry` existe en ligne ;
- récupérer la branche distante ;
- créer un dossier temporaire dans `/tmp` avec un nom aléatoire pour éviter les collisions ;
- créer un worktree dans ce dossier temporaire ;
- mettre à jour les données ;
- créer un commit avec le nouveau JSON ;
- pousser le commit sur la branche `registry` ;
- supprimer le worktree ;
- supprimer le dossier temporaire.

## 1ère itération
Pour la première itération de notre script, je suis allé au plus simple.
```bash
git fetch origin registry/references
git worktree add /tmp/... registry/references
# ... Manipulation de notre registre
git add references.json
git commit -m "Update references registry"
git push origin registry/references
git worktree remove --force /tmp/...
rm -rf /tmp/...
```

On configure le pre-commit, on déploie en production et : tout roule 🎉

Les premiers commits tombent, je vois le registre se remplir et je suis content : tout fonctionne. Avec ce workflow, aucune trace de notre passage. En plus, supprimer le worktree et le dossier temporaire évite les problèmes de synchronisation entre la branche locale et la branche distante.

Enfin… c'est ce que je croyais.

## 2ème itération
Un matin, on vient me voir et on me dit qu'il est impossible de commit car le pre-commit bloque. Je regarde ce qu'il se passe et, honnêtement, je ne comprends pas immédiatement le problème. Le souci vient du fait que le pre-commit ne peut plus pull la branche distante car la branche locale diverge.

Sur le moment, cela me semble impossible puisque je supprime toutes traces de mon passage, il ne devrait donc rien rester. Je commence donc mon investigation et finis par comprendre le scénario permettant de reproduire le bug. La divergence vient du fait que lors de la création du worktree, `HEAD` est copié localement via le checkout. Si quelqu'un ajoute une référence entre-temps, le `HEAD` distant change.

Mais comme la branche locale a été supprimée, Git ne sait plus quelle stratégie appliquer pour résoudre la divergence. Résultat : impossible de refaire un commit après en avoir déjà fait un. Je comprends alors que mon script ne fonctionne pas exactement comme je le pensais et qu'il reste malgré tout une trace locale de son passage.

Je continue mes recherches.

Après quelques dizaines de minutes, je découvre qu'il est possible de ne pas copier localement le `HEAD` et de se positionner directement sur le `HEAD` distant grâce à l'option `--detach` lors de la création du worktree.

Je mets donc à jour ma commande :
```bash
git worktree add --detach /tmp/... origin/registry/references
```

Je fais mes tests : tout fonctionne. Je publie le correctif et les utilisateurs peuvent à nouveau commit. Cette fois-ci, plus aucune trace locale de mon passage.

Mais malgré tout… quelque chose continue de me déranger dans mon script.

## 3ème itération
Les jours passent, aucun problème en vue. Le script fonctionne bien, les références s'ajoutent progressivement.
Les utilisateurs râlent parce qu'il devient impossible de commit un document sans référence… mais c'était justement l'objectif.

Pourtant, quelque chose dans mon code me dérange...

En regardant celui-ci, je réalise que la logique métier liée aux références est noyée dans tout le boilerplate Git nécessaire à la gestion du registre. J'ai donc envie de rendre tout ça plus propre et, pourquoi pas, réutilisable ailleurs.

En Python, nous avons le décorateur [`@contextmanager`](https://docs.python.org/3/library/contextlib.html#contextlib.contextmanager), qui permet de transformer une fonction en contexte. En simplifiant, un context manager permet de gérer facilement l'acquisition et la libération d'une ressource. Dans notre cas, cela s'applique parfaitement au registre et à la gestion du boilerplate Git.

Je me mets donc à transformer mon workflow autour d'un context manager.
```py
@contextmanager
def get_registry(branch: str, filename: str):
    assert git("fetch", "origin", branch, cwd=root) == 0, f"Can't find the branch origin/{branch}"

    tmp = Path(tempfile.mkdtemp(prefix="refs-worktree-"))

    registry = None

    try:
        git("fetch", "origin", branch, cwd=root)
        git("worktree", "add", "--detach", str(tmp), f"origin/{branch}", cwd=root)

        registry = load_registry(tmp)
        yield registry
    finally:
        save_registry(tmp, registry)

        git("add", filename, cwd=tmp)
        git("commit", "-m", "Update reference registry", cwd=tmp)
        git("push", "origin", f"HEAD:{branch}", cwd=tmp)

        git("worktree", "remove", "--force", str(tmp), cwd=root, check=False)
        shutil.rmtree(tmp, ignore_errors=True)
```

Et l'utilisation devient extrêmement simple :

```py
with get_registry("registry/references", "references.json") as registry:
    ...
```

Avec cette interface, toute la logique autour de Git et du dossier temporaire est encapsulée dans une seule fonction.

Cependant, il reste un dernier problème : le bloc `finally` est toujours exécuté. Comme c'est lui qui pousse les modifications, j'aimerais qu'il ne s'exécute réellement que lorsqu'il y a eu des changements. Cela éviterait des commits inutiles et des messages parasites pendant le pre-commit.

## 4ème itération
La base est là. Le script fonctionne, le boilerplate est correctement isolé et on se rapproche d'une solution propre. Mais le bloc `finally` continue d'exécuter systématiquement les opérations Git. Il faut donc détecter si le registre a réellement été modifié.

L'idée est simple : conserver une copie de l'état initial du registre pour le comparer à son état final.
Je modifie donc le script :
```py
@contextmanager
def get_registry(branch: str, filename: str):
    assert git("fetch", "origin", branch, cwd=root) == 0, f"Can't find the branch origin/{branch}"

    tmp = Path(tempfile.mkdtemp(prefix="refs-worktree-"))

    registry = None
    before = None

    try:
        git("fetch", "origin", branch, cwd=root)
        git("worktree", "add", "--detach", str(tmp), f"origin/{branch}", cwd=root)

        registry = load_registry(tmp)
        before = @...(registry) # que faut-il utiliser ici ?

        yield registry
    finally:
        if registry and before != registry:
            save_registry(tmp, registry)

            git("add", filename, cwd=tmp)
            git("commit", "-m", "Update reference registry", cwd=tmp)
            git("push", "origin", f"HEAD:{branch}", cwd=tmp)

        git("worktree", "remove", "--force", str(tmp), cwd=root, check=False)
        shutil.rmtree(tmp, ignore_errors=True)
```

Mais alors, que faut-il utiliser pour conserver une copie fiable du registre initial ?

La première idée que j'ai eue, la plus simple, était d'utiliser la fonction native `hash()` de Python. L'idée semblait parfaite : récupérer le hash avant modification puis le comparer après. Simple, rapide, natif. Sauf qu'en réalité, cela ne fonctionne pas correctement pour ce cas.

Le hash d'un dictionnaire Python n'est pas fiable lorsqu'il contient des sous-objets modifiables. Modifier la valeur d'une clé ne garantit pas un changement de hash exploitable de cette manière. Cette solution n'était donc pas viable.

Deuxième idée : convertir le dictionnaire en chaîne de caractères puis calculer le hash de cette chaîne. Cette fois-ci, je suis sûr de détecter les modifications. Mais cela implique plusieurs conversions successives :
- dictionnaire → chaîne ;
- chaîne → hash ;
- puis à nouveau conversion pour sauvegarder.

Avec un petit registre, ce n'est pas un problème. Mais à long terme, avec des centaines ou des milliers de références, cela devient inutilement coûteux. Je me retrouve donc à nouveau bloqué. 

Je continue mes recherches et, en parcourant un bout de code de notre framework interne, je remarque l'utilisation de `deepcopy()` pour copier des objets qui contiennent des dictionnaires. Je me renseigne et cela semble parfaitement adapté à mon besoin. 

Certes, `deepcopy()` peut être coûteux sur de très gros objets profondément imbriqués. Mais dans mon cas, les objets restent simples et composés uniquement de types natifs. Le coût reste donc acceptable. En plus, cela me permet ensuite d'utiliser simplement l'opérateur `==` pour comparer précisément les deux dictionnaires.

La solution coche toutes les cases :
- simple ;
- native à Python ;
- sans dépendance externe ;
- suffisamment performante pour mon besoin.

Ma solution était donc trouvée : utiliser `deepcopy()`.

```python
before = deepcopy(registry) 
```

# Conclusion
Pfiou… nous voilà enfin au bout. Sacrée aventure pour un simple pre-commit et pour éviter de payer une base de données.

J'ai bien conscience que ce n'est pas la solution parfaite pour ce genre de problématique. Manipuler directement un JSON n'est pas idéal pour des requêtes complexes ou du filtrage avancé. Il faudrait probablement ajouter une couche d'abstraction supplémentaire, ce qui pourrait rapidement alourdir le mécanisme.

Mais pour mon besoin, c'est largement suffisant. Ce qui m'intéressait surtout ici, c'était l'aspect « hack » autour de GitHub, des pre-commit hooks et des worktrees pour résoudre un problème concret.

En parcourant le dépôt [Awesome Python](https://github.com/vinta/awesome-python), j'ai également découvert [TinyDB](https://github.com/msiemens/tinydb), un outil permettant de manipuler des fichiers JSON comme des bases de données.

L'outil semble intéressant. Il est possible que je l'utilise plus tard si les recherches de références deviennent plus complexes. Mais pour le moment, il est important de savoir s'arrêter à une solution adaptée au besoin présent et d'éviter l'overengineering.

Merci à tous d'avoir lu ce petit billet de blog, j'espère que tout ça vous inspirera 😊
