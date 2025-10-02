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
    return df, show

def create_rating_grid(df):
    """Pivot DataFrame into a season vs episode grid."""
    grid = df.pivot(index='episode_number', columns='season', values='rating')
    return grid

# -----------------------
# Streamlit App
# -----------------------
st.title("📺 TV Show Ratings Explorer")

# Input: Show name
show_name = st.text_input("Enter a TV show name:")

if show_name:
    try:
        # Search for the show
        search_url = f"https://api.tvmaze.com/singlesearch/shows?q={show_name}&embed=episodes"
        response = requests.get(search_url)
        response.raise_for_status()
        data = response.json()

        # Extract episodes
        episodes = data["_embedded"]["episodes"]
        df = pd.DataFrame(episodes)[["season", "number", "name", "rating"]]

        # Flatten rating dict
        df["rating"] = df["rating"].apply(lambda r: r["average"] if isinstance(r, dict) else None)

        # Prepare data for grid
        df2, show_info = get_show_episodes(show_name)
        grid = create_rating_grid(df2)

        # -----------------------
        # Tabs
        # -----------------------
        tab1, tab2, tab3 = st.tabs(["ℹ️ Show Info", "📊 Ratings Chart", "🗂 Ratings Grid"])

        with tab1:
            st.header(show_info["name"])
            if show_info.get("image"):
                st.image(show_info["image"]["medium"], width=200)
            if show_info.get("summary"):
                st.markdown(show_info["summary"], unsafe_allow_html=True)
            st.markdown(f"**Genres:** {', '.join(show_info.get('genres', []))}")
            st.markdown(f"**Premiered:** {show_info.get('premiered', 'N/A')}")
            st.markdown(f"**Runtime:** {show_info.get('runtime', 'N/A')} minutes")
            st.markdown(f"**Official Site:** [{show_info.get('officialSite', 'N/A')}]({show_info.get('officialSite')})")

        with tab2:
            st.subheader("Ratings by Season")
            fig, ax = plt.subplots()
            for season, group in df.groupby("season"):
                ax.plot(group["number"], group["rating"], marker="o", label=f"Season {season}")
            ax.set_xlabel("Episode")
            ax.set_ylabel("Average Rating")
            ax.set_title(f"Ratings for {data['name']}")
            ax.legend()
            st.pyplot(fig)

        with tab3:
            st.subheader(f"Episode Ratings for '{show_info['name']}'")
            st.markdown("**Episode Ratings Grid:**")
            st.dataframe(grid.style.background_gradient(cmap='YlGn', axis=None).format("{:.1f}"))

    except Exception as e:
        st.error(f"Error fetching show: {e}")

# Footer
st.markdown(
    "<sub>Data source: TVMaze API (https://www.tvmaze.com/api)</sub>",
    unsafe_allow_html=True
)
