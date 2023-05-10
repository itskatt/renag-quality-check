# Documentation RENAG quality check

## Utilisation du *dashboard*

TODO cdc

### Modification des couleurs des courbes

TODO

### Administration

TODO

- Compte admin
- Ajouter des utilisateurs

## Utilisation du script d'alimentation de la base de données

TODO xtr2database <!-- attendre que l'interface CLI soit definie -->

## Sauvegarde des données

TODO scripts `pg_dump`

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

TODO documenter le fichier de config

### Connexion à la base de donnée

TODO grafana <-> bdd avec bon utilisateur

### Importation des dashboards

TODO comment importer les dashboards