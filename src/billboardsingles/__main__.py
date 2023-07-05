import os
import sys

from dotenv import load_dotenv
from prefect import flow

from .closedai import summarize_lyrics
from .genius import get_lyrics, update_database
from .wiki import BILLBOARD_WIKIPEDIA_URL, clean, save, scrape

load_dotenv()

SQLITE_DATABASE = "billboardsingles.db"


@flow
def get_hot_singles(url: str, start_year: int, end_year: int, db_path: str) -> None:
    # Scrape the Billboard Year-End Hot 100 singles from Wikipedia
    scraped_songs = scrape(url, start_year, end_year)

    # Clean and prepare for writing to database
    cleaned_songs = clean(scraped_songs)

    # Write the data to the SQLite database
    save(cleaned_songs, db_path)


@flow
def get_genius_lyrics(db_path, genius_access_token, start_rowid, end_rowid):
    # Scrape lyrics from Genius
    lyrics = get_lyrics(db_path, genius_access_token, start_rowid, end_rowid)

    # Update songs table with retrieved lyrics
    update_database(lyrics, db_path)


@flow
def get_summaries(db_path, year_from, year_to):
    for year in range(year_from, year_to + 1):
        summarize_lyrics(year, SQLITE_DATABASE)


if __name__ == "__main__":
    if sys.argv[1] == "wiki":
        get_hot_singles(BILLBOARD_WIKIPEDIA_URL, 1960, 2022, SQLITE_DATABASE)

    elif sys.argv[1] == "genius":
        try:
            start_rowid = int(sys.argv[2])
        except IndexError:
            start_rowid = 1
        try:
            end_rowid = int(sys.argv[3])
        except IndexError:
            end_rowid = None

        get_genius_lyrics(
            SQLITE_DATABASE, os.getenv("GENIUS_ACCESS_TOKEN"), start_rowid, end_rowid
        )

    elif sys.argv[1] == "openai":
        try:
            year_from = int(sys.argv[2])
            year_to = int(sys.argv[3])
        except ValueError:
            print("Select a year between 1960 and 2022")
        get_summaries(SQLITE_DATABASE, year_from, year_to)
