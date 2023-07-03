# Configuration Docker Compose minimale

Ceci est un exemple de configuration Docker Compose pour déployer l'application. **A adapter selon vos besoins.**

## Instructions

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
