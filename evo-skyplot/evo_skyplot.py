"""
Produit une vidéo montrant l'évolution d'un skyplot au fils du temps.
=====================================================================

MIT License

Copyright (c) 2023 Raphaël Caldwell

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import asyncio
import re
from datetime import datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import ParseResult, parse_qs, urlencode, urlparse

import aiohttp
from tqdm.asyncio import tqdm_asyncio

URL_REGEX = re.compile(
    "^https?:\\/\\/(?:www\\.)?[-a-zA-Z0-9@:%._\\+~#=]{1,256}\\.[a-zA-Z0-9()]{1,6}\\b(?:[-a-zA-Z0-9()@:%_\\+.~#?&\\/=]*)$"
)
VALID_DATE_REGEX = re.compile(r"\d{4}-\d{2}-\d{2}")

here = Path(".")
semaphore = asyncio.Semaphore(5)


def daterange(start_date: datetime, end_date: datetime):
    """
    Renvoie une liste de dates entre `start_date` et `end_date`
    """
    out = []
    for n in range(int((end_date - start_date).days) + 1):
        out.append((start_date + timedelta(n)).strftime("%Y-%m-%d"))
    return out


async def download_image(
    sess: aiohttp.ClientSession,
    parse_res: ParseResult,
    query: dict,
    i: int,
    date: datetime,
    dest: Path,
):
    """
    Télécharge une image de façon asynchrone et l'enregistre dans le dossier `dest`
    """
    query["var-day"] = [date]
    url = (
        parse_res.scheme
        + "://"
        + parse_res.netloc
        + parse_res.path
        + "?"
        + urlencode({k: v[0] for k, v in query.items()})
    )
    async with semaphore:
        async with sess.get(url) as res:
            with open(dest / f"{i:06}.png", "wb") as f:
                f.write(await res.read())


def is_first_url_valid(url: str):
    return "/render/d-solo/" in url


async def async_main():
    print(
        """
  ________      ______         _____ _  ____     _______  _      ____ _______ 
 |  ____\ \    / / __ \       / ____| |/ /\ \   / /  __ \| |    / __ \__   __|
 | |__   \ \  / / |  | |_____| (___ | ' /  \ \_/ /| |__) | |   | |  | | | |   
 |  __|   \ \/ /| |  | |______\___ \|  <    \   / |  ___/| |   | |  | | | |   
 | |____   \  / | |__| |      ____) | . \    | |  | |    | |___| |__| | | |   
 |______|   \/   \____/      |_____/|_|\_\   |_|  |_|    |______\____/  |_|   

    """
    )

    # Est-ce qu'on a ffmpeg ?
    proc = await asyncio.create_subprocess_shell(
        "ffmpeg -version",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, _ = await proc.communicate()

    if proc.returncode != 0:
        print("FFmpeg n'est pas installé et est requis : https://ffmpeg.org/")
        return

    version = " ".join(stdout.decode().splitlines()[0].split()[:3])
    print(f"Nous allons utiliser {version} pour produire la vidéo")
    print()

    # Url
    print("Url de la première image :")
    raw_url = ""
    while True:
        try:
            raw_url = input(">> ").strip()
        except EOFError:
            print()
            return

        if not is_first_url_valid(raw_url) or not URL_REGEX.fullmatch(raw_url):
            print("L'url n'est pas valide, veuillez en donner une autre.")
            print("(Cela doit être l'url du rendu de la première image).")
            continue

        first_url = urlparse(raw_url)
        query = dict(parse_qs(first_url.query))

        if "var-day" not in query:
            print("Vous devez cliquer une fois sur une des options du menu déroulant avant de copier l'url.")
            print("Veuillez réessayer une fois que vous avez fait cela :")
            continue

        break

    first_date = query["var-day"][0]
    first_date_obj = datetime.strptime(first_date, "%Y-%m-%d")

    # Date de fin
    print()
    print(f"La date de début est {first_date}, donnez celle de fin (même format) :")
    last_date = ""
    while True:
        try:
            last_date = input(">> ")
        except EOFError:
            print()
            return

        if not VALID_DATE_REGEX.fullmatch(last_date):
            print("Respectez le format de la date svp.")
            continue

        last_date_obj = datetime.strptime(last_date, "%Y-%m-%d")

        if first_date_obj > last_date_obj:
            print("La date de fin ne peut pas être antérieure à celle de début.")
            continue

        break

    all_dates = daterange(
        first_date_obj,
        last_date_obj,
    )

    # Téléchargement des images
    print()
    print(f"{len(all_dates)} images doivent être produite...")
    print()
    with TemporaryDirectory() as tmp:
        async with aiohttp.ClientSession() as sess:
            print("Génération des images...")
            await tqdm_asyncio.gather(
                *[download_image(sess, first_url, query.copy(), i, d, Path(tmp)) for i, d in enumerate(all_dates)]
            )

        print()

        video_name = f'{query["var-network"][0]}_{query["var-station"][0]}_{query["var-constellation"][0]}-from_{first_date}_to_{last_date}.mp4'

        proc = await asyncio.create_subprocess_shell(
            f'ffmpeg -y -r 10 -f image2 -i "{tmp}/%06d.png" -vcodec libx264 -crf 10 -pix_fmt yuv420p "{here / video_name}"',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        print("Création de la vidéo avec ffmpeg...")
        sdtout, stderr = await proc.communicate()

        if proc.returncode == 0:
            print(f'Fini ! La vidéo a été sauvegardé sous le nom "{video_name}" dans votre répertoire courrant.')
            return

        # Il y a eu un soucis avec ffmpeg
        print("Il y a eu un soucis avec ffmpeg :")
        print()
        print("/===========================")
        print(sdtout.decode())
        print(stderr.decode().strip())
        print("\\===========================")
        print()
        print("Il y a eu un soucis avec ffmpeg, regardez au dessus pour plus de details.")


def main():
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        print("Au revoir")
        return


if __name__ == "__main__":
    main()
