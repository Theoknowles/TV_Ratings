# app.py
import streamlit as st
import pandas as pd
import requests

# -----------------------
# Helper functions
# -----------------------
def get_show_episodes(show_name):
    """Fetch episodes and ratings for a given show from TVMaze API."""
    search_url = f"http://api.tvmaze.com/singlesearch/shows?q={show_name}"
    r = requests.get(search_url)
    r.raise_for_status()
    show = r.json()
    show_id = show['id']

    episodes_url = f"http://api.tvmaze.com/shows/{show_id}/episodes"
    r = requests.get(episodes_url)
    r.raise_for_status()
    episodes = r.json()

    # Convert to DataFrame
    df = pd.DataFrame(episodes)
    df['season'] = df['season'].astype(int)
    df['episode_number'] = df['number'].astype(int)
    df['rating'] = df['rating'].apply(lambda x: x['average'] if x and x['average'] else None)
    df = df[['season', 'episode_number', 'name', 'rating']]
    return df, show['name']

def create_rating_grid(df):
    """Pivot DataFrame into a season vs episode grid."""
    grid = df.pivot(index='episode_number', columns='season', values='rating')
    return grid

# -----------------------
# Streamlit App
# -----------------------
st.title("📺 TV Show Episode Ratings by Season")

show_name_input = st.text_input("Enter a TV show name:")

if show_name_input:
    try:
        df, show_name = get_show_episodes(show_name_input)
        st.subheader(f"Episode Ratings for '{show_name}'")

        # Compute season averages
        season_avg = df.groupby('season')['rating'].mean().round(2)
        st.markdown("**Average Rating per Season:**")
        st.dataframe(season_avg)

        # Create grid
        grid = create_rating_grid(df)
        st.markdown("**Episode Ratings Grid:**")
        
        # Color-code cells using background gradient
        st.dataframe(grid.style.background_gradient(cmap='YlGnBu', axis=None).format("{:.1f}"))

    except Exception as e:
        st.error(f"Error fetching show: {e}")
