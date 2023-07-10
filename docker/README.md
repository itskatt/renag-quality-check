# Configuration Docker Compose minimale

Ceci est un exemple de configuration Docker Compose pour déployer l'application. **A adapter selon vos besoins.**

## Comment lancer et arrêter l'application ?

Tout simplement : 

```bash
docker-compose up -d
```

Cela va lancer la base de données PostgreSQL sur le port 5432, le tableau de bord Grafana sur le port 3000 ainsi que le service permettant de produire des images à partir des graphiques.

La première fois que vous lancer la commande, attendez une ou deux minutes le temps que les images Docker se téléchargent et que la base de données s'initialise.

Pour tout arrêter :

```bash
docker-compose down
```

## Configuration initiale

Avant d'importer les tableau de bord, vous devez créer une connection à la base de données depuis Grafana. Pour cela, allez dans *Administration* > *Data sources*, puis créez une source de données PostgreSQL.

Rentrez ensuite les informations suivantes (avec la configuration par défault) :

- **Host :** `host.docker.internal:5432`
- **Database :** `quality_check_data`
- **User :** `grafana_reader`
- **Password :** `grafana`
- **TLS/SSL Mode :** `disable` 

Une fois que cela à été testé et enregistré, vous pouvez [importer les tableau de bords](../docs/README.md#ajout-dun-nouveau-réseau).
