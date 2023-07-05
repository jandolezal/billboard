import string

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account
from wordcloud import WordCloud

# https://docs.streamlit.io/knowledge-base/tutorials/databases/bigquery
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"]
)
client = bigquery.Client(credentials=credentials)


@st.cache_data
def load_data(query):
    # https://docs.streamlit.io/knowledge-base/tutorials/databases/bigquery
    query_job = client.query(query)
    rows_raw = query_job.result()

    rows = [dict(row) for row in rows_raw]

    df = pd.DataFrame(rows).assign(
        meaning=lambda d: d["meaning"]
        .astype("string")
        .str.lower()
        .str.strip(string.punctuation),
    )

    return df


@st.cache_data
def convert_df(df):
    # https://docs.streamlit.io/library/api-reference/widgets/st.download_button
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
data = load_data(
    query="SELECT year, rank, artist, title, meaning FROM `storied-pixel-390317.billboard.songs` WHERE meaning IS NOT NULL ORDER BY year, rank;"
)


# Select a year
selected_year = st.slider(
    label="**Year**",
    min_value=int(data["year"].min()),
    max_value=int(data["year"].max()),
    step=1,
    value=2022,
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


# TOP themes for year
@st.cache_data
def get_themes_for_year(data, selected_themes):
    fig = px.bar(
        data.loc[
            (data["year"] == selected_year) & (data["meaning"].isin(selected_themes)),
            "meaning",
        ].value_counts(ascending=False),
        x="count",
        orientation="h",
        labels={"count": "Number of occurences", "meaning": "Main theme"},
    )
    return fig


@st.cache_data
def get_themes_counts_for_year(data, selected_year):
    return (
        data.loc[data["year"] == selected_year, "meaning"]
        .value_counts(ascending=False)
        .index.unique()
        .tolist()
    )


st.header("TOP themes for year")

possible_themes = get_themes_counts_for_year(data, selected_year)

selected_themes = st.multiselect(
    label="Select themes to display",
    options=possible_themes,
    default=possible_themes[:10],
    help="Choose which themes should be included in the visualisations below",
)

fig = get_themes_for_year(data, selected_themes)
st.plotly_chart(fig)


# TOP 5 themes accross years
st.header("TOP 5 themes accross years")
top5_themes = data["meaning"].value_counts(ascending=False).index[:5]

top5 = (
    data.loc[data["meaning"].isin(top5_themes), ["year", "rank", "meaning"]]
    .pivot_table(index="year", columns="meaning", aggfunc="count")
    .droplevel(0, axis=1)
    .rename_axis(columns="Main theme")
)

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
