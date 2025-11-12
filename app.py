import streamlit as st
import json
import os
import sqlite3
import pandas as pd


#
# Streamlit application for Bram's AI Newsletter
#
# Newsletter content is loaded from JSON files placed in the `content_versions` directory.
# Each JSON file follows the structure of the sample `week 44.json` and contains
# the page title, subtitle, period, a mapping of audio labels to filenames, a list
# of top developments, and regional overviews. JSON files should be named
# according to ISO week number (e.g., `week 44.json`) and reside inside a folder
# (e.g., `Week 44`) alongside their corresponding audio files. The most
# recently modified JSON determines the landing page; previous versions are
# selectable via the sidebar.
#
# Audio files must be present in the same folder as their JSON file. The keys of
# the `audio_files` mapping act as labels (for example, "Executive Summary",
# "News Update", and "Deep Dive") and the values are the filenames (e.g.,
# `Executive Summary.m4a`).
#
# Feedback from users is stored persistently in a SQLite database (`feedback.db`). Each
# entry records the newsletter item, the comment, and a timestamp, with an option
# to download all feedback as a CSV file.


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


def init_db(db_path: str = "feedback.db") -> sqlite3.Connection:
    """
    Initialize a SQLite database and return the connection. Creates the feedback
    table if it does not already exist. This database persists on the local file
    system, so feedback remains available across sessions (as long as the file
    system persists, e.g., when running locally or on a server with persistent
    storage).
    """
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_title TEXT NOT NULL,
            comment TEXT NOT NULL,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    return conn


def save_feedback(item_title: str, feedback: str, conn: sqlite3.Connection):
    """
    Persist a feedback entry into the SQLite database. Empty comments are ignored.

    Parameters:
        item_title: The title of the item receiving feedback.
        feedback: The comment provided by the user.
        conn: An open SQLite connection.
    """
    if not feedback.strip():
        return
    conn.execute(
        "INSERT INTO feedback (item_title, comment) VALUES (?, ?)",
        (item_title, feedback.strip()),
    )
    conn.commit()


def display_audio(audio_files: dict, base_dir: str | None = None):
    """
    Render audio players in columns. Each audio file path is resolved
    relative to `base_dir` if provided. Keys of the audio_files dict are
    used as labels and values are filenames.
    """
    if not audio_files:
        return
    st.markdown("## Listen")
    cols = st.columns(len(audio_files))
    for (title, file), col in zip(audio_files.items(), cols):
        with col:
            st.markdown(f"**{title}**")
            # Determine full path: if the file is not absolute and base_dir is given, join them
            file_path = file
            if base_dir and not os.path.isabs(file):
                file_path = os.path.join(base_dir, file)
            if os.path.isfile(file_path):
                # Determine mime type based on extension
                ext = os.path.splitext(file_path)[1].lower()
                mime_type = "audio/mp3" if ext == ".mp3" else "audio/mp4"
                with open(file_path, "rb") as af:
                    st.audio(af.read(), format=mime_type)
            else:
                st.warning(f"Audio file '{file_path}' not found. Upload it to the appropriate directory.")


def main():
    # Configure page
    st.set_page_config(page_title="Bram's AI Newsletter", layout="wide")
    # Determine available content versions and allow the user to choose
    versions = get_available_versions()
    selected_content_file = None
    if versions:
        # Build a list of display names using the parent folder of each JSON file
        version_options: list[tuple[str, str]] = []
        for path in versions:
            # Display name uses the immediate directory name (e.g., 'Week 44')
            dir_name = os.path.basename(os.path.dirname(path)) or os.path.basename(path)
            version_options.append((dir_name, path))
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

    # Initialize database connection for persistent feedback storage
    conn = init_db()

    # If no content JSON is available, show a placeholder message
    if content is None:
        st.title("Bram's AI Newsletter")
        st.write("json file with articles missing")
        return

    # Header
    st.title(content.get("title", "Bram's AI Newsletter"))
    st.subheader(content.get("subtitle", ""))
    st.write(f"For the period: {content.get('period', '')}")

    # Audio players
    display_audio(content.get("audio_files", {}), base_dir=content.get("_base_dir"))

    # Initialize feedback storage in session state
    if "feedback" not in st.session_state:
        st.session_state.feedback = {}

    st.markdown("---")
    st.header("Top Developments")
    st.write(
        "This week's top developments illustrate the aviation industry's complex dynamics. "
        "Below each item you can share your feedback, insights or thoughts."
    )

    # Display each top development with feedback form
    for idx, item in enumerate(content.get("top_developments", [])):
        title = item.get("title", f"Item {idx + 1}")
        desc = item.get("description", "")
        with st.expander(title, expanded=False):
            st.write(desc)
            form_key = f"form_top_{idx}"
            feedback_key = f"feedback_top_{idx}"
            with st.form(key=form_key):
                user_feedback = st.text_area("Your feedback:", key=feedback_key)
                submitted = st.form_submit_button("Submit Feedback")
                if submitted:
                    save_feedback(title, user_feedback, conn)
                    st.session_state.feedback[title] = user_feedback
                    st.success("Thank you for your feedback!")

    # Regional overviews
    st.markdown("---")
    st.header("Regional Overviews")
    st.write(
        "Explore the dynamics shaping each region. Click on a region below to read more and provide your feedback."
    )
    for idx, region in enumerate(content.get("regional_overviews", [])):
        title = region.get("title", f"Region {idx + 1}")
        desc = region.get("description", "")
        with st.expander(title, expanded=False):
            st.write(desc)
            form_key = f"form_region_{idx}"
            feedback_key = f"feedback_region_{idx}"
            with st.form(key=form_key):
                user_feedback = st.text_area("Your feedback:", key=feedback_key)
                submitted = st.form_submit_button("Submit Feedback")
                if submitted:
                    save_feedback(title, user_feedback, conn)
                    st.session_state.feedback[title] = user_feedback
                    st.success("Thank you for your feedback!")

    # Display collected feedback (optional)
    st.markdown("---")
    st.header("Collected Feedback")
    # Retrieve feedback from the database and display it
    try:
        rows = conn.execute(
            "SELECT item_title, comment, submitted_at FROM feedback ORDER BY submitted_at DESC"
        ).fetchall()
    except Exception:
        rows = []

    if rows:
        for item_title, comment, ts in rows:
            st.markdown(f"**{item_title}** ({ts}): {comment}")
        # Provide a download button for all feedback as CSV
        df_feedback = pd.DataFrame(rows, columns=["Item", "Comment", "Submitted At"])
        csv_data = df_feedback.to_csv(index=False)
        st.download_button(
            label="Download feedback as CSV",
            data=csv_data,
            file_name="feedback.csv",
            mime="text/csv",
        )
    else:
        st.info("No feedback submitted yet.")


if __name__ == "__main__":
    main()