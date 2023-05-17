# Documentation RENAG quality check

## Utilisation du *dashboard*

TODO cdc

### Assigner une couleur à une courbe.

L'assignation d'une couleur à une courbe se fait en fonction du nom de la courbe : si une nouvelle courbe est ajoutée, il est nécessaire de lui assigner manuelement une nouvelle couleur.

Cela se fait en créant un *override* sur le *dashboard*. Le moyen le plus simple de faire ça consiste à cliquer sur la couleur de la courbe :

![Couleur de la courbe](img/couleur_courbe.png)

Un menu s'ouvre vous invitant à choisir la couleur de la courbe :

![Menu](img/click_couleur_courbe.png)

Il est possible de rentrer la couleur qu'on veut :

![Color picker](img/click_couleur_custom.png)

### Administration

TODO

- Compte admin
- Ajouter des utilisateurs

## Utilisation du script d'alimentation de la base de données

TODO xtr2database <!-- attendre que l'interface CLI soit definie -->

## Sauvegarde et restauration des données des données

TODO

- scripts *wrapper* `pg_dump` & `pg_restore`
- 2 bases de données... (bref car section config bdd)

## Déployement sur une nouvelle machine

### Pré-requis

Avant d'installer et de configurer le *dashboard* sur une machine, il est nécéssaire d'avoir à disposition une base de données [PostgreSQL](https://www.postgresql.org/).

Pour l'installation, referez-vous aux instructions adaptés à votre système : https://www.postgresql.org/download/.

Une version récente (15+) est conseillé, même si cela devrait fonctionner avec des versions plus anciennes de PostgreSQL.

### Configuration de la base de données

Une fois que la base de donnée est accesible, ...

1. Importer le schéma

2. Créer l'utilisateur pour grafana (uniquement select)

### Installation de Grafana

Installez la version 9.5 de Grafana : https://grafana.com/grafana/download?platform=linux&edition=oss.

### Configuration de Grafana

TODO documenter le fichier de config (voir le docker-compose)

### Plugins

- nline-plotlyjs-panel
- marcusolsson-dynamictext-panel

### Connexion à la base de donnée

TODO grafana <-> bdd avec bon utilisateur

### Importation des dashboards

TODO comment importer les dashboards
