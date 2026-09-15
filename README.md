# dysta.github.io

## Développement

Utiliser Hugo **0.166.0**, également fixé dans le workflow GitHub Pages.

```sh
git submodule update --init --recursive
hugo server
```

Le thème actif est `themes/PaperMod` (sous-module PaperMod). Les
personnalisations sont conservées dans le dépôt du site pour survivre aux
mises à jour du sous-module :

- `layouts/home.html` : accueil GitHub.
- `layouts/cv.html` : CV et compétences.
- `layouts/_partials/extend_head.html` : redirection Discord.
- `assets/css/extended/github-home.css` : styles de l’accueil et calendrier sombre.

Les shortcodes `inTextImg` et `rawhtml`, ainsi que le style des images intégrées,
sont déjà fournis par PaperMod.

Validation : `hugo --minify`. Avec la révision actuelle du sous-module, Hugo
signale deux dépréciations dans PaperMod (`LanguageDirection` et `LanguageCode`),
sans empêcher la compilation.
