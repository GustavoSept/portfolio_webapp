import logging
import sqlite3
from sqlite3 import Cursor
import os
from datetime import datetime, timedelta
import pandas as pd
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BASE_DIR = os.getenv('DB_BASE_DIR')

def save_df_to_sqlite(df: pd.DataFrame, table_name: str = 'education_journey'):
    logging.debug(f"education_journey > save_df_to_sqlite | running... ")
    os.makedirs(BASE_DIR, exist_ok=True)

    db_path = os.path.join(BASE_DIR, 'education_journey.db')

    with sqlite3.connect(db_path) as conn:
        df.to_sql(table_name, conn, if_exists='replace', index=False)

def get_data_from_sqlite(database: str, table_name: str) -> pd.DataFrame:
    logging.debug(f"education_journey > get_data_from_sqlite | running... ")
    BASE_DIR = os.getenv('DB_BASE_DIR')
    db_path = os.path.join(BASE_DIR, database)
    
    with sqlite3.connect(db_path) as conn:
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        
    return df

def should_fetch_df(check_every=15, database_name='education_journey.db') -> bool:
    """
    Check if the DataFrame should be reprocessed based on the last stored timestamp.

    Parameters:
    - check_every (int): Number of minutes to check between reprocesses. Default is 15 minutes.
    - database_name (str): Name of the db. Default is 'education_journey.db'.

    Returns:
    - bool: True if reprocessing is needed, otherwise False.
    """
    logging.debug(f"education_journey > should_fetch_df | running... ")
    table_name='last_processed'

    os.makedirs(BASE_DIR, exist_ok=True)

    db_path = os.path.join(BASE_DIR, database_name)

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        # Check if the table exists
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';")
        table_exists = cursor.fetchone()

        if table_exists:
            # Retrieve the last processed time from the table
            cursor.execute(f"SELECT timestamp FROM {table_name} ORDER BY id DESC LIMIT 1;")
            last_timestamp = cursor.fetchone()

            if last_timestamp:
                last_time = datetime.fromisoformat(last_timestamp[0])
                current_time = datetime.now()
                logging.info(f"education_journey > should_fetch_df | {current_time - last_time = } | {check_every = }")

                # Check if the last timestamp is more than the specified minutes ago
                if current_time - last_time > timedelta(minutes=check_every):
                    # More than 'check_every' minutes have passed
                    _update_last_processed_time(cursor, table_name)
                    logging.info(f"education_journey > should_fetch_df | returning True!")
                    return True
                else:
                    # Less than 'check_every' minutes have passed
                    logging.info(f"education_journey > should_fetch_df | returning False!")
                    return False
        else:
            # The table doesn't exist, so create it and log the current time
            _create_last_processed_table(cursor, table_name)
            _update_last_processed_time(cursor, table_name)
            logging.info(f"education_journey > should_fetch_df | returning True!")
            return True

def _create_last_processed_table(cursor: Cursor, table_name: str):
    """Create the table for storing timestamps if it doesn't exist"""
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL
        );
    """)

def _update_last_processed_time(cursor: Cursor, table_name: str):
    """Insert the current timestamp into the table"""
    current_time = datetime.now().isoformat()
    cursor.execute(f"INSERT INTO {table_name} (timestamp) VALUES (?);", (current_time,))