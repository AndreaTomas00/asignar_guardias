import pandas as pd
import re
import streamlit as st
import altair as alt

def parse_backtracking_log(file_path):
    """
    Parses the backtracking log file and extracts relevant information.
    """
    log_data = []
    with open(file_path, "r") as f:
        for line in f:
            # Match different log patterns
            if "Processing shift" in line:
                match = re.match(r"(.+?) - Processing shift (\d+)/(\d+): (.+?) \((.+?)\) (.+)", line)
                if match:
                    log_data.append({
                        "timestamp": match.group(1),
                        "action": "processing",
                        "shift_number": int(match.group(2)),
                        "total_shifts": int(match.group(3)),
                        "date": match.group(4),
                        "day": match.group(5),
                        "section": match.group(6),
                        "details": None
                    })
            elif "not eligible" in line:
                match = re.match(r"(.+?) -   - (.+?) not eligible: (.+)", line)
                if match:
                    log_data.append({
                        "timestamp": match.group(1),
                        "action": "not_eligible",
                        "worker": match.group(2),
                        "reason": match.group(3),
                        "details": None
                    })
            elif "ELIGIBLE WORKERS" in line:
                match = re.match(r"(.+?) - ELIGIBLE WORKERS for (.+?) on (.+?): (.+)", line)
                if match:
                    log_data.append({
                        "timestamp": match.group(1),
                        "action": "eligible_workers",
                        "section": match.group(2),
                        "date": match.group(3),
                        "eligible_workers": match.group(4).split(", "),
                        "details": None
                    })
            elif "Attempting to assign" in line:
                match = re.match(r"(.+?) - Attempting to assign (.+?) on (.+?) to (.+)", line)
                if match:
                    log_data.append({
                        "timestamp": match.group(1),
                        "action": "attempt",
                        "section": match.group(2),
                        "date": match.group(3),
                        "assigned_worker": match.group(4),
                        "details": None
                    })
            elif "SUCCESS" in line:
                match = re.match(r"(.+?) - SUCCESS: Assigned (.+?) on (.+?) to (.+)", line)
                if match:
                    log_data.append({
                        "timestamp": match.group(1),
                        "action": "success",
                        "section": match.group(2),
                        "date": match.group(3),
                        "assigned_worker": match.group(4),
                        "details": None
                    })
            elif "BACKTRACK" in line:
                match = re.match(r"(.+?) - BACKTRACK: Undoing assignment of (.+?) on (.+?) from (.+)", line)
                if match:
                    log_data.append({
                        "timestamp": match.group(1),
                        "action": "backtrack",
                        "section": match.group(2),
                        "date": match.group(3),
                        "worker": match.group(4),
                        "details": None
                    })
    return pd.DataFrame(log_data)

# Streamlit app
st.title("Backtracking Visualization")

# File input
log_file_path = st.sidebar.text_input("Enter the path to the backtracking log file:", "./data/backtracking_log_20250603_110447.txt")

if log_file_path:
    try:
        # Parse the log file
        log_df = parse_backtracking_log(log_file_path)

        # Convert timestamp to datetime
        log_df["timestamp"] = pd.to_datetime(log_df["timestamp"])

        # Sidebar filters
        st.sidebar.header("Filters")
        action_filter = st.sidebar.multiselect(
            "Select actions to display:",
            options=log_df["action"].unique(),
            default=log_df["action"].unique()
        )
        log_df_filtered = log_df[log_df["action"].isin(action_filter)]

        # Display the log as a table
        st.subheader("Backtracking Log")
        st.dataframe(log_df_filtered)

        # Create a timeline visualization
        st.subheader("Backtracking Timeline")
        timeline_chart = alt.Chart(log_df_filtered).mark_circle(size=60).encode(
            x=alt.X("timestamp:T", title="Timestamp"),
            y=alt.Y("section:N", title="Section"),
            color=alt.Color("action:N", legend=alt.Legend(title="Action")),
            tooltip=["timestamp", "section", "action", "worker", "assigned_worker", "details"]
        ).properties(
            width=800,
            height=400
        )
        st.altair_chart(timeline_chart, use_container_width=True)

    except Exception as e:
        st.error(f"Error reading or processing the log file: {e}")