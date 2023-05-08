import pandas as pd

from .scraper import scrape_billboard, clean_billboard
from .database import write_to_database


def run():
    # Scrape the Billboard Year-End Hot 100 singles from Wikipedia
    df = scrape_billboard().pipe(clean_billboard)

    # Write the data to the SQLite database
    write_to_database(df, "billboard.db")


if __name__ == "__main__":
    run()
