from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc
import sqlite3
import hashlib

from webapp.helpers.db import should_fetch_df, save_df_to_sqlite, get_data_from_sqlite

MODEL_NAME = "all-MiniLM-L6-v2"

# Helper function to assign colors based on Group and Level
def assign_color(row):
    group_colors = {
        'Software Eng & CS': (0, 0, 255),  # Blue
        'Data Eng & Science': (128, 0, 128),  # Purple
        'Math': (255, 255, 0),  # Yellow
        'Management & Self-Mastery': (64, 224, 208)  # Turquoise
    }
    level_shades = {
        'Introductory': 0.3,
        'Fundamentals': 0.6,
        'Applied': 0.9
    }
    base_color = group_colors[row['Group']]
    shade = level_shades[row['Level']]
    return f"rgb({int(base_color[0]*shade)}, {int(base_color[1]*shade)}, {int(base_color[2]*shade)})"

# TODO: generate the actual logic to cluster these
# To be efficient, we should only embed each row once, and calculate clusters on every update
def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate clusters in the data"""
    # Assign cluster based on Group
    df['cluster'] = df['Group'].astype('category').cat.codes
    
    # Generate random positions within each cluster
    df['x'] = df.apply(lambda row: np.random.normal(row['cluster'] * 5, 1), axis=1)
    df['y'] = df.apply(lambda row: np.random.normal(row['cluster'] * 5, 1), axis=1)
    
    # Assign colors
    df['color'] = df.apply(assign_color, axis=1)
    
    return df

def create_cluster_plot(df):
    fig = go.Figure()

    for group in df['Group'].unique():
        group_data = df[df['Group'] == group]
        
        fig.add_trace(go.Scatter(
            x=group_data['x'],
            y=group_data['y'],
            mode='markers',
            marker=dict(
                size=group_data['Time (in hours)'],
                sizemode='area',
                sizeref=2.*max(df['Time (in hours)'])/(40.**2),
                sizemin=4,
                color=group_data['color']
            ),
            text=group_data.apply(
                lambda row: f"<b>{row['Specific Content']}</b><br>{row['Group']}//{row['SubGroup']}<br>"
                            f"Institution: {row['Institution']}<br>Time: {row['Time (in hours)']} hours<br>"
                            f"Language: {row['Language']}<br>Level: {row['Level']}",
                axis=1
            ),
            hoverinfo='text',
            name=group,
            customdata=group_data['Source Link']
        ))

    fig.update_layout(
        title="",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        showlegend=True,
        hovermode='closest'
    )

    return fig

def get_row_hash(row):
    """Generate a hash for a row to track changes"""
    return hashlib.md5(str(row.values).encode()).hexdigest()

def get_vectorized_rows():
    """Retrieve the list of vectorized row hashes from SQLite"""
    conn = sqlite3.connect('education_journey.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS vectorized_rows
                      (row_hash TEXT PRIMARY KEY)''')
    cursor.execute("SELECT row_hash FROM vectorized_rows")
    vectorized_hashes = set(row[0] for row in cursor.fetchall())
    conn.close()
    return vectorized_hashes

def update_vectorized_rows(new_hashes):
    """Update the list of vectorized row hashes in SQLite"""
    conn = sqlite3.connect('education_journey.db')
    cursor = conn.cursor()
    cursor.executemany("INSERT OR IGNORE INTO vectorized_rows (row_hash) VALUES (?)",
                       [(hash,) for hash in new_hashes])
    conn.commit()
    conn.close()

def vectorize_and_store_data(df: pd.DataFrame, batch_size: int = 3) -> None:
    """Vectorize each row of the DataFrame and store in ChromaDB in smaller batches"""
    model = SentenceTransformer(MODEL_NAME)
    
    # Set tokenizer attribute
    if hasattr(model, 'tokenizer') and hasattr(model.tokenizer, 'clean_up_tokenization_spaces'):
        model.tokenizer.clean_up_tokenization_spaces = False
    
    chroma_client = chromadb.Client(Settings(persist_directory="./chroma_db"))
    collection = chroma_client.get_or_create_collection(name="education_journey")
    vectorized_hashes = get_vectorized_rows()
    
    new_data = []
    new_hashes = set()
    
    for idx, row in df.iterrows():
        row_hash = get_row_hash(row)
        if row_hash not in vectorized_hashes:
            document = ' '.join(row.astype(str))
            new_data.append({
                'id': str(idx),
                'document': document,
                'metadata': row.to_dict(),
                'hash': row_hash
            })
            new_hashes.add(row_hash)
    
    if new_data:
        # Process in smaller batches
        for i in range(0, len(new_data), batch_size):
            batch = new_data[i:i + batch_size]
            print(f"Processing batch {i}...")
            embeddings = model.encode([item['document'] for item in batch])
            collection.add(
                ids=[item['id'] for item in batch],
                embeddings=embeddings.tolist(),
                metadatas=[item['metadata'] for item in batch],
                documents=[item['document'] for item in batch]
            )
        
        update_vectorized_rows(new_hashes)


def similarity_search(query: str, n_results: int = 5) -> list:
    """Perform a similarity search using the vectorized data"""
    model = SentenceTransformer(MODEL_NAME)
    
    # Set tokenizer attribute
    if hasattr(model, 'tokenizer') and hasattr(model.tokenizer, 'clean_up_tokenization_spaces'):
        model.tokenizer.clean_up_tokenization_spaces = False
    
    chroma_client = chromadb.Client(Settings(persist_directory="./chroma_db"))
    collection = chroma_client.get_collection(name="education_journey")
    
    # Vectorize the query
    query_embedding = model.encode(query).tolist()
    
    # Perform the search
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )
    
    return results

def fetch_and_process_data() -> pd.DataFrame:
    url = 'https://docs.google.com/spreadsheets/d/17_Eq4kJ6LE4hVF-kaa6P6YOy07bukCtQuMHYcNYLjWc/export?format=csv'
    df = pd.read_csv(url)
    
    # Crop the DataFrame to the last valid row based on 'Label' column
    last_valid_index = df['Label'].last_valid_index()
    df = df.loc[:last_valid_index].reset_index(drop=True)
    
    # Fill NaN values in 'Group' column with a placeholder
    df['Group'] = df['Group'].fillna('Uncategorized')
    
    df = preprocess_data(df)
    save_df_to_sqlite(df)
    
    # Vectorize and store data in ChromaDB
    vectorize_and_store_data(df)
    
    return df

def dash_educational_journey(flask_app):
    dash_app = Dash(
        __name__,
        server=flask_app,
        external_stylesheets=[dbc.themes.BOOTSTRAP],
        routes_pathname_prefix="/dash/educationJourney/",
        suppress_callback_exceptions=True,
    )

    # Load and preprocess data
    if should_fetch_df():
        df = fetch_and_process_data()
    else:
        df = preprocess_data(get_data_from_sqlite(database='education_journey.db', table_name='education_journey'))
        # Ensure vectorized data is up to date
        vectorize_and_store_data(df)

    # Add error handling for empty DataFrame
    if df.empty:
        dash_app.layout = html.Div([
            html.H1("Error: No data available"),
            html.P("Please check the data source and try again.")
        ])
    else:
        dash_app.layout = html.Div([
            dcc.Graph(id='cluster-plot', figure=create_cluster_plot(df), style={'height': '90vh'}),
            html.Div(id='dummy-output', style={'display': 'none'}),
            dcc.Location(id='url', refresh=False)
        ])


        # makes each dot clickable
        dash_app.clientside_callback(
            """
            function(clickData) {
                if (clickData && clickData.points && clickData.points.length > 0) {
                    var url = clickData.points[0].customdata;
                    window.open(url, '_blank');
                }
                return null;
            }
            """,
            Output('dummy-output', 'children'),
            Input('cluster-plot', 'clickData')
        )

    return dash_app