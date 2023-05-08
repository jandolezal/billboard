import sqlite3


def write_to_database(df, db_path):
    # Create a connection to the SQLite database
    conn = sqlite3.connect(db_path)

    # Write the DataFrame to the database
    df.to_sql("songs", conn, if_exists="replace", index=False)

    # Close the connection
    conn.close()
