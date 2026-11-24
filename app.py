
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

from database import (
    initialize_database,
    read_table,
    get_full_timetable,
    replace_timetable,
    save_report
)

from validation import validate_timetable


# PAGE CONFIGURATION

st.set_page_config(
    page_title="Smart University Timetable",
    page_icon="📅",
    layout="wide"
)


# CUSTOM CSS

st.markdown("""
<style>

.main {
    background-color: #f5f7fb;
}

.block-container {
    padding-top: 2rem;
}

[data-testid="stMetric"] {
    background-color: white;
    padding: 18px;
    border-radius: 12px;
    border: 1px solid #e5eaf2;
}

h1, h2, h3 {
    color: #263653;
}

</style>
""", unsafe_allow_html=True)


# INITIALIZE DATABASE

initialize_database()


# SIDEBAR

st.sidebar.title("📅 Timetable Validator")

st.sidebar.caption(
    "Smart University Scheduling System"
)

page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Timetable",
        "Validation",
        "Data Explorer"
    ]
)

st.sidebar.divider()

st.sidebar.info(
    "Python | Streamlit | SQLite"
)


# LOAD DATA

timetable = get_full_timetable()

raw_timetable = read_table("timetable")

rooms = read_table("rooms")

faculty = read_table("faculty")

courses = read_table("courses")

sections = read_table("sections")


# VALIDATION

issues = validate_timetable(
    raw_timetable,
    rooms,
    faculty,
    courses,
    sections
)


# APPLICATION HEADER

st.title(
    "Smart University Timetable & Schedule Validation"
)

st.caption(
    "Manage class schedules and identify timetable conflicts."
)


# ==================================
# DASHBOARD
# ==================================

if page == "Dashboard":

    st.subheader("Dashboard Overview")

    errors = (
        len(issues[issues["severity"] == "Error"])
        if not issues.empty else 0
    )

    warnings = (
        len(issues[issues["severity"] == "Warning"])
        if not issues.empty else 0
    )

    # METRIC CARDS

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Scheduled Classes",
        len(raw_timetable)
    )

    c2.metric(
        "Total Rooms",
        len(rooms)
    )

    c3.metric(
        "Validation Errors",
        errors
    )

    c4.metric(
        "Warnings",
        warnings
    )

    st.divider()

    # CHARTS

    left, right = st.columns(2)

    with left:

        st.subheader("Classes Per Day")

        if not raw_timetable.empty:

            day_order = [
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday"
            ]

            day_counts = (
                raw_timetable.groupby("day")
                .size()
                .reindex(day_order, fill_value=0)
                .reset_index()
            )

            day_counts.columns = ["Day", "Classes"]

            fig = px.bar(
                day_counts,
                x="Day",
                y="Classes",
                color="Classes",
                color_continuous_scale="Blues"
            )

            fig.update_layout(
                plot_bgcolor="white",
                paper_bgcolor="white"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

    with right:

        st.subheader("Validation Status")

        if issues.empty:

            st.success(
                "No timetable issues detected!"
            )

        else:

            counts = (
                issues["severity"]
                .value_counts()
                .reset_index()
            )

            counts.columns = [
                "Severity",
                "Count"
            ]

            fig = px.pie(
                counts,
                names="Severity",
                values="Count",
                hole=0.5,
                color="Severity",
                color_discrete_map={
                    "Error": "#e05b64",
                    "Warning": "#f0b44d"
                }
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

    st.divider()

    st.subheader("Recent Timetable Entries")

    st.dataframe(
        timetable.head(10),
        use_container_width=True,
        hide_index=True
    )


# ==================================
# TIMETABLE PAGE
# ==================================

elif page == "Timetable":

    st.subheader("University Timetable")

    if not timetable.empty:

        days = [
            "All",
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday"
        ]

        selected_day = st.selectbox(
            "Select Day",
            days
        )

        if selected_day == "All":

            filtered = timetable

        else:

            filtered = timetable[
                timetable["day"] == selected_day
            ]

        st.dataframe(
            filtered,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info("No timetable entries available.")

    st.divider()

    st.subheader("Import Timetable")

    st.write(
        "Upload a CSV file to replace the current timetable."
    )

    uploaded_file = st.file_uploader(
        "Upload Timetable CSV",
        type=["csv"]
    )

    if uploaded_file is not None:

        try:

            new_data = pd.read_csv(uploaded_file)

            st.write("Preview:")

            st.dataframe(
                new_data.head(),
                use_container_width=True
            )

            if st.button(
                "Import Timetable",
                type="primary"
            ):

                replace_timetable(new_data)

                st.success(
                    "Timetable imported successfully!"
                )

                st.rerun()

        except Exception as e:

            st.error(
                f"Import failed: {e}"
            )

    st.download_button(
        "Download Timetable CSV",
        raw_timetable.to_csv(index=False).encode("utf-8"),
        file_name="timetable.csv",
        mime="text/csv"
    )


# ==================================
# VALIDATION PAGE
# ==================================

elif page == "Validation":

    st.subheader("Timetable Validation")

    st.write(
        "The system checks scheduling conflicts and timetable errors."
    )

    if issues.empty:

        st.success(
            "All validation checks passed!"
        )

    else:

        errors = len(
            issues[issues["severity"] == "Error"]
        )

        warnings = len(
            issues[issues["severity"] == "Warning"]
        )

        c1, c2 = st.columns(2)

        c1.metric(
            "Total Errors",
            errors
        )

        c2.metric(
            "Total Warnings",
            warnings
        )

        selected_severity = st.multiselect(
            "Filter Issues",
            ["Error", "Warning"],
            default=["Error", "Warning"]
        )

        filtered_issues = issues[
            issues["severity"].isin(selected_severity)
        ]

        st.dataframe(
            filtered_issues,
            use_container_width=True,
            hide_index=True
        )

        st.divider()

        # DOWNLOAD REPORT

        st.download_button(
            "Download Validation Report",
            issues.to_csv(index=False).encode("utf-8"),
            file_name="validation_report.csv",
            mime="text/csv"
        )

        # SAVE REPORT

        if st.button("Save Report"):

            report_path = (
                Path(__file__).parent
                / "reports"
                / "validation_report.csv"
            )

            save_report(
                issues,
                report_path
            )

            st.success(
                "Report saved successfully!"
            )


# ==================================
# DATA EXPLORER
# ==================================

elif page == "Data Explorer":

    st.subheader("University Data Explorer")

    selected_table = st.selectbox(
        "Select Dataset",
        [
            "rooms",
            "faculty",
            "courses",
            "sections"
        ]
    )

    data = read_table(selected_table)

    st.dataframe(
        data,
        use_container_width=True,
        hide_index=True
    )

    st.download_button(
        "Download Dataset",
        data.to_csv(index=False).encode("utf-8"),
        file_name=f"{selected_table}.csv",
        mime="text/csv"
    )


# FOOTER

st.divider()

st.caption(
    "Smart University Timetable & Schedule Validation System | Mini Project"
)
