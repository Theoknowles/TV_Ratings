# app.py
import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt

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
st.title("  📺 TV Show Ratings Explorer")

# Input: Show name
show_name = st.text_input("Enter a TV show name:")

if show_name:
    try:
        # Search for the show
        search_url = f"https://api.tvmaze.com/singlesearch/shows?q={show_name}&embed=episodes"
        response = requests.get(search_url)
        response.raise_for_status()
        data = response.json()

        # Show title and summary
        st.header(data["name"])
        if data.get("image"):
            st.image(data["image"]["medium"], width=200)  # Show poster

        # Extract episodes
        episodes = data["_embedded"]["episodes"]
        df = pd.DataFrame(episodes)[["season", "number", "name", "rating"]]

        # Flatten rating dict
        df["rating"] = df["rating"].apply(lambda r: r["average"] if isinstance(r, dict) else None)

        # Show dataframe
        st.subheader("Episode Ratings")
        st.dataframe(df[["season", "number", "name", "rating"]])

        # Plot ratings by season
        st.subheader("📊 Ratings by Season")
        fig, ax = plt.subplots()
        for season, group in df.groupby("season"):
            ax.plot(group["number"], group["rating"], marker="o", label=f"Season {season}")
        ax.set_xlabel("Episode")
        ax.set_ylabel("Average Rating")
        ax.set_title(f"Ratings for {data['name']}")
        ax.legend()
        st.pyplot(fig)

        df, show_name = get_show_episodes(show_name_input)
        st.subheader(f"Episode Ratings for '{show_name}'")

        # Compute season averages
        season_avg = df.groupby('season')['rating'].mean().round(2)
        st.markdown("**Average Rating per Season:**")
        st.dataframe(season_avg)

        grid = create_rating_grid(df)
        st.markdown("**Episode Ratings Grid:**")
        
        # Color-code cells using background gradient
        st.dataframe(grid.style.background_gradient(cmap='YlGnBu', axis=None).format("{:.1f}"))

    except Exception as e:
        st.error(f"Error fetching show: {e}")

        # At the very bottom of your app.py
st.markdown(
    "<sub>Data source: TVMaze API (https://www.tvmaze.com/api)</sub>",
    unsafe_allow_html=True
)
