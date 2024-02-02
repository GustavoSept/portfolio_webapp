import pandas as pd
import sched, time
from threading import Timer
import threading
import time

# Global variable to store the data
data_store = {
    'DATA_CACHE': pd.DataFrame(columns=['Label', 'Specific Content', 'Group', 'SubGroup', 'Institution', 'Source Link', 'Time (in hours)']), 
    'UNIQUE_INSTITUTIONS': [],
    'HOURS_STUDIED': 0
}

def fetch_data():
    global DATA_CACHE
    url = 'https://docs.google.com/spreadsheets/d/17_Eq4kJ6LE4hVF-kaa6P6YOy07bukCtQuMHYcNYLjWc/export?format=csv'
    df = pd.read_csv(url)

    # deleting rows with NaN values
    df = df[df['Specific Content'].notna()]

    HOURS_STUDIED = int(df['Time (in hours)'].sum())
    UNIQUE_INSTITUTIONS = df['Institution'].unique()

    # Preprocessing the 'Label' column, to mantain divisions
    def preprocess_labels(df, column_name):
        label_counts = df[column_name].value_counts()
        
        # For labels that occur more than once, add a prefix
        for label, count in label_counts.items():
            if count > 1:
                # Filter rows with the current label
                label_rows = df[df[column_name] == label]
                
                # Generate new labels with prefixes
                new_labels = [f"{i+1}_{label}" for i in range(count)]
                
                df.loc[label_rows.index, column_name] = new_labels

        return df

    df = preprocess_labels(df, 'Label')

    data_store['DATA_CACHE'] = df
    data_store['HOURS_STUDIED'] = int(df['Time (in hours)'].sum())
    data_store['UNIQUE_INSTITUTIONS'] = df['Institution'].unique()

    print("Data updated")  # For testing purposes

def start_data_fetcher(interval=21600):  # Default interval set to 6 hours
    def fetch_periodically():
        while True:
            fetch_data()
            time.sleep(interval)

    # Start the periodic data fetching in a separate thread
    thread = threading.Thread(target=fetch_periodically)
    thread.daemon = True  # Daemonize thread
    thread.start()
