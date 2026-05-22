---
title:  "Git + JSON + worktree = petite base de donnée"
date:   2026-05-22T12:00:00+01:00
categories: "life"
draft: true
---
# Les worktrees de Git pour partager de la donnée en fond

Besoin initiale, à chaque commit, s'assurer qu'une référence est bonne, la sauvegarder ou alors rejeter le commit si un truc va pas.

```py
# v contextmanager
@contextmanager
def get_db(root: Path):
    git("fetch", "origin", REFERENCES_BRANCH, cwd=root, check=False)
    exist = (
        subprocess.run(
            ["git", "rev-parse", "--verify", f"origin/{REFERENCES_BRANCH}"],
            cwd=root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode
        == 0
    )
    if not exist:
        raise RuntimeError(
            f"Can't find branch origin/{REFERENCES_BRANCH}\nPlease contact the IT team",
            file=sys.stderr,
        )

    tmp = Path(tempfile.mkdtemp(prefix="refs-worktree-"))

    registry = None
    before = None

    try:
        git("fetch", "origin", REFERENCES_BRANCH, cwd=root)
        git("worktree", "add", "--detach", str(tmp), f"origin/{REFERENCES_BRANCH}", cwd=root)

        registry = load_registry(tmp)
        before = copy.deepcopy(registry)

        yield registry
    finally:
        if registry and before != registry:
            save_registry(tmp, registry)

            git("add", REFERENCES_FILE, cwd=tmp)
            git("commit", "-m", "Update reference registry", cwd=tmp)
            git("push", "origin", f"HEAD:{REFERENCES_BRANCH}", cwd=tmp)

        git("worktree", "remove", "--force", str(tmp), cwd=root, check=False)
        shutil.rmtree(tmp, ignore_errors=True)

def main():
    root = repo_root()
    try:
        with get_db(root) as registry:
            return update_reference_registry(root, registry, files, args.yes)
    except Exception as e:
        print(f"Error {e}")
        return 1
```


L'idée derrière, avoir un pre commit hook qui ajoute une ref


Itération 1
J'ai fait un 
`git("worktree", "add", str(tmp), f"origin/{REFERENCES_BRANCH}", cwd=root)`
mais pas de --detach du coup ça clone la branch en local, parfois des conflits


Itération 2
On ne clone plus la branche localement, on veut seulement une branche détachée de HEAD et pousser notre commit. En gros on passe en "write only"

Itération 3
On ajoute le contexte manager car on se rend compte qu'on a quand même bcp de boiler plate qu'on veut éviter dans notre code et qu'on préfère déléguer à notre contexte

Itération 4
Il faut mtn détecter les changements entre ancien et nouveau registry,
  Idée 1: hash du dict de notre registry
    Pas bon car hash(dict) ne détecte pas les modifs profonde
  Idée 2: hash du string du dict
    Fonctionne mais bcp trop de conversion, limitation si registry lourd
  Idée 3: deepcopy de l'ancien qu'on compare au nouveau dict
    Validé car deepcopy de dict opti et fallback sur du C

Itération 5
On considère notre JSON comme une DB, pourquoi pas utiliser [TinyDB](https://github.com/msiemens/tinydb) pour faire des querys plus complèxe

Avantage:
On paye pas de db, pas de setup de db côté user, pas de ship de db en prod, juste 1 branch seul détachée qui ne contient que le json

Inconvénient:
Pas vraiment scalable pour d'autre usages que quelque chose de simple
