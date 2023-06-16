import os
import re
import sqlite3

import openai
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")


def remove_square_brackets(text: str) -> str:
    pattern = r"\[.*?\]"
    result = re.sub(pattern, "", text)
    return result


def summarize_lyrics(year: int, db: str) -> None:
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    result = cur.execute(
        "select rowid, lyrics from songs where year = ? and lyrics not null", (year,)
    )
    rows = result.fetchall()

    for row in rows:
        id_ = row[0]
        lyrics = remove_square_brackets(row[1])

        prompt = f"Q: What is the main theme of this song in one word?\n\n{lyrics}\nA:"
        try:
            response = openai.Completion.create(
                model="text-davinci-003",
                prompt=prompt,
                temperature=0,
                max_tokens=100,
                top_p=1,
                frequency_penalty=0.0,
                presence_penalty=0.0,
                stop=["\n"],
            )
        except openai.error.InvalidRequestError as e:
            print(e)
            continue

        meaning = response["choices"][0]["text"].strip().lower()

        cur = conn.cursor()
        cur.execute("UPDATE songs SET meaning = ? WHERE rowid = ?", (meaning, id_))
        print(id_, meaning)
        conn.commit()


if __name__ == "__main__":
    summarize_lyrics(1980, "billboard.db")
