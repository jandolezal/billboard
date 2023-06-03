from prefect import flow

from .database import write_to_database
from .scraper import clean_billboard, scrape_billboard


@flow
def get_hot_singles():
    # Scrape the Billboard Year-End Hot 100 singles from Wikipedia
    scraped_songs = scrape_billboard()

    # Clean and prepare for writing to database
    cleaned_songs = clean_billboard(scraped_songs)

    # Write the data to the SQLite database
    write_to_database(cleaned_songs, "billboard.db")


if __name__ == "__main__":
    get_hot_singles()
