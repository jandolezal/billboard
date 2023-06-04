import sqlite3

from prefect import get_run_logger, task


@task
def write_to_database(df, db_path):
    logger = get_run_logger()
    # Create a connection to the SQLite database
    conn = sqlite3.connect(db_path)

    # Write the DataFrame to the database
    df.to_sql("songs", conn, if_exists="replace", index=False)

    logger.info(f"{df.shape[0]} songs saved to {db_path}")

    # Close the connection
    conn.close()
