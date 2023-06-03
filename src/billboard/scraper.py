import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
from prefect import task


@task
def scrape_billboard():
    # Set the URL of the Wikipedia page
    url = "https://en.wikipedia.org/wiki/Billboard_Year-End_Hot_100_singles_of_"

    cols = ["year", "rank", "title", "artist"]

    # Create an empty DataFrame to store the data
    df = pd.DataFrame(columns=cols)

    # Loop over the years from 1960 to 2020
    for year in range(1960, 2023):
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
            artist = cells[2].text.strip()

            L.append([year, rank, title, artist])

        # Make a dataframe from the single year songs and concat to the whole dataframe
        df = pd.concat([df, pd.DataFrame(L, columns=cols)], ignore_index=True)

    return df


@task
def clean_billboard(df):
    cleaned_df = df.dropna(subset=["title"])

    # Fix rank (there can be value "Tie" and not a number)
    cleaned_df.loc[~cleaned_df["rank"].str.isnumeric(), "rank"] = np.nan
    cleaned_df["rank"] = cleaned_df["rank"].fillna(method="ffill").astype("int")

    # Fix song title
    cleaned_df["title"] = cleaned_df["title"].str.strip('"')

    # Fix year
    cleaned_df["year"] = cleaned_df["year"].astype("int")

    return cleaned_df
