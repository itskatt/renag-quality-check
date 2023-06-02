# Documentation RENAG quality check

## Utilisation du *dashboard*

TODO définition du cdc

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

## Script d'alimentation de la base de données

Pour pouvoir lire et extraire les données pertinentes à l'affichage des graphiques depuis les fichiers XTR et les insérer dans la base de données, un script (xtr2database) est fourni.

### Instalation du script

<!-- TODO : tester les compatibilité de version -->
> **NOTE :** Le script requiert la version 3.7 de Python minimum pour fonctionner, idéalement la version 3.11.

Une fois que vous vous êtes déplacé dans le répertoire [xtr2database](../xtr2database/), suivez les étapes suivantes :

1. #### Création d'un environnement virtuel (optionnel)

    Un [environnement virtuel en Python](https://docs.python.org/3/library/venv.html) est un espace isolé qui permet de gérer facilement les dépendances et les configurations spécifiques d'un projet, offrant ainsi une meilleure portabilité et évitant les conflits entre différentes applications.

    Suivez cette étape si l'installation du script pose un souci de compatibilité de dépendances. Sachez qu'il sera nécessaire d'activer (une seule fois) l'environnement virtuel à chaque utilisation du script.

    ```sh
    # Création
    python3 -m venv env

    # Activation
    source env/bin/activate
    ```

2. #### Installation du script

    ```sh
    python3 -m pip install -U .
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

### Utilisation

Une utilisation basique du script s'effectue de la manière suivante :

```sh
xtr2database <chemin/vers/repertoire> <nom du réseau>
```

Le script va se connecter à la base de données, lire les fichiers xtr dans le répertoire précisé et sauvegarder les données comme faisant partie du réseau donné.

Par défaut, les données vont être insérées en mode strict : avant de commencer l'insertion, le script va interroger la base de données et récupérer la liste des fichiers dont le contenu a déjà été inséré dedans. Ainsi, le script va traiter uniquement les fichiers qu'il n'a pas déjà traité précédemment.

Il est possible d'écraser les données précédement insérées pour un réseau avec l'option `--override` :

```sh
xtr2database <chemin/vers/repertoire> <nom du réseau> --override
```

Finalement, il est possible de décomprésser à la volée des fichiers xtr compressé avec gzip avec l'option `--gziped`.

## Sauvegarde et restauration des données

Il est recommandé d'effectuer des sauvegardes régulières des bases de données. Pour cela, un script de sauvegarde des données (`backup.sh`) ainsi qu'un script de restauration des données (`restore.sh`) sont fournis.

Pour que les script fonctionnent, il est nécéssaire d'avoir les utilitaire `pg_dump` et `pg_restore` sur le PATH.

<!-- TODO : username + password -->

Exemple d'utilisation :

```sh
# Sauvegarde des bases de données
./backup.sh
# Cela produit un fichier "backups_2023-05-19_10-15-41.tar.gz"

# Restauration
# Extraction de l'archive
tar xzf backups_2023-05-19_10-15-41.tar.gz

# Restauration des données de "quality_check_data_backup" dans la base de données "quality_check_data"
./restore.sh "quality_check_data_backup" "quality_check_data"
```

> **Note** : Pour accelerer la restauration des données, il est recomendé de temporairement supprimer les indexes. Vous pouvez utiliser le script [drop_indexes.sql](../database/drop_indexes.sql) pour cela, et ensuite re-créer ces indexes avec [create_indexes.sql](../database/create_indexes.sql).

## Déployement sur une nouvelle machine

### Pré-requis

Avant d'installer et de configurer le *dashboard* sur une machine, il est nécéssaire d'avoir à disposition une base de données [PostgreSQL](https://www.postgresql.org/).

Pour l'installation, referez-vous aux instructions adaptés à votre système : https://www.postgresql.org/download/.

Une version récente (15+) est conseillé, même si cela devrait fonctionner avec des versions plus anciennes de PostgreSQL.

### Configuration de la base de données

#### Création des bases de données

Une fois que la base de donnée est accesible, il est nécéssaire de créer deux bases de données :

- Une pour Grafana
- Une pour les données à afficher

```sql
create database grafana;
create database quality_check_data;
```

Pour la base de données `quality_check_data`, il est nécéssaire d'ajuster les permissions. En effet, Grafana ne filtre pas les requêtes envoyées à la base de données, il faut donc créer un utilisateur avec un minimum de permissions.

Une fois connecté à la bonne base de données :

```sql
revoke all on schema public from public;

create user grafana_reader with password '<mdp>';

grant connect on database quality_check_data to grafana_reader;
grant usage on schema public to grafana_reader;
grant select on all tables in schema public to grafana_reader;
```

#### Importation du schéma

Pour que le script puisse fonctionner, il est nécéssaire d'importer le [schéma](../database/schema.sql) :

```sh
psql -d quality_check_data -f schema.sql
```

Ensuite, insérer des données universelles :

```sh
psql -d quality_check_data -f inserts.sql
```

Et finalement, créer les indexes. Sachez cependant qu'il est recommandé de les créer une fois que le plus gros des données ont été insérées :

```sh
psql -d quality_check_data -f create_indexes.sql
```

### Installation de Grafana

Installez la version **9.5** de Grafana : https://grafana.com/grafana/download?platform=linux&edition=oss.

### Configuration de Grafana

Une fois que Grafana a été installé, il est nécéssaire de configurer. Pour cela, localisez le [fichier de configuration à utiliser en fonction de votre système](https://grafana.com/docs/grafana/latest/setup-grafana/configure-grafana/#configuration-file-location), puis modifiez les valeurs suivantes :

#### Section `server`

- `enable_gzip` = true

#### Section `database`

- `type` = postgres (ou "mysql" ou "sqlite3")
- `host` = \<adresse\>:\<port\>
- `name` = grafana
- `user` = \<utilisateur\>
- `password` = \<mdp\>

#### Section `auth.anonymous`

- `enabled` = true
- `org_name` = Géoazur


Il peut être nécéssaire de configurer d'avantage Grafana en fonction de la configuration du serveur (par exemple si Grafana est exposé directement ou si un proxy inverse est utilisé). Pour cela, référez-vous à la documentation officielle : https://grafana.com/docs/grafana/latest/setup-grafana/configure-grafana/.

### Plugins

Nos visualisations requierent les plugins suivants :

- nline-plotlyjs-panel
- marcusolsson-dynamictext-panel

[Guide sur l'installation des plugins](https://grafana.com/docs/grafana/latest/administration/plugin-management/#install-a-plugin).

### Connexion à la base de donnée

Une fois que la base de données est prête et que Grafana a été correctement configuré et installé, il faut définir notre base de données comme source de données pour Grafana.

Référez-vous à la documentation officielle de Grafana : https://grafana.com/docs/grafana/latest/datasources/postgres/#postgresql-settings.

### Importation des dashboards

TODO comment importer les dashboards
