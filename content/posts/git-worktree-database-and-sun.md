---
title:  "Git + JSON + worktree = petite base de donnée partagée"
date:   2026-05-22T12:00:00+01:00
categories: "dev"
draft: true
---
# Du stockage simple, sans frais et sans maintenance
1 an depuis le dernier poste ou c'était un petit hack de GitHub pour avoir une API sans payer. Je vous ai présenté fièrement mon idée et les retours ont été plutôt positif. Devinez quoi ? Aujourd'hui, on remet ça !

## Contexte
Dans mon travail actuel, nous écrivons des documents référencés. Une référence est défini par un code unique issue d'une combinaison de trois chose :
- le type de projet, un trigramme bien souvent
- le type du document, souvent le nom du projet utilisé en interne auquel on rattache le document en cours de rédaction
- un id unique, choisi par l'auteur du document

Lorsqu'on calcul la référence, on prend ces 3 éléments qu'on lie avec un `-`. Ce qui peut nous donner par exemple `POP-DOC1234-TI99902`.

Ces références sont partagés dans toute l'entreprise par l'ensemble des collaborateurs car elles permettent d'identifier les documents crés et signés.

Avant mon arrivé, aucun outil ne permettait une vérification des références autre que localement. La seule façon de faire était de générer l'ensemble des documents et c'était pendant la génération qu'était vérifé qu'aucune duplication est présente. Autant vous dire que personne ne prenait le temps de faire ça sur son pc. Sinon, une pipeline GitHub s'en chargeait. Mais bien souvent la pipeline était lancé en fin de rédation et donc révelait le soucis trop tard. Dernier point, et pas des moindres : avec le temps, différents projets se sont constitués au sein de l'entreprise, le système de vérification des doublons n'est pas prévu pour aller chercher dans les autres projets, il se peut donc que des références soient dupliqués entre les différents projets, ce qu'on ne souhaite pas.

J'ai donc été missionné pour trouver une solution.

## Les bases
Pour répondre à ce besoin, j'ai l'idée d'utiliser une base de donnée qui serait alimenté pendant l'exécution d'un pre-commit hook. Pourquoi un pre-commit hook ? Car le lancement des hooks est déjà paramétrés chez l'ensemble des collaborateurs, je n'aurais donc rien à faire hormis rajouter le miens. De plus, ça permet d'assurer que notre script sera lancé, de manière correctement qui plus est et toujours au même moment. \
Pour le stockage, l'idée de paramétrer et d'héberger une base de donnée dans le cloud ne me plaisait pas, le ratio entre maintenir à jour plusieurs outils décentralisé pour des strings me paraissait pas du tout équilibré. Puis, d'expérience, je sais que c'est quelque chose qui sera oublié jusqu'au jour ou ça ne fonctionne plus et qu'on se rendent compte qu'on a ignoré des warnings involontairement depuis des mois et qu'il faut tout mettre à jour, bloquant au passage l'ensemble des collaborateurs pendant quelques heures.

Je voulais une solution simple, qui serait évolutif et qui ne demanderais très peu voir aucune maintenance humaine. Dans la continuité de mon ancien projet d'API REST sur GitHub, j'ai eu l'idée d'utiliser une branche dédié sur le repos GitHub pour stocker nos données. De plus, tout le monde peut aller sur la branche et vérifier les références avec un simple Ctrl + F. Et en bonus, avec mon ancien projet d'API REST sur GitHub, je savais qu'une lecture des références pouvait être facilement mis en place avec une petite requête HTTPS via un script ou un frontend prévu pour l'occasion.  \
Pour la mise en place des bases c'est plutôt simple : on configure une branche qui serait orpheline au projet (sans historique) et qui ne contiendrait simplement qu'un seul fichier JSON, ça nous fait donc une branche très rapide à récupérer, puis on y ajoute nos référenes et, on le renvoi sur la branche, tout ça dans le dos de l'utilisateur. Il y verrais que du feu ! Pour le format du JSON c'est simple, en clé : notre référence, en valeur : tout ce qu'on veut et qui pourra nous servir maintenant et plus tard, un peu comme une base de donnée NoSQL.

Après rapide présentation de l'idée à mon collègue, il a tout de suite adoré et validé ! Me voilà donc parti pour mettre en place mon pre-commit hook, ma branche dédié et mon fichier JSON.

# De l'idée à la pratique
## Mise en place
Pour commencer, il faut créer notre branche orpheline qui servira de base de donnée. Dans mon cas, j'ai appliqué la convention `registry/*` afin de pouvoir appliquer des règles de protection sur GitHub et protégé ma branche des pull requests ou des merge dans une autre branche. En plus, ça me permet de l'identifier rapidement dans la masse de branche non supprimé après une pull request approuvée (supprimez vos branches svp).

Pour le setup, ça donne ça :
```bash
git checkout --orphan registry/references # on crée notre branche sans historique
git rm -rf . # on supprime l'intégralité des fichiers
echo "[]" >> references.json # une liste vide car on aura une liste d'objet JSON
git add references.json
git commit -m "first commit"
git push
```
Pas plus compliqué que ça ! On a initialisé une branche sur notre repository, qui n'a pas d'historique et qui ne contient qu'un seul fichier !

## Utilisation dans notre pre-commit
Au vu de la simplicité de notre branche, elle est très rapide à pull. Cependant cette strategie pose un nouveau problème. Il est compliqué de basculer dessus de manière traditionnel à l'aide d'un checkout car la différence d'historique et la quantité de modification détecté rend le tout très lent et surtout, très peu stable pour le cas d'un script qui fera ça en arrière plan sans intervention humaine.

## Les worktrees à la rescousse
Heureusement pour nous, git possède un système de worktree. Pour faire simple, un worktree permet de partager le même `.git` mais dans des dossiers différent, ce qui permet d'avoir différentes branches en même temps sans devoir checkout à chaque fois. Il suffit simplement de changer de worktree. Cela répond parfaitement à notre besoin ! Voici l'approche : nous pouvons créer un worktree en arrière plan, checkout sur la branch `registry`, faire notre tambouille et push sur la branche remote !

# Vous avez des problèmes ? J'ai des solutions.
Je vous épargnes l'implémentation mais de mon côté je l'ai fait en **Python**.
Voici le workflow adopté dans le script et qui sera joué à chaque pre-commit :
- On check si on détecte la branch `registry` en ligne
- On fetch la branche en ligne
- On créer un dossier temporaire dans `/tmp` avec un nom aléatoire pour éviter les collisions
- On créer notre worktree dans le dossier temporaire de l'étape précédente, avec la branche récupéré dans les étapes plus haut.
- Mise à jour de la donnée
- On crée un commit avec le nouveau json
- On push le commit sur la branche `registry`
- On supprime le worktree
- On supprime le dossier temporaire

## 1ère itération
Pour la première itération de notre script, je suis allé au plus simple à chacune des étapes cité précédemment.

- `git fetch origin registry/references`
- `git worktree add /tmp/... registry/references`

Manipulation de notre registry

- `git add references.json`
- `git commit -m "Update references registry"`
- `git push origin registry/references`
- `git worktree remode --force /tmp/...`
- `rm -rf /tmp/...`

On configure notre pre-commit et on envoi en prod et : tout roule ! 🎉

Les premiers commit tombe, je vois le registry se remplir et je suis content car tout fonctionne.
Avec ce workflow, aucune trace de notre passage ! En plus, supprimer le worktree et le dossier temporaire évite des soucis de synchronisation entre la branche registry local et remote.

Enfin... C'est ce que je croyais...

## 2ème itération
Un matin, on vient me voir et on me dit qu'il est impossible de faire de commit car le pre-commit bloque. Je regarde donc ce qui se passe et j'avoue que je ne comprends pas trop.
Le soucis est que le pre-commit ne peux pas pull la branche distante car la branche local diverge. Sur le coup, je ne comprends pas exactement le soucis car de mon côté, j'efface toute trace de mon passage. Impensable donc qu'il reste quoi que ce soit de cette branche qui puisse poser un soucis du genre !

Je commence donc mon investigation et je comprends le scénario pour reproduire le bug. La divergence vient du fait que lors de la création du worktree, HEAD est copié en local via le checkout. Si quelqu'un d'autre ajoute une référence via un commit, il va changer le HEAD distant. Mais vu qu'on supprime la branche en local, git n'est pas capable de savoir quelle stratégie appliquer pour résoudre la divergeance. C'est ce qui provoque notre blocage. Du coup, impossible de refaire un commit si on a déjà fait un commit avant ! Je comprends donc que mon script ne fonctionne pas comme je le souhaite et qu'il y a quand même une trace de mon passage qui est gardé en local, je dois changer ça. 

Je continue donc mes recherches... Après quelques dizaines de minutes écoulés, je découvre qu'il est possible de ne pas faire de copie local de HEAD et de se positionner directement sur le HEAD distant en utilisant l'argument `--detach` lors de la création de notre worktree.

Je met donc ma seconde étape à jour avec ma nouvelle commande : \
`git worktree add --detach /tmp/... origin/registry/references`

J'effectue mes tests, ça fonctionne ! Je publie mon correctif et tout est bien qui fini bien. Les utilisateurs peuvent à nouveau commit et la, vraiment aucune trace n'est gardé en local de mon passage, je suis satisfait.

Mais quand même... Quelque chose me dérange dans mon script...

## 3ème itération
Les jours passent, pas de soucis en vue. Le script fonctionne bien, les références s'ajoutent petit à petit. Les gens râlent car ça devient bloquant de commit un document sans référence et qu'il faut en mettre un, mais c'est le but !

Mais quand même... Quelque chose me dérange dans mon script...

Quand je regarde mon script, je me rend compte que la logique de modification des références est énormément parasité par mon code boilerplate permettant de manipuler git et mon registre. J'ai donc envie d'améliorer ça pour que ça soit plus propre et, pourquoi pas, réutiliser le système ailleurs ?

En python, on a le décorateur [@contextmanager](https://docs.python.org/3/library/contextlib.html#contextlib.contextmanager) qui permet de transformer une fonction en contexte. En gros, le contextmanager aide a gérer de manière simple le moment ou on acquière et on libère une ressource. Si on adapte un peu le système, on peut l'utiliser pour notre registry et le boilerplate git.

Je m'attèle donc à la tâche de transformet mon workflow avec l'utilisation d'un contextmanager. De manière simple, mon contexte est
```py
@contextmanager
def get_registry(branch: str, filename: str):
    exist = git("fetch", "origin", branch) == 0
    if not exist:
        raise RuntimeError(
            f"Can't find branch origin/{branch}.",
            file=sys.stderr,
        )

    tmp = Path(tempfile.mkdtemp(prefix="refs-worktree-"))

    registry = None

    try:
        git("fetch", "origin", brancg, cwd=root)
        git("worktree", "add", "--detach", str(tmp), f"origin/{brancg}", cwd=root)

        registry = load_registry(tmp)
        yield registry
    finally:
        save_registry(tmp, registry)

        git("add", filename, cwd=tmp)
        git("commit", "-m", "Update reference registry", cwd=tmp)
        git("push", "origin", f"HEAD:{brancg}", cwd=tmp)

        git("worktree", "remove", "--force", str(tmp), cwd=root, check=False)
        shutil.rmtree(tmp, ignore_errors=True)
```

que je peux utiliser comme ça :
```py
with get_registry("registry/references", "references.json") as registry:
    ...
```

Avec cet interface simple, je sais que la logique autour de git et du dossier temporaire est complètement caché dans une seule fonction et ne se balade plus partout dans mon script. Il reste cependant un dernier soucis : vu que mon block `finally` sera exécuté en permanance et que c'est dans celui-ci que les modifications sont envoyés, j'aimerais qu'il ne s'exécute que lorsque qu'il y en a qui ont été faites. Cela évite d'avoir un message parasite pour les utilisateurs lorsqu'ils vont lancer mon pre-commit.

## 4ème itération
La base est la, mon script fonctionne, le boilerplate est extrait de la logique de modification du registry, je touche presque à la perfection !
Comme dit avant, le block `finally` est quand même exécuté, peut importe si il y a eu des modifications ou non. Un `git add/commit/push` sera fait. Et je ne veux pas.

Il faut donc que je détecte les modifications sur mon registry que je renvoi. L'idée est simple, avant de retourner mon registry, je garde une trace de son état initial afin de le comparer avec son état final. Je modifie donc mon script de la façon suivante :
```py
@contextmanager
def get_registry(branch: str, filename: str):
    exist = git("fetch", "origin", branch) == 0
    if not exist:
        raise RuntimeError(
            f"Can't find branch origin/{branch}.",
            file=sys.stderr,
        )

    tmp = Path(tempfile.mkdtemp(prefix="refs-worktree-"))

    registry = None
    before = None

    try:
        git("fetch", "origin", brancg, cwd=root)
        git("worktree", "add", "--detach", str(tmp), f"origin/{brancg}", cwd=root)

        registry = load_registry(tmp)
        before = @...(registry) # qu'est-ce qu'il faut que j'utilise ici ???

        yield registry
    finally:
        if registry and before != registry:
            save_registry(tmp, registry)

            git("add", filename, cwd=tmp)
            git("commit", "-m", "Update reference registry", cwd=tmp)
            git("push", "origin", f"HEAD:{brancg}", cwd=tmp)

        git("worktree", "remove", "--force", str(tmp), cwd=root, check=False)
        shutil.rmtree(tmp, ignore_errors=True)
```

Mais du coup, qu'est-ce qu'il faut que j'utilise pour garder une trace de mon ancien registry ?

La première idée que j'ai eu et la plus simple ? Passer par la fonction native `hash` en python. Je récupère le hash avant les modifications et je le compare au hash après modification. Parfait ça ! C'est rapide, natif et super simple à mettre en place. Mais en faite non. L'inconvénient est que le hash d'un dictionnaire en python n'est pas fiable sur les sous objets qu'il contient. Le hash ne sera fait que sur la racine. En gros, si j'ajoute ou que je modifie une référence (une clé) dans celui-ci, le hash de mon dictionnaire sera toujours le même. Cette solution n'est donc pas envisageable.

La seconde idée qui me vient et de continuer d'utiliser `hash` mais cette fois ci sur la string du dictionnaire. Malin ça, au moins je suis sûr de détecter les modifications cette fois-ci. J'adapte donc mon script, je charge mon registry, je reconvertis en string, je récupère le hash de celui-ci, puis j'envoi mon registry. Il revient, je reconverti le nouveau registry en string, un coup de hash, je compare et je reconverti une dernière fois pour le sauvegarder et c'est... gagné..? Je me rend compte qu'il y a beaucoup trop de conversion en string, 3 pour être précis. Pour l'instant mon registry est petit donc c'est rapide, mais dans quelques semaines, quand tout mes collègues vont avoir publiés leurs documents, mon registry sera énorme lui ! Non, je ne peux pas faire comme ça, ce n'est pas scalable du tout.

Me voilà à nouveau bloqué, si près du but ! Je cherche donc d'autre solution, je farfouille le web... Je ne trouve pas grand chose qui me satisfait. Entre temps, je fini un autre ticket et en parcourant le code, je vois que `deepcopy()` est utilisé pour copier des dictionnaires. Je reprends donc mon problème et je regarde si c'est adapté à mon usage. D'après internet, c'est un peu lent sur les gros dictionnaires d'objets imbriqué. Dans mon cas, mes objets sont simples et sont composés uniquement de types natifs. Je ne pense pas être impacté tant que ça dans par la lenteur. En plus, ça me permet ensuite utiliser l'opérateur `==` entre mes deux dictionnaires pour les comparer de manière précise et détecter mes modifications. \
Tout ça répond plutôt bien à mon besoin. C'est simple, c'est natif à Python, pas besoin de dépendance externe et ça n'allourdi en rien mon script.

Ma solution est toute trouvée ! J'utilise donc `deepcopy()` !

# Conclusion
Pfiou, on est enfin à la fin ! Sacré aventure la dit donc ! Tout ça pour un pre-commit et ne pas payer une base de donnée. C'est ça la vie d'artiste oui !

J'ai bien conscience que ce n'est pas LA solution parfaite pour ce genre de soucis, manipuler un JSON n'est pas vraiment adapté pour le cas de requêtes complèxe ou du filtrage. Il faudra rajouter une couche par dessus tout ça et ça peut vite allourdir notre méchanisme. 

Pour mon besoin, lire une clef, écrire une clef, c'est amplement suffisant. Ce qui m'intéressait plus ici c'était l'aspect 'hack' de GitHub, des pre-commit et du fonctionnement des worktrees pour résoudre mon problème.

En parcourants le dépôt [Awesome Python](https://github.com/vinta/awesome-python), j'ai trouvé un outil permettant de manipuler les JSON comme des bases de données : [TinyDB](https://github.com/msiemens/tinydb). \
L'outil semble assez puissant, il se peut que lorsque j'aurais plus de complexité dans les recherches de références, je le mette en place. En attendant, il est important de savoir s'arrêter à une solution à un instant T et ne pas commencer à faore de l'overengineering.

Merci à tous d'avoir lu ce petit billet de blog 😊