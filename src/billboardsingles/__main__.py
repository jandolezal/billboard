import os
import sys

from dotenv import load_dotenv
from prefect import flow

from .database import write_to_database
from .genius import get_lyrics, update_database
from .scraper import BILLBOARD_WIKIPEDIA_URL, clean_billboard, scrape_billboard
from .summarize import summarize_lyrics

load_dotenv()

SQLITE_DATABASE = "billboard.db"


@flow
def get_hot_singles(url: str, start_year: int, end_year: int, db_path: str) -> None:
    # Scrape the Billboard Year-End Hot 100 singles from Wikipedia
    scraped_songs = scrape_billboard(url, start_year, end_year)

    # Clean and prepare for writing to database
    cleaned_songs = clean_billboard(scraped_songs)

    # Write the data to the SQLite database
    write_to_database(cleaned_songs, db_path)


@flow
def get_genius_lyrics(db_path, genius_access_token, start_rowid, end_rowid):
    # Scrape lyrics from Genius
    lyrics = get_lyrics(db_path, genius_access_token, start_rowid, end_rowid)

    # Update songs table with retrieved lyrics
    update_database(lyrics, db_path)


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
            year = int(sys.argv[2])
            summarize_lyrics(year, SQLITE_DATABASE)
        except ValueError:
            print("Select a year between 1960 and 2022")
