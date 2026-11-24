
import pandas as pd
from database import read_table


def overlap(a_start, a_end, b_start, b_end):

    return a_start < b_end and b_start < a_end


def validate_timetable(
    timetable,
    rooms=None,
    faculty=None,
    courses=None,
    sections=None
):

    rooms = rooms if rooms is not None else read_table("rooms")
    faculty = faculty if faculty is not None else read_table("faculty")
    courses = courses if courses is not None else read_table("courses")
    sections = sections if sections is not None else read_table("sections")

    issues = []

    if timetable.empty:

        return pd.DataFrame(
            columns=[
                "severity",
                "entry_id",
                "issue",
                "details"
            ]
        )

    room_ids = set(rooms["room_id"].astype(str))
    faculty_ids = set(faculty["faculty_id"].astype(str))
    course_ids = set(courses["course_id"].astype(str))
    section_ids = set(sections["section_id"].astype(str))

    room_capacity = dict(
        zip(rooms["room_id"], rooms["capacity"])
    )

    section_strength = dict(
        zip(sections["section_id"], sections["strength"])
    )

    df = timetable.copy()

    for col in [
        "entry_id", "day", "start_time", "end_time",
        "course_id", "faculty_id", "room_id", "section_id"
    ]:

        df[col] = df[col].astype(str).str.strip()

    # Check individual timetable entries

    for _, row in df.iterrows():

        eid = row["entry_id"]

        if row["start_time"] >= row["end_time"]:

            issues.append([
                "Error",
                eid,
                "Invalid Time Range",
                "End time must be later than start time."
            ])

        checks = [
            ("room_id", room_ids, "Unknown Room"),
            ("faculty_id", faculty_ids, "Unknown Faculty"),
            ("course_id", course_ids, "Unknown Course"),
            ("section_id", section_ids, "Unknown Section")
        ]

        for column, valid_ids, title in checks:

            if row[column] not in valid_ids:

                issues.append([
                    "Error",
                    eid,
                    title,
                    f"Invalid {column}: {row[column]}"
                ])

        # Room capacity validation

        room = row["room_id"]
        section = row["section_id"]

        if room in room_capacity and section in section_strength:

            if section_strength[section] > room_capacity[room]:

                issues.append([
                    "Warning",
                    eid,
                    "Room Capacity Exceeded",
                    f"Section strength is {section_strength[section]}, "
                    f"but room capacity is {room_capacity[room]}."
                ])

    # Check scheduling conflicts

    rows = list(df.iterrows())

    for i in range(len(rows)):

        a = rows[i][1]

        for j in range(i + 1, len(rows)):

            b = rows[j][1]

            if a["day"] != b["day"]:
                continue

            if not overlap(
                a["start_time"],
                a["end_time"],
                b["start_time"],
                b["end_time"]
            ):
                continue

            if a["room_id"] == b["room_id"]:

                issues.append([
                    "Error",
                    a["entry_id"],
                    "Room Double Booking",
                    f"Overlaps with {b['entry_id']} in room "
                    f"{a['room_id']} on {a['day']}."
                ])

            if a["faculty_id"] == b["faculty_id"]:

                issues.append([
                    "Error",
                    a["entry_id"],
                    "Faculty Conflict",
                    f"Faculty {a['faculty_id']} has overlapping classes."
                ])

            if a["section_id"] == b["section_id"]:

                issues.append([
                    "Error",
                    a["entry_id"],
                    "Section Conflict",
                    f"Section {a['section_id']} has overlapping classes."
                ])

    return pd.DataFrame(
        issues,
        columns=[
            "severity",
            "entry_id",
            "issue",
            "details"
        ]
    )
