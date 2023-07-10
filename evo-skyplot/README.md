# Script evo-skyplot

## Présentation

`evo-skyplot` est un script qui permet de créer des vidéos montrant l'évolution d'un graphique de skyplot en fonction du temps.

Pour chaque jour dans l'intervalle, il enregistre une photo du graphique puis les concatène en une vidéo.

## Pré-requis

Il est nécessaire que l'instance de Grafana que vous comptez utiliser possède le plugin [Grafana image renderer](https://grafana.com/grafana/plugins/grafana-image-renderer/). Si vous avez un doute, contacter votre administrateur.

## Installation

Pour installer et utiliser ce script, vous devez avoir [Python 3.7+](https://www.python.org/downloads/), [git](https://git-scm.com/) et [Ffmpeg](https://ffmpeg.org/) d'installé et de disponible dans votre PATH.

Si vous êtes sur Windows, il est conseillé d'utiliser [Scoop](https://scoop.sh/) pour installer Ffmpeg :

```powershell
scoop install main/ffmpeg
```

Attention, Anaconda peut causer des problèmes. Si cela vous arrive, utilisez la [version officielle de Python](https://www.python.org/downloads/).

Le script s'installe de la manière suivante :

```sh
pip install git+https://gitlab.oca.eu/AstroGeoGPM/renag-qc#subdirectory=evo-skyplot
```

## Utilisation

Ouvrez un terminal à l'emplacement ou vous voulez sauvegarder la vidéo, puis lancez la commande suivante :

```sh
evo-skyplot

# alternativement
python -m evo-skyplot
```

Suivez ensuite les instructions affichées.

Un tutoriel est disponible sur [Youtube](https://www.youtube.com/watch?v=w2eVqw7kh-U).

> **Notes**
> 
> - L'URL de la première image correspond au lien du rendu disponible dans le panneau de partage. Faites un clic droit sur le bouton puis copiez l'URL.
> - Avant de copier le lien, vous devez cliquer au moins une fois sur une option du menu déroulant. Le script vous avertira si vous n'avez pas fait ça.

## FAQ

**Q :** J'ai installé le script en copiant-collant la commande `pip install...` dans le terminal et ça marche pas. Qu'est-ce que je dois faire ?

**A :** Installez le script sur la version de Python que vous utilisez. Par exemple pour l'installer sur la version de Python qui est disponible en tant que `python` ajoutez `python -m` devant : ` pip install ...`. Vous lancerez ensuite le script avec `python -m evo-skyplot`.

**Q :** Après avoir donné l'url et la date j'ai une erreur incompréhensible. Qu'est-ce que je dois faire ?

**A :** N'utilisez pas Anaconda.
