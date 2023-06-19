import sqlite3
import string

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from wordcloud import WordCloud

SQLITE_DATABASE = "billboard.db"


@st.cache_data
def load_data(db):
    conn = sqlite3.connect(db)
    df = pd.read_sql_query(
        "SELECT year, rank, artist, title, meaning FROM songs WHERE meaning IS NOT NULL",
        conn,
    ).assign(
        meaning=lambda d: d["meaning"]
        .astype("string")
        .str.lower()
        .str.strip(string.punctuation),
    )

    return df


@st.cache_data
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv(index_label="rowid").encode("utf-8")


def create_wordcloud(text: str):
    # Generate a word cloud image
    wordcloud = WordCloud().generate(text)
    fig, ax = plt.subplots()
    ax.imshow(wordcloud)
    plt.axis("off")

    return fig


st.title("Billboard Year-End Hot 100 singles in just one word 🎙️")
st.markdown(
    """
    **What was the main theme of [Billboard Hot 100 singles](https://en.wikipedia.org/wiki/Billboard_Hot_100) across years according to *you know who's* large language model?**
    """
)


# Load data
data = load_data(SQLITE_DATABASE)


# Select a year
selected_year = st.slider(
    label="**Year**",
    min_value=int(data["year"].min()),
    max_value=int(data["year"].max()),
    step=1,
    value=1980,
    help="Select a year which interests you",
)

# Wordcloud from meanings of songs for the selected year
st.header("Main theme")
st.markdown(
    """
    Based on a prompt: *What is the main theme of this song in one word?*
    Is it really the main theme? Who knows... I don't:-)
    """
)

text = ",".join(data.loc[data["year"] == selected_year, "meaning"].values)
fig = create_wordcloud(text)

st.pyplot(fig)

st.markdown(
    """
    “Love! 🥰 No need to scrape the internet, Sherlock! I know... You just wanted a ChatGPT app like all the cool kids.”
    """
)

st.header("Hot 100 singles")

# Dataframe with 100 songs for selected year
st.dataframe(
    data[data["year"] == selected_year],
    column_config={
        "year": st.column_config.NumberColumn(
            "Year",
            format="%d",
        ),
        "rank": st.column_config.Column("Rank"),
        "artist": st.column_config.Column("Artist"),
        "title": st.column_config.Column("Title"),
        "meaning": st.column_config.Column("Main theme"),
    },
    hide_index=True,
    use_container_width=True,
)


st.header("TOP 5 themes accross years")
top5_themes = data["meaning"].value_counts(ascending=False).index[:5]

top5 = (
    data.loc[data["meaning"].isin(top5_themes), ["year", "rank", "meaning"]]
    .pivot_table(index="year", columns="meaning", aggfunc="count")
    .droplevel(0, axis=1)
    .rename_axis(columns="Main theme")
)

# st.dataframe(top5)
# st.line_chart(top5)
fig = px.line(top5, labels={"value": "Number of occurences", "year": "Year"})

st.plotly_chart(fig)

csv = convert_df(data)

st.download_button(
    label="Download data as CSV",
    data=csv,
    file_name="billboard.csv",
    mime="text/csv",
)

st.divider()

st.markdown(
    """
    Inspired by Vicky Boykis' blog [Doing small, fun projects](https://vickiboykis.com/2021/10/10/doing-small-fun-projects/).
    
    [Streamlit](https://streamlit.io/) is really cool for Python people. Discovered [Wordcloud](https://github.com/amueller/word_cloud) along the way. Should fix how I get the lyrics and try [Hugging Face](https://huggingface.co/) models.
    
    Source code is on [GitHub](https://github.com/jandolezal/billboard).
    """
)
