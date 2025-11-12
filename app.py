import streamlit as st
import json
import os
import sqlite3
import pandas as pd

"""
Streamlit application for Bram's AI Newsletter

This app displays the aviation briefing as an interactive newsletter and allows
users to provide feedback on each listed item. The text and audio references
are defined in a dictionary at the top of the script for easy editing. To
update the briefing or swap out audio files, simply modify the values in the
`CONTENT` dictionary. Audio files should be placed in the same directory as
this script when deploying to Streamlit or GitHub Pages using the Streamlit
service.

Feedback from users is stored in session state and appended to a CSV file
(`feedback.csv`) in the working directory. Each feedback entry records the
item title and the submitted comment. If you prefer another storage format
or naming convention, feel free to adjust the `save_feedback` function.
"""


CONTENT_DIR = "content_versions"


def get_available_versions() -> list:
    """
    Scan the content_versions directory for JSON files. Returns a list of file
    names sorted by modification time (most recent first). Creates the
    directory if it does not exist. The newest file will be treated as the
    default landing page content.
    """
    if not os.path.isdir(CONTENT_DIR):
        os.makedirs(CONTENT_DIR, exist_ok=True)
    files = [f for f in os.listdir(CONTENT_DIR) if f.lower().endswith(".json")]
    files.sort(key=lambda f: os.path.getmtime(os.path.join(CONTENT_DIR, f)), reverse=True)
    return files


def load_content(file_path: str | None = None):
    """
    Load newsletter content from a JSON file. If `file_path` is provided, it is
    used directly; otherwise the most recent JSON file in `content_versions`
    directory is selected. When no JSON file is available, return None to
    indicate that content is missing. JSON files should follow the structure of
    the sample provided as a separate file. To add a new edition, place a
    new JSON file named "week XX.json" into the `content_versions` folder.
    """
    version_file = None
    if file_path:
        version_file = file_path
    else:
        versions = get_available_versions()
        if versions:
            version_file = os.path.join(CONTENT_DIR, versions[0])
    if not version_file or not os.path.isfile(version_file):
        # No JSON content found
        return None
    try:
        with open(version_file, "r", encoding="utf-8") as f:
            user_content = json.load(f)
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


def display_audio(audio_files: dict):
    """Render audio players in three columns."""
    st.markdown("## Listen")
    cols = st.columns(len(audio_files))
    for (title, file), col in zip(audio_files.items(), cols):
        with col:
            st.markdown(f"**{title}**")
            if os.path.isfile(file):
                # Determine mime type based on extension
                ext = os.path.splitext(file)[1].lower()
                mime_type = "audio/mp3" if ext == ".mp3" else "audio/mp4"
                with open(file, "rb") as af:
                    st.audio(af.read(), format=mime_type)
            else:
                st.warning(f"Audio file '{file}' not found. Upload it to the app directory.")


def main():
    # Configure page
    st.set_page_config(page_title="Bram's AI Newsletter", layout="wide")
    # Determine available content versions and allow the user to choose
    versions = get_available_versions()
    selected_content_file = None
    if versions:
        # Build a list of display names using the period from each JSON file
        version_options = []
        for fname in versions:
            fpath = os.path.join(CONTENT_DIR, fname)
            display = fname
            try:
                with open(fpath, "r", encoding="utf-8") as vf:
                    vdata = json.load(vf)
                display = vdata.get("period", fname)
            except Exception:
                pass
            version_options.append((display, fname))
        # Sidebar selection for available versions
        st.sidebar.markdown("### Previous Editions")
        labels = [f"{disp}" for disp, _ in version_options]
        # default index 0 is latest
        selected_label = st.sidebar.selectbox("Choose an edition to view", labels, index=0)
        # Find the corresponding file
        for disp, fn in version_options:
            if disp == selected_label:
                selected_content_file = os.path.join(CONTENT_DIR, fn)
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
    display_audio(content.get("audio_files", {}))

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