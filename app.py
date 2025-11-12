import streamlit as st
import json
import os

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


def load_content():
    """Load newsletter content from a JSON file if present; otherwise, use defaults."""
    default_content = {
        "title": "Bram's AI Newsletter",
        "subtitle": "Weekly Executive Aviation Briefing",
        "period": "24 October 2025 to 3 November 2025",
        "audio_files": {
            "2‑Minute Summary": "2 min summary.m4a",
            "6‑Minute Update": "6 min update.m4a",
            "20‑Minute Deep Dive": "20 min deep dive.m4a",
        },
        "top_developments": [
            {
                "title": "Singapore Mandates SAF Procurement Through New State Entity",
                "description": (
                    "Singapore's aviation regulator is establishing a state‑owned company, SAFCo, "
                    "to centrally procure Sustainable Aviation Fuel (SAF). The program will be funded "
                    "by a new green fuel levy on all departing passengers and aims to achieve a 1% SAF "
                    "blend at Changi and Seletar airports by 2026. Citation: (5: Airport Electrification "
                    "and Sustainability/Region_Asia)."
                ),
            },
            {
                "title": "Cebu Pacific Taps European Partner for Peak Season Capacity",
                "description": (
                    "To manage high holiday travel demand, Philippine carrier Cebu Pacific has secured "
                    "two Airbus A320 aircraft from Bulgaria Air through a short‑term damp lease. "
                    "The arrangement reflects a growing trend of international collaboration to flexibly "
                    "manage seasonal capacity pressures. Citation: (4: Airport Pooling and Collaborative "
                    "Operations/Region_Asia)."
                ),
            },
            {
                "title": "U.S. Shutdown Cripples Air Travel System",
                "description": (
                    "The prolonged U.S. government shutdown is causing escalating disruption as unpaid air "
                    "traffic controllers and TSA staff strain operations, leading to significant flight delays. "
                    "Major airlines have begun providing food aid to essential workers and are warning of a "
                    "potential \"holiday travel meltdown\" if the political impasse continues. Citation: (1: "
                    "Airlines and Flight Operations/Region_Global)."
                ),
            },
            {
                "title": "IATA Issues Stricter 2026 Cargo and Ground Handling Standards",
                "description": (
                    "The International Air Transport Association (IATA) has released its updated 2026 manuals "
                    "for cargo and ground operations. The new editions include significantly stricter rules "
                    "for the air transport of lithium batteries and revised global standards for ground handling "
                    "and the transport of live animals. Citation: (5: Ground Support Equipment and Technology/Region_Global)."
                ),
            },
            {
                "title": "China's Major Airlines Achieve First Post‑Pandemic Collective Profit",
                "description": (
                    "Signaling a major turning point in the region's recovery, China’s three largest state‑owned "
                    "carriers—Air China, China Eastern, and China Southern—have posted their first collective "
                    "quarterly profit since the start of the pandemic, driven by a strong rebound in domestic travel. "
                    "Citation: (16: Airlines and Flight Operations/Region_Asia)."
                ),
            },
            {
                "title": "Portugal Secures Political Consensus for TAP Privatization",
                "description": (
                    "Portugal's government has achieved cross‑party political support for the partial privatization "
                    "of its flag carrier, TAP Air Portugal. The consensus clears the path to sell a 49.9% stake, "
                    "opening the door for formal bids from major European airline groups like Lufthansa, Air France‑KLM, "
                    "and IAG. Citation: (11: Airlines and Flight Operations/Region_Europe)."
                ),
            },
            {
                "title": "Lufthansa Insources Ground Handling at Munich Hub",
                "description": (
                    "In a strategic move to gain greater operational control and enhance reliability, Lufthansa Group "
                    "is insourcing ground handling at its Munich hub. The group has acquired a local handling company "
                    "to create Lufthansa Ground Services, which will now service its subsidiary and partner airlines "
                    "at the airport. Citation: (1: GSE Leasing and Financial Models/Region_Global)."
                ),
            },
        ],
        "regional_overviews": [
            {
                "title": "North America",
                "description": (
                    "The North American market is currently defined by a stark contrast between severe operational strain and "
                    "a determined push for innovation. A major IT failure at Alaska Airlines (link) exposed deep system "
                    "vulnerabilities, compounded by a U.S.-Mexico regulatory dispute over airport slots (link) that adds "
                    "further uncertainty. Simultaneously, proactive, tech‑driven efforts aim to improve the passenger journey "
                    "and advance sustainability, with Delta Air Lines beta‑testing an AI‑powered \"concierge\" to enhance "
                    "customer experience while Denver International Airport's fleet was recognized as the \"greenest\" in the "
                    "nation (link), demonstrating a parallel commitment to modernization."
                ),
            },
            {
                "title": "Europe",
                "description": (
                    "Europe's aviation landscape is marked by sharp contrasts, where strategic advancements contend with persistent "
                    "vulnerabilities. The financial collapse of UK regional carrier Eastern Airways (link) highlights ongoing market "
                    "fragility, even as new international services launch. Major investments aim to bolster hub efficiency, such as "
                    "Lufthansa's move to insource ground handling at its Munich hub (link), but operational integrity remains a concern, "
                    "as evidenced by a two‑hour shutdown of Berlin's airport due to an unauthorized drone sighting (link)."
                ),
            },
            {
                "title": "Asia‑Pacific",
                "description": (
                    "Sentiment in the Asia‑Pacific region is strongly optimistic, fueled by significant financial recovery, ambitious "
                    "sustainability mandates, and groundbreaking technological progress. The financial turnaround of China's major "
                    "carriers signals a firm post‑pandemic rebound, while Singapore's new state‑backed initiative to procure sustainable "
                    "aviation fuel (link) sets a new benchmark for decarbonization policy. The region is also a hub of innovation, "
                    "demonstrated by a world‑first liquid hydrogen refuelling exercise at New Zealand's Christchurch Airport (link) and "
                    "the launch of new connectivity, such as Air India's first‑ever nonstop service to Manila (link)."
                ),
            },
            {
                "title": "Middle East",
                "description": (
                    "The Middle East continues to project high optimism as long‑term strategic aviation ambitions materialize into operational "
                    "reality. The inaugural flight of Saudi Arabia's new national airline, Riyadh Air (link), marks a pivotal moment in the "
                    "Kingdom's plan to become a global aviation hub. This expansion is supported by the rapid development of a world‑class "
                    "logistics and premium service ecosystem, exemplified by a new strategic agreement between Saudi Logistics Services and "
                    "China Cargo Airlines to enhance air trade (link)."
                ),
            },
            {
                "title": "Africa",
                "description": (
                    "The African aviation market is characterized by optimistic growth, with a dominant theme of expanding international "
                    "connectivity. This expansion is being driven by both local and foreign carriers, with Nigeria's Air Peace launching a "
                    "landmark route to London Heathrow (link) and Delta Air Lines inaugurating a new nonstop service to Marrakech (link). "
                    "Concurrentlysers, the region is attracting significant foreign investment in its ground services sector, highlighted by "
                    "Turkish handler Çelebi's $40 million acquisition of a major cargo hub in Kenya (link)."
                ),
            },
        ],
    }
    # If a content.json file exists in the working directory, use it to override defaults
    if os.path.isfile("content.json"):
        try:
            with open("content.json", "r", encoding="utf-8") as f:
                user_content = json.load(f)
            # recursively update default_content with user_content
            def deep_update(d, u):
                for k, v in u.items():
                    if isinstance(v, dict):
                        d[k] = deep_update(d.get(k, {}), v)
                    else:
                        d[k] = v
                return d
            default_content = deep_update(default_content, user_content)
        except Exception as e:
            st.warning(f"Could not load content.json: {e}. Using default content.")
    return default_content


def save_feedback(item_title: str, feedback: str, filename: str = "feedback.csv"):
    """Append feedback to a CSV file."""
    # Only save non-empty feedback
    if not feedback.strip():
        return
    header_needed = not os.path.isfile(filename)
    with open(filename, "a", encoding="utf-8") as f:
        if header_needed:
            f.write("item,feedback\n")
        # Escape newlines and commas in feedback by wrapping in quotes
        feedback_sanitized = feedback.replace("\n", " ").replace("\r", " ")
        f.write(f"{item_title},\"{feedback_sanitized}\"\n")


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
    content = load_content()

    # Header
    st.title(content["title"])
    st.subheader(content["subtitle"])
    st.write(f"For the period: {content['period']}")

    # Audio players
    display_audio(content["audio_files"])

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
    for idx, item in enumerate(content["top_developments"]):
        with st.expander(item["title"], expanded=False):
            st.write(item["description"])
            form_key = f"form_top_{idx}"
            feedback_key = f"feedback_top_{idx}"
            with st.form(key=form_key):
                user_feedback = st.text_area("Your feedback:", key=feedback_key)
                submitted = st.form_submit_button("Submit Feedback")
                if submitted:
                    save_feedback(item["title"], user_feedback)
                    st.session_state.feedback[item["title"]] = user_feedback
                    st.success("Thank you for your feedback!")

    # Regional overviews
    st.markdown("---")
    st.header("Regional Overviews")
    st.write(
        "Explore the dynamics shaping each region. Click on a region below to read more and provide your feedback."
    )
    for idx, region in enumerate(content["regional_overviews"]):
        with st.expander(region["title"], expanded=False):
            st.write(region["description"])
            form_key = f"form_region_{idx}"
            feedback_key = f"feedback_region_{idx}"
            with st.form(key=form_key):
                user_feedback = st.text_area("Your feedback:", key=feedback_key)
                submitted = st.form_submit_button("Submit Feedback")
                if submitted:
                    save_feedback(region["title"], user_feedback)
                    st.session_state.feedback[region["title"]] = user_feedback
                    st.success("Thank you for your feedback!")

    # Display collected feedback (optional)
    st.markdown("---")
    st.header("Collected Feedback")
    if st.session_state.feedback:
        for item_title, feedback in st.session_state.feedback.items():
            st.markdown(f"**{item_title}**: {feedback}")
    else:
        st.info("No feedback submitted yet.")


if __name__ == "__main__":
    main()