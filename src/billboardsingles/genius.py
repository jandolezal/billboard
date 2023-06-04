import re
import sqlite3
from typing import Dict

import requests
from bs4 import BeautifulSoup
from prefect import get_run_logger, task
from tqdm import tqdm


# TODO: Some lyrics are scraped only in part
@task
def get_lyrics(
    db_path: str, access_token: str, start_rowid: int, end_rowid: int
) -> Dict[int, str]:
    conn = sqlite3.connect(db_path)

    cur = conn.execute("SELECT rowid, artist, title FROM songs;")
    songs = cur.fetchall()

    s = requests.Session()

    all_lyrics = {}

    for rowid, artist, title in tqdm(songs[start_rowid - 1 : end_rowid]):
        base_url = "https://api.genius.com"
        headers = {"Authorization": "Bearer " + access_token}

        # Fix if one artist featuring another
        if "featuring" in artist:
            artist = artist[: artist.index(" featuring")]

        # Search for the song based on artist and title
        search_url = base_url + "/search"
        params = {"q": title + " " + artist}
        response = s.get(search_url, params=params, headers=headers)

        all_lyrics[rowid] = None

        if response.status_code == requests.codes.ok:
            data = response.json()

            # Extract the URL of the first search result
            try:
                song_url = data["response"]["hits"][0]["result"]["url"]
            except IndexError:
                continue  # for this song current logic to find url does not work

            # Scrape the lyrics from the song page
            lyrics = ""
            page = s.get(song_url)
            soup = BeautifulSoup(page.text, "html.parser")
            lyrics_div = soup.find(class_=re.compile(r"^Lyrics__Container.*"))

            if lyrics_div:
                for line in lyrics_div.stripped_strings:
                    lyrics += line + "\n"
                all_lyrics[rowid] = lyrics

    return all_lyrics


@task
def update_database(lyrics: Dict[int, str], db_path: str) -> None:
    logger = get_run_logger()

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Save lyrics to database
    for rowid, lyric in lyrics.items():
        cur.execute("UPDATE songs SET lyrics = ? WHERE rowid = ?", (lyric, rowid))

    conn.commit()

    logger.info(
        "{retrieved} songs from {total} updated with lyrics".format(
            retrieved=sum(1 if v else 0 for v in lyrics.values()), total=len(lyrics)
        )
    )

    return None
