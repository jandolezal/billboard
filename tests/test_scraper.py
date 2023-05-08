import pytest
import pandas as pd
from billboard.scraper import scrape_billboard


@pytest.mark.skip(reason="Prevent scraping wikipedia.com")
def test_scrape_billboard():
    # Call the scrape_billboard function to get the DataFrame of songs
    df = scrape_billboard()

    # Check that the DataFrame is not empty
    assert not df.empty

    # Check that the DataFrame has the expected columns
    expected_columns = ["rank", "title", "artist", "year"]
    assert set(df.columns) == set(expected_columns)

    # Check that all the years are integers between 1958 and the current year
    current_year = pd.Timestamp.now().year
    assert df["year"].between(1960, current_year).all()
