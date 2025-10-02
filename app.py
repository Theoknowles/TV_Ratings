import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt

# -----------------------
# Helper functions
# -----------------------
def get_close_matches(show_name):
    """
    Return shows with close name matches from TVMaze,
    including start and end years and show ID.
    """
    search_url = f"http://api.tvmaze.com/search/shows?q={show_name}"
    r = requests.get(search_url)
    r.raise_for_status()
    shows = r.json()

    matches = []
    for item in shows:
        show = item.get('show', {})
        if not show:
            continue

        name = show.get('name', 'Unknown')
        start = show.get('premiered')
        start_year = start[:4] if start else "N/A"
        end = show.get('ended')
        end_year = end[:4] if end else "Present"
        show_id = show.get('id')

        matches.append({
            "name": name,
            "start": start_year,
            "end": end_year,
            "id": show_id,
            "image": show.get('image', {}).get('medium'),
            "summary": show.get('summary', 'No summary available'),
            "genres": show.get('genres', []),
            "runtime": show.get('runtime')
        })

    return matches


def get_show_episodes(show_id):
    """Fetch episodes and ratings for a given show by ID from TVMaze API."""
    episodes_url = f"http://api.tvmaze.com/shows/{show_id}/episodes"
    r = requests.get(episodes_url)
    r.raise_for_status()
    episodes = r.json()

    df = pd.DataFrame(episodes)
    df['season'] = df['season'].astype(int)
    df['episode_number'] = df['number'].astype(int)
    df['rating'] = df['rating'].apply(lambda x: x['average'] if x and x['average'] else None)
    df = df[['season', 'episode_number', 'name', 'rating']]
    return df


def create_rating_grid(df):
    """Pivot DataFrame into a season vs episode grid."""
    grid = df.pivot(index='episode_number', columns='season', values='rating')
    return grid


# -----------------------
# Streamlit App
# -----------------------
st.title("📺 TV Show Ratings Explorer")

# Input: Show name
user_input = st.text_input("Enter a TV show name:")

if user_input:
    matches = get_close_matches(user_input)

    if not matches:
        st.warning("No close matches found. Please try again.")
    else:
        # Dropdown of close matches
        options = [f"{m['name']} ({m['start']}–{m['end']})" for m in matches]
        selected_index = st.selectbox("Did you mean?", range(len(options)), format_func=lambda x: options[x])
        selected_show = matches[selected_index]

        # Tabs
        tab1, tab2, tab3 = st.tabs(["ℹ️ Show Info", "📊 Ratings Chart", "🗂 Ratings Grid"])

        # Tab 1: Show Info
        with tab1:
            st.header(selected_show['name'])
            if selected_show['image']:
                st.image(selected_show['image'], width=200)
            st.write(f"**Genres:** {', '.join(selected_show['genres']) if selected_show['genres'] else 'N/A'}")
            st.write(f"**Runtime:** {selected_show['runtime']} minutes" if selected_show['runtime'] else "")
            st.markdown(selected_show['summary'], unsafe_allow_html=True)

        # Tab 2: Ratings Chart
        with tab2:
            df = get_show_episodes(selected_show['id'])
            st.subheader("Ratings by Season")
            fig, ax = plt.subplots()
            for season, group in df.groupby("season"):
                ax.plot(group["episode_number"], group["rating"], marker="o", label=f"Season {season}")
            ax.set_xlabel("Episode")
            ax.set_ylabel("Average Rating")
            ax.set_title(f"Ratings for {selected_show['name']}")
            ax.legend()
            st.pyplot(fig)

        # Tab 3: Ratings Grid
        with tab3:
            st.subheader("Episode Ratings Grid")
            grid = create_rating_grid(df)
            st.dataframe(grid.style.background_gradient(cmap='YlGn', axis=None).format("{:.1f}"))

# Footer
st.markdown(
    "<sub><i>Data source: TVMaze API (https://www.tvmaze.com/api)</i></sub>",
    unsafe_allow_html=True
)
