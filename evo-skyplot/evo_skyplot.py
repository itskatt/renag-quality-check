import asyncio
from tempfile import TemporaryDirectory
from urllib.parse import parse_qs, urlencode, urlparse, ParseResult
from datetime import datetime, timedelta
from pathlib import Path

from tqdm.asyncio import tqdm_asyncio
import aiohttp

here = Path(__file__).parent
semaphore = asyncio.Semaphore(5)


def daterange(start_date: datetime, end_date: datetime):
    out = []
    for n in range(int((end_date - start_date).days) + 1):
        out.append((start_date + timedelta(n)).strftime("%Y-%m-%d"))
    return out


async def download_image(sess: aiohttp.ClientSession, parse_res: ParseResult, query: dict, i: int, date: datetime, dest: Path):
    query["var-day"] = [date]
    url = parse_res.scheme + "://" + parse_res.netloc + parse_res.path + "?" + urlencode({k: v[0] for k, v in query.items()})
    async with semaphore:
        async with sess.get(url) as res:
            with open(dest / f"{i:04}.png", "wb") as f:
                f.write(await res.read())


async def main():
    # Est-ce qu'on a ffmpeg ?
    proc = await asyncio.create_subprocess_shell(
        "ffmpeg -version",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    stdout, _ = await proc.communicate()

    if proc.returncode != 0:
        print("FFmpeg n'est pas installé et est requis : https://ffmpeg.org/")
        return
    
    version = " ".join(stdout.decode().splitlines()[0].split()[:3])
    print(f"Nous allons utiliser {version} pour produire la vidéo")
    print()

    print("Url de la première image :")
    first = urlparse(input(">> "))
    query = dict(parse_qs(first.query))
    first_date = query["var-day"][0]
    
    print()
    print(f"La première date est {first_date}, donnez celle de fin (même format) :")
    last_date = input(">> ")

    all_dates = daterange(
        datetime.strptime(first_date, "%Y-%m-%d"),
        datetime.strptime(last_date, "%Y-%m-%d"),
    )

    with TemporaryDirectory() as tmp:
        async with aiohttp.ClientSession() as sess:
            print("Génération des images...")
            await tqdm_asyncio.gather(*[download_image(sess, first, query.copy(), i, d, Path(tmp)) for i, d in enumerate(all_dates)])

        proc = await asyncio.create_subprocess_shell(
            f"ffmpeg -y -r 10 -f image2 -i \"{tmp}/%04d.png\" -vcodec libx264 -crf 10 -pix_fmt yuv420p \"{here / 'out.mp4'}\""
        )

        await proc.communicate()


asyncio.run(main())
