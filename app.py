import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime




#
# Streamlit application for Bram's AI Newsletter
#
# Newsletter content is loaded from JSON files placed in the `content_versions` directory.
# Each JSON file contains the page title, subtitle, period, a list of top developments,
# and regional overviews. JSON files should be named according to the week
# (e.g., `week 44.json`) and reside inside a folder (e.g., `Week 44`) alongside
# their corresponding audio files. The most recently modified JSON determines the
# landing page; previous versions are selectable via the sidebar.
#
# Audio files must be present in the same folder as their JSON file with fixed names:
# - "Executive Summary.m4a"
# - "Deep Dive.m4a"
#
# Feedback from users is stored in a CSV file (`feedback.csv`) within each week's folder.
# Each entry records the newsletter item, rating, comment, and timestamp. Feedback is
# separated per week and can be downloaded as a CSV file.


# Determine base directory of this script so relative paths resolve correctly even
# when the working directory changes (e.g., when running on Streamlit Cloud).
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONTENT_DIR = os.path.join(BASE_DIR, "content_versions")


def get_available_versions() -> list[str]:
    """
    Recursively scan the `content_versions` directory for JSON files. Returns a
    list of absolute paths to JSON files sorted by modification time (most
    recent first). If the directory does not exist, it will be created.
    """
    if not os.path.isdir(CONTENT_DIR):
        os.makedirs(CONTENT_DIR, exist_ok=True)
    json_paths: list[str] = []
    for root, _, filenames in os.walk(CONTENT_DIR):
        for name in filenames:
            if name.lower().endswith(".json"):
                json_paths.append(os.path.join(root, name))
    json_paths.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return json_paths


def load_content(file_path: str | None = None):
    """
    Load newsletter content from a JSON file. If `file_path` is provided, it is
    used directly; otherwise the most recent JSON file in `content_versions`
    directory is selected. When no JSON file is available, return None to
    indicate that content is missing. JSON files should follow the structure of
    the sample provided as a separate file. To add a new edition, place a
    new JSON file named "week XX.json" into the `content_versions` folder.
    """
    # Determine which JSON file to load: use provided file_path or pick the most
    # recent file from the available versions. The get_available_versions
    # function returns absolute paths to JSON files.
    version_file: str | None = None
    if file_path:
        version_file = file_path
    else:
        versions = get_available_versions()
        if versions:
            version_file = versions[0]
    if not version_file or not os.path.isfile(version_file):
        # No JSON content found
        return None
    try:
        with open(version_file, "r", encoding="utf-8") as f:
            user_content = json.load(f)
        # Attach the base directory of this version for resolving relative audio paths
        user_content["_base_dir"] = os.path.dirname(version_file)
        return user_content
    except Exception as e:
        st.warning(f"Could not load {version_file}: {e}.")
        return None


def get_feedback_path(week_folder: str) -> str:
    """
    Get the path to the feedback CSV file for a specific week folder.
    """
    return os.path.join(week_folder, "feedback.csv")


def save_feedback(item_title: str, feedback: str, rating: str, week_folder: str):
    """
    Save feedback to a CSV file in the week's folder. Each week has its own feedback file.

    Parameters:
        item_title: The title of the item receiving feedback.
        feedback: The comment provided by the user.
        rating: The rating (thumbs up/down or other).
        week_folder: The folder path for the current week.
    """
    if not feedback.strip():
        return

    feedback_path = get_feedback_path(week_folder)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Create new feedback entry
    new_entry = pd.DataFrame([{
        "Item": item_title,
        "Rating": rating if rating else "",
        "Comment": feedback.strip(),
        "Submitted At": timestamp
    }])

    # Append to existing file or create new one
    if os.path.isfile(feedback_path):
        existing_df = pd.read_csv(feedback_path)
        updated_df = pd.concat([existing_df, new_entry], ignore_index=True)
    else:
        updated_df = new_entry

    updated_df.to_csv(feedback_path, index=False)


def load_feedback(week_folder: str) -> pd.DataFrame:
    """
    Load feedback from the CSV file in the week's folder.

    Parameters:
        week_folder: The folder path for the current week.

    Returns:
        DataFrame with feedback entries, or empty DataFrame if no feedback exists.
    """
    feedback_path = get_feedback_path(week_folder)
    if os.path.isfile(feedback_path):
        return pd.read_csv(feedback_path)
    return pd.DataFrame(columns=["Item", "Rating", "Comment", "Submitted At"])


def main():
    # Configure page
    st.set_page_config(page_title="Aviation Weekly Briefing", layout="wide")

    # Inject global CSS styles for a clean, modern look. This CSS defines a
    # centered content container, updated typography, a styled header bar,
    # section titles, podcast boxes, and paragraph formatting. These styles
    # follow the design provided by the user. The use of `unsafe_allow_html`
    # enables the custom CSS to take effect across the page.
    st.markdown(
        """
        <style>
            /* General body style */
            .block-container {
                max-width: 900px;
                margin: 0 auto;
                padding-top: 2rem;
            }

            /* Clean, modern typography */
            html, body, [class*="css"] {
                font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                line-height: 1.6;
                color: #222;
            }

            /* Header bar styling */
            .main-header {
                background-color: #004C8C;  /* Deep aviation blue */
                color: white;
                text-align: center;
                padding: 3rem 1rem;
                border-radius: 6px;
            }

            .main-header h1 {
                font-size: 2.5rem;
                margin-bottom: 0.5rem;
            }

            .main-header h3 {
                font-size: 1.2rem;
                font-weight: normal;
                color: #dbe8ff;
            }

            /* Section titles */
            h2 {
                color: #004C8C;
                border-bottom: 2px solid #004C8C;
                padding-bottom: 0.3rem;
                margin-top: 2.5rem;
            }

            /* Podcast box styling */
            .podcast-box {
                background-color: #f5f8fc;
                border: 1px solid #cfd8e0;
                border-radius: 6px;
                padding: 1.5rem;
                margin-bottom: 2rem;
            }

            .podcast-title {
                font-weight: 600;
                font-size: 1.1rem;
                color: #004C8C;
                margin-bottom: 0.5rem;
            }

            /* Article text */
            p, li {
                font-size: 1.05rem;
                text-align: justify;
            }

            ol {
                padding-left: 1.5rem;
            }
            /* Set a subtle page background for readability */
            body {
                background-color: #f7f9fb;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
    # Determine available content versions and allow the user to choose
    versions = get_available_versions()
    selected_content_file = None
    selected_label: str | None = None
    if versions:
        # Build a list of display names using the parent folder of each JSON file
        version_options: list[tuple[str, str]] = []
        for path in versions:
            # Display name uses the base filename without extension (e.g., 'Week 44 Y25')
            base = os.path.splitext(os.path.basename(path))[0]
            version_options.append((base, path))
        # Sidebar selection for available versions
        st.sidebar.markdown("### Previous Editions")
        labels = [disp for disp, _ in version_options]
        # default index 0 is the most recently modified edition
        # Use radio buttons instead of a dropdown so editions appear as a list
        selected_label = st.sidebar.radio(
            "Choose an edition to view", labels, index=0
        )
        # Find the corresponding file path for the selected label
        for disp, path in version_options:
            if disp == selected_label:
                selected_content_file = path
                break

    # Load content from the selected file (or default if none)
    content = load_content(selected_content_file)

    # If no content JSON is available, show a placeholder message
    if content is None:
        st.title("Bram's AI Newsletter")
        st.write("json file with articles missing")
        return

    # Get the base directory for the current week (for feedback storage)
    week_folder = content.get("_base_dir")

    # Header: use a custom HTML container to apply the aviation-themed styling
    # Compute values outside of the f-string to avoid backslash escapes
    header_title = content.get("title", "Bram's AI Newsletter")
    header_subtitle = content.get("subtitle", "")
    header_period = content.get("period", "")
    st.markdown(
        f"""
        <div class="main-header">
            <h1>{header_title}</h1>
            <h3>{header_subtitle}</h3>
            <p>{header_period}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Listen section: Display two podcast columns for Executive Summary and Deep Dive.
    # Audio files always have fixed names in each week folder
    base_dir = content.get("_base_dir")
    audio_files = [
        ("Executive Summary", "Executive Summary.m4a"),
        ("Deep Dive", "Deep Dive.m4a")
    ]

    st.markdown('<h2>🎧 Listen</h2>', unsafe_allow_html=True)
    cols = st.columns(len(audio_files))
    for (label, filename), col in zip(audio_files, cols):
        with col:
            # Show podcast box with title
            st.markdown(
                f'<div class="podcast-box"><div class="podcast-title">{label}</div>',
                unsafe_allow_html=True,
            )
            # Resolve audio file path relative to the JSON's base directory
            file_path = os.path.join(base_dir, filename) if base_dir else filename
            # Check if file exists and play audio
            if os.path.isfile(file_path):
                ext = os.path.splitext(file_path)[1].lower()
                mime = "audio/mp3" if ext == ".mp3" else "audio/mp4"
                with open(file_path, "rb") as af:
                    st.audio(af.read(), format=mime)
            else:
                st.warning(f"Audio file '{filename}' not found. Please upload it.")
            st.markdown('</div>', unsafe_allow_html=True)

    # Initialize feedback storage in session state
    if "feedback" not in st.session_state:
        st.session_state.feedback = {}

    st.markdown("---")
    st.markdown("## 1.0 Top Developments")
    st.markdown(
        "This week's top developments, ranked by strategic importance, illustrate the aviation industry's complex and often contradictory dynamics. "
        "Key events span critical areas from ambitious regulatory mandates and significant financial turnarounds to severe operational pressures and new strategic partnerships."
    )

    # Display each top development in full with rating and feedback form
    for idx, item in enumerate(content.get("top_developments", [])):
        title = item.get("title", f"Item {idx + 1}")
        desc = item.get("description", "")
        # Create two columns: left for article, right for interaction
        # Use a wider article column and narrower interaction column for compact layout
        article_col, interact_col = st.columns([4, 2])
        with article_col:
            # Construct bullet point with title, link icon and tags
            url = item.get("url_source")
            tags = item.get("tags", [])
            bullet = f"- **{title}**"
            if url:
                bullet += f" [🔗]({url})"
            if tags:
                # Display tags as inline code
                bullet += " " + " ".join([f"`{tag}`" for tag in tags])
            st.markdown(bullet)
            # Show description as a short summary below the bullet
            st.markdown(item.get("description", ""))
        with interact_col:
            # Initialize rating and submission state for this item if not present
            rating_key = f"rating_top_{idx}"
            submit_key = f"submitted_top_{idx}"
            if rating_key not in st.session_state:
                st.session_state[rating_key] = ""
            if submit_key not in st.session_state:
                st.session_state[submit_key] = False

            current = st.session_state[rating_key]
            up_label = "🟢👍" if current == "👍" else "👍"
            down_label = "🔴👎" if current == "👎" else "👎"
            up_col, down_col = st.columns([1, 1])
            with up_col:
                if st.button(up_label, key=f"up_btn_top_{idx}"):
                    st.session_state[rating_key] = "👍"
                    st.rerun()
            with down_col:
                if st.button(down_label, key=f"down_btn_top_{idx}"):
                    st.session_state[rating_key] = "👎"
                    st.rerun()

            rating = st.session_state[rating_key]
            # Arrange feedback input and submit checkbox horizontally
            input_col, button_col = st.columns([4, 1])
            with input_col:
                user_feedback = st.text_input(
                    label="", key=f"text_top_{idx}",
                    placeholder="Your feedback..."
                )
            with button_col:
                # Show green checkmark if already submitted, otherwise white checkbox
                if st.session_state[submit_key]:
                    st.markdown("✅", unsafe_allow_html=True)
                else:
                    if st.button("☑️", key=f"button_top_{idx}"):
                        save_feedback(title, user_feedback, rating, week_folder)
                        st.session_state.feedback[title] = user_feedback
                        st.session_state[submit_key] = True
                        st.rerun()

    # Regional overviews
    st.markdown("---")
    st.markdown("## 2.0 Regional Overviews")
    st.markdown(
        "This section provides a more granular analysis of the trends, challenges, and strategic movements shaping the aviation landscape in key geographic markets. "
        "It offers essential context beyond the global headlines, detailing the specific pressures and opportunities defining each region's trajectory."
    )
    for idx, region in enumerate(content.get("regional_overviews", [])):
        title = region.get("title", f"Region {idx + 1}")
        desc = region.get("description", "")
        # Two columns: left for region text, right for rating and feedback
        article_col, interact_col = st.columns([4, 2])
        with article_col:
            url = region.get("url_source")
            tags = region.get("tags", [])
            bullet = f"- **{title}**"
            if url:
                bullet += f" [🔗]({url})"
            if tags:
                bullet += " " + " ".join([f"`{tag}`" for tag in tags])
            st.markdown(bullet)
            st.markdown(region.get("description", ""))
        with interact_col:
            # Initialize rating and submission state for this region if not present
            rating_key = f"rating_region_{idx}"
            submit_key = f"submitted_region_{idx}"
            if rating_key not in st.session_state:
                st.session_state[rating_key] = ""
            if submit_key not in st.session_state:
                st.session_state[submit_key] = False

            current = st.session_state[rating_key]
            up_label = "🟢👍" if current == "👍" else "👍"
            down_label = "🔴👎" if current == "👎" else "👎"
            up_col, down_col = st.columns(2)
            with up_col:
                if st.button(up_label, key=f"up_btn_region_{idx}"):
                    st.session_state[rating_key] = "👍"
                    st.rerun()
            with down_col:
                if st.button(down_label, key=f"down_btn_region_{idx}"):
                    st.session_state[rating_key] = "👎"
                    st.rerun()

            rating = st.session_state[rating_key]
            input_col, button_col = st.columns([4, 1])
            with input_col:
                user_feedback = st.text_input(
                    label="", key=f"text_region_{idx}", placeholder="Your feedback..."
                )
            with button_col:
                # Show green checkmark if already submitted, otherwise white checkbox
                if st.session_state[submit_key]:
                    st.markdown("✅", unsafe_allow_html=True)
                else:
                    if st.button("☑️", key=f"button_region_{idx}"):
                        save_feedback(title, user_feedback, rating, week_folder)
                        st.session_state.feedback[title] = user_feedback
                        st.session_state[submit_key] = True
                        st.rerun()

    # Display collected feedback for the current edition
    st.markdown("---")
    st.markdown(f"## Feedback for {selected_label or 'Current Edition'}")

    # Load feedback from the week's folder
    feedback_df = load_feedback(week_folder)

    if not feedback_df.empty:
        # Display each feedback entry
        for _, row in feedback_df.iterrows():
            rating_icon = row['Rating'] if row['Rating'] else ""
            st.markdown(f"**{row['Item']}** {rating_icon} ({row['Submitted At']}): {row['Comment']}")

        # Provide a download button for feedback CSV
        csv_data = feedback_df.to_csv(index=False)
        st.download_button(
            label="Download feedback as CSV",
            data=csv_data,
            file_name=f"feedback_{selected_label or 'current'}.csv",
            mime="text/csv",
        )
    else:
        st.info("No feedback submitted yet.")


if __name__ == "__main__":
    main()