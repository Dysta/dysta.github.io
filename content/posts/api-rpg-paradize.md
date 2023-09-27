---
title:  "Une API pour RPG Paradize ?"
# description: "Apprendre à récupérer les données de RPG Paradize"
date:   2021-02-10T12:00:00+01:00
categories: "dev"
---
# Mise en contexte
Bonjour à tous ! Pour ce premier post sur mon blog j'aimerais vous partager un petit bout de code que j'avais fait il y a un moment.

Certains d'entre vous l'ont utilisé, mais pas tous. Il est également inclus dans mon CMS privé [*PantyCMS*](https://github.com/Dysta/Panty) afin de récupérer des statistiques sur RPG.

Ce petit bout de code permet de **parser** une page RPG afin de récupérer les infos suivantes :
- valeur out
- le nom
- le nombre de vote
- la position dans le classement
- le graphe RPG (voir plus bas)

J'ai réalisé ce petit bout de code lorsque je codais la partie admin de mon CMS Dofus. J'ai réalisé qu'avoir un récapitulatif automatique et précis de RPG Paradize directement dans le panel admin donnait une réelle plus value.

# Code
Lorsque j'ai réalisé le code, je l'ai fais en PHP pour rester sur la même stack technique que le CMS et donc, faciliter son intégration.
Cependant, il est facilement convertissable dans un autre langage comme Python ou Javascript (merci ChatGPT).

J'ai conscience que le code n'est pas des plus PHPiste qui existe étant donné mon niveau relativement basique dans le langage. Le code est donc prompt a diverses optimisation.

## Initialisation
```PHP {linenos=true}
<?php
class RpgApi {
    public function __construct($id) {
        $this->id = $id;
    }
}
?>
```
On commence par créer notre object RpgApi en lui fournissant simplement l'id de notre page. Pour rappel, l'id de la page se trouve à la fin de l'url. \
Par exemple, l'url [https://www.rpg-paradize.com/site-Fun-Zandix+2.10-101961](https://www.rpg-paradize.com/site-Fun-Zandix+2.10-101961), l'id sera **101961**. \
Notez également que tout ce qui se situe entre le `site-` et `-101961` est inutile et peu être enlevé.
Ainsi, l'url [https://www.rpg-paradize.com/site--101961](https://www.rpg-paradize.com/site--101961) est valide !

Nous pouvons donc initialiser notre api de cette façon :
```PHP {linenos=true}
$RPG = new RpgApi(101961);
```

## Récupérer le nombre de vote
Lorsque notre objet RpgApi est initialisé, il nous permet de récupérer de manière très simple le nombre de vote grace à la fonction publique `getVote()`.
```PHP {linenos=true}
 /**
 * Return RPG vote
 * @return int vote number
 */
public function getVote() {
    if (empty($this->webContent))
        $this->getWebContent();

    if (empty($this->votes)) 
        $this->parseVote();

    return $this->votes;
}
```
Cette méthode est en plusieurs temps. Elle va d'abord récupérer le HTML de la page grâce à la fonction privé `getWebContent()` pour ensuite *parser* le nombre de vote via la fonction `parseVote()`. \
La méthode qui permet de parser le nombre de vote n'est pas très compliqué. Elle repose sur une simple regEx qu'on applique sur le HTML récupéré.
```PHP {linenos=true}
private function parseVote() {
    preg_match('/Vote : (.*?)<\/a>/', $this->webContent, $vote);
    $this->votes = $vote[1];
}
```
Le principe est similaire pour les autres méthodes à l'exception de `parseGraph()`.

Nous pouvons donc ajouter à notre petit bout de code d'exemple le nombre de vote !

```PHP {linenos=true}
$RPG = new RpgApi(101961);

$vote = $RPG->getVote();
echo "<p> Vote : " . vote . "</p>";
```
Ici le nombre de vote est affiché dans une balise paragraphe. Pour récupérer d'autres info comme l'url ou le nombre de out, le principe est le même.

## Récuperation du code HTML
Comme dit précédemment, le code HTML est récupéré via la fonction `getWebContent()`. Cette fonction est appelée en interne et utilise le module PHP `curl`.
```PHP {linenos=true}
private function getWebContent() {
    $opts = array(
        CURLOPT_URL             => 'http://rpg-paradize.com/site--' . $this->id,
        CURLOPT_HEADER          => true,
        CURLOPT_RETURNTRANSFER  => true,
        CURLOPT_CONNECTTIMEOUT  => 3,
        CURLOPT_USERAGENT       => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246'
    );
    $ch = curl_init();
    curl_setopt_array($ch, $opts);
    $this->webContent = curl_exec($ch);
    curl_close($ch);
}
```
Je commence par initialiser un tableau avec tous mes paramètres CURL. Le nom des paramètres est défini par le module curl lui même. On peut voir que j'ai utilisé la méthode de supprimer l'intérieur de l'url afin d'être certain de tomber sur la bonne page. \
On continue en définissant un header et des user-agents afin que notre requête soit le moins suspecte possible. Puis on initialise notre objet curl en lui donnant les paramètres et en envoyant la requête.

Notez que dans chaque fonction `get*()`, un *if* est effectué sur le contenu du HTML afin de ne le récupérer qu'une seule fois et non à chaque fois que nous voulons récupérer une info comme ici sur `getName()` qui possède une structure similaire à `getVote()`.
```PHP {linenos=true}
/**
 * * Return RPG name
 * @return string name
 */
public function getName() {
    if (empty($this->webContent))
        $this->getWebContent();
    
    if (empty($this->name))
        $this->parseName();
    
    return $this->name;
}
```
Si vous voulez donc rafraîchir les données contenu dans votre objet rpg, vous devez le recréer. Notez qu'une fonction permettant de rafraîchir le contenu n'est pas réellement nécessaire vu que le site met à jour les données que toutes les 3 heures environs.
Cependant, cela reste possible de cette manière :
```PHP {linenos=true}
$RPG = new RpgApi(101961);

$vote = $RPG->getVote();
echo "<p> Vote : " . vote . "</p>";
// many treatment...

// we want to refresh data
$RPG = new RpgApi(101961);

$vote = $RPG->getVote();
echo "<p> Vote : " . vote . "</p>"; // will be an another number
```

# Graphe
Comme dit plus haut, ce petit script permet de récupérer le graphe RPG. Enfin.. il ne récupère pas le graphe en lui-même sinon ça serait beaucoup trop compliqué et très peu modulable. 
Il récupère simplement les données servant à construire le graphe sur RPG, à savoir, la date d'un jour et le nombre de vote correspondant à ce jour. De cette manière, vous êtes libres d'utiliser n'importe quelle bibliothèque de votre choix afin de construire le graphe comme bon vous sembles.

En effet, *RPG Paradize* utilise la bibliothèque [Char.js](https://www.chartjs.org/) pour générer ses graphes. Le fait de récupérer seulement les données nous permet d'utiliser une autre bibliothèque pour construire le graphe. Dans le screen ci-dessous, j'ai utilisé la bibliothèque [Morris.js](https://morrisjs.github.io/morris.js/) afin d'inclure le graphe RPG dans un panel admin..


| ![PCA](https://cdn.discordapp.com/attachments/573225654452092930/809038148763910184/unknown.png "Panel admin utilisant Morris.js pour générer le graphe") |
| --: |
| Fig.1 -- PantyCMS -- Panel admin utilisant Morris.js pour générer le graphe |

| ![RPG](https://cdn.discordapp.com/attachments/573225654452092930/809038370167586846/unknown.png) |
| --: |
| Fig.2 -- RPG Paradize -- Graphe d'origine généré avec Chart.js |

## Récupération des infos
La récupération des infos du graphe se fait dans la fonction `parseGraph()`. Cette fonction construit un tableau de la forme suivante :
```PHP {linenos=true}
[
    "key_id" = {
        "date": "YYYY-MM-DD",
        "vote": 5
    },
    "key_id" = {
        "date": "YYYY-MM-DD",
        "vote": 9
    },
    "key_id" = {
        "date": "YYYY-MM-DD",
        "vote": 13
    },
    // ...
]
```

Dans un premier temps, je fais comme les autres méthodes. j'applique une regEx sur le contenu HTML afin d'extraire une énorme string contenant les labels (les dates) et la data (les votes) puis je crée un tableau en séparant la string via les virgules entre chaque donnée.
```PHP {linenos=true}
preg_match('/labels : \[(.*?)\]/',$this->webContent, $label);
preg_match('/data : \[(.*?)\]/', $this->webContent, $data);
$array_label = explode(",", $label[1]);
$array_data = explode(",", $data[1]);
```

Dans le tableau des dates, chaque date est entouré de double quote. Il faut les enlever.
```PHP {linenos=true}
foreach($array_label as $k => $v)
    $array_label[$k] = substr($v, 1, -1);
```

Je peux ensuite crée le tableau final qui contient la donnée des labels nettoyé en lui associant le bon nombre de vote
```PHP {linenos=true}
$this->graph = array();
foreach ($array_label as $k => $v) {
    $this->graph[$k]['date'] = $array_label[$k];
    $this->graph[$k]['vote'] = $array_data[$k];
}
```
C'est ce tableau qui sera retourné à l'utilisateur lorsqu'il appellera la fonction `getGraph()`.
```PHP {linenos=true}
/**
 * Return RPG graph data
 * @return array RPG graph data as array('date', 'votes')
 */
public function getGraph() {
    if (empty($this->webContent))
        $this->getWebContent();
    
    if (empty($this->graph)) 
        $this->parseGraph();
    
    return $this->graph;
}
```

# Exemples
Les nombreux bout de code présent dans ce billet sont tirés du dossier exemple du repos GitHub disponible [ici](https://github.com/Dysta/RpgApi/tree/master/examples)


---

Merci de votre lecture et à une prochaine ! 👋