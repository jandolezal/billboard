"""Get list of Billboard year-end hot 100 singles from Wikipedia."""

import sqlite3

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
from prefect import get_run_logger, task
from tqdm import tqdm

BILLBOARD_WIKIPEDIA_URL = (
    "https://en.wikipedia.org/wiki/Billboard_Year-End_Hot_100_singles_of_"
)


@task
def scrape(url: str, start_year: int, end_year: int) -> pd.DataFrame:
    logger = get_run_logger()

    # Set the URL of the Wikipedia page

    cols = ["year", "rank", "title", "artist"]

    # Create an empty DataFrame to store the data
    df = pd.DataFrame(columns=cols)

    # Loop over the years
    for year in tqdm(range(start_year, end_year + 1)):
        # Make a GET request to the Wikipedia page for the current year
        response = requests.get(url + str(year))

        # Parse the HTML content of the page using BeautifulSoup
        soup = BeautifulSoup(response.content, "html.parser")

        # Find the table with class "wikitable sortable"
        table = soup.find("table", {"class": "wikitable sortable"})

        # Find all the rows in the table
        rows = table.find_all("tr")

        # Gather songs for single year in a list
        L = []

        # Loop over the rows, starting from the second row
        for i in range(1, len(rows)):
            # Find all the cells in the row
            cells = rows[i].find_all("td")

            # Extract the rank, title, and artist from the cells
            rank = cells[0].text.strip()
            title = cells[1].text.strip()
            try:
                artist = cells[2].text.strip()
            except IndexError as e:
                pass # use artist from previous iteration. likely merged table cell vertically

            L.append([year, rank, title, artist])

        # Make a dataframe from the single year songs and concat to the whole dataframe
        df = pd.concat([df, pd.DataFrame(L, columns=cols)], ignore_index=True)

    logger.info(f"Scraped years {start_year}-{end_year}")

    df["lyrics"] = pd.NA
    df["meaning"] = pd.NA

    return df


@task
def clean(df):
    cleaned_df = df.dropna(subset=["title"])

    # Fix rank (there can be value "Tie" and not a number)
    cleaned_df.loc[~cleaned_df["rank"].str.isnumeric(), "rank"] = np.nan
    cleaned_df["rank"] = cleaned_df["rank"].fillna(method="ffill").astype("int")

    # Fix song title
    cleaned_df["title"] = cleaned_df["title"].str.strip('"')

    # Fix year
    cleaned_df["year"] = cleaned_df["year"].astype("int")

    return cleaned_df


@task
def save(df, db_path):
    logger = get_run_logger()
    # Create a connection to the SQLite database
    conn = sqlite3.connect(db_path)

    # Write the DataFrame to the database
    df.to_sql("songs", conn, if_exists="replace", index=False)

    logger.info(f"{df.shape[0]} songs saved to {db_path}")

    # Close the connection
    conn.close()
