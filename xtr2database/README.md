# xtr2database - Script d'importation des données

Ce script à pour but d'importer les données situées dans des fichiers de qualité xtr pour les mettre en forme en vue de leur insertion dans une base de donnée PostgreSQL.

## Installation du script

> **NOTE :** Le script requiert la version 3.7 de Python minimum pour fonctionner, idéalement la version 3.11.

Le script s'installe et se met à jour avec la commande suivante, [git](https://git-scm.com/) est requis :

```bash
pip install -U git+https://gitlab.oca.eu/AstroGeoGPM/renag-qc#subdirectory=xtr2database
```

Vous pouvez maintenant utiliser le script ! Testez qu'il soit bien installé avec la commande suivante :

```sh
xtr2database --help
```

Si cela ne marche pas, peut être que le script n'est pas dans votre path. Dans ce cas, il faudrait utiliser :

```sh
python3 -m xtr2database -h
```

### Gestion des identifiants de connexion à la base de données

Pour se connecter à la base de données, il y a deux moyen de spécifier les identifiants.

- Par variables d'environement, en configurant `X2D_USER` et `X2D_PASSWORD` avec le nom d'utilisateur et le mot de passe respectivement.
- Par arguments en ligne de commande, avec `--user` et `--password`. Les arguments en ligne de commande sont prioritaire sur les variables d'environement.

## Exemples d'utilisation

Le script possède deux modes d'utilisation, l'importation des fichiers xtr et la vérification de la disponibilité des fichiers.

### Lecture et importation des fichiers xtr

Cette promière fonction du script s'utilise de la manière suivante :

```sh
xtr2database import <chemin/vers/fichiers_xtr> <nom du réseau>
```

Le script va se connecter à la base de données, lire les fichiers xtr dans le répertoire précisé et sauvegarder les données comme faisant partie du réseau donné.

Par défaut, les données vont être insérées en mode strict : avant de commencer l'insertion, le script va interroger la base de données et récupérer la liste des fichiers dont le contenu a déjà été inséré dedans. Ainsi, le script va traiter uniquement les fichiers qu'il n'a pas déjà traité précédemment.

Il est possible d'écraser les données précédement insérées pour un réseau avec l'option `--override` :

```sh
xtr2database --override import <chemin/vers/repertoire> <nom du réseau>
```

### Vérificaion de la disponibilité des fichiers

Cette seconde fonction s'utilise de cette manière :

```sh
xtr2database file_status <chemin/vers/rinex3> <chemin/vers/xtr> <nom du réseau>
```

Le script va parcourir les deux répertoires et va enregistrer dans la base de données, pour chaque jours, la présence de fichiers Rinex 3 et xtr.
