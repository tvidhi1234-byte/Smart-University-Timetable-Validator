
import sqlite3
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "timetable.db"
DATASET_DIR = BASE_DIR / "dataset"

TABLES = {
    "rooms": ["room_id", "room_name", "building", "capacity", "room_type"],
    "faculty": ["faculty_id", "faculty_name", "department", "email"],
    "courses": ["course_id", "course_name", "department", "credits"],
    "sections": ["section_id", "program", "year", "strength"],
    "timetable": [
        "entry_id", "day", "start_time", "end_time",
        "course_id", "faculty_id", "room_id", "section_id"
    ]
}


def get_connection():
    return sqlite3.connect(DB_PATH)


def initialize_database():

    with get_connection() as conn:

        conn.execute("""
        CREATE TABLE IF NOT EXISTS rooms (
            room_id TEXT PRIMARY KEY,
            room_name TEXT,
            building TEXT,
            capacity INTEGER,
            room_type TEXT
        )
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS faculty (
            faculty_id TEXT PRIMARY KEY,
            faculty_name TEXT,
            department TEXT,
            email TEXT
        )
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            course_id TEXT PRIMARY KEY,
            course_name TEXT,
            department TEXT,
            credits INTEGER
        )
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS sections (
            section_id TEXT PRIMARY KEY,
            program TEXT,
            year INTEGER,
            strength INTEGER
        )
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS timetable (
            entry_id TEXT PRIMARY KEY,
            day TEXT,
            start_time TEXT,
            end_time TEXT,
            course_id TEXT,
            faculty_id TEXT,
            room_id TEXT,
            section_id TEXT
        )
        """)

        count = conn.execute(
            "SELECT COUNT(*) FROM timetable"
        ).fetchone()[0]

        if count == 0:

            for table, columns in TABLES.items():

                file_path = DATASET_DIR / f"{table}.csv"

                if file_path.exists():

                    df = pd.read_csv(file_path)

                    df = df[columns]

                    df.to_sql(
                        table,
                        conn,
                        if_exists="append",
                        index=False
                    )


def read_table(table):

    if table not in TABLES:
        raise ValueError("Invalid table name")

    with get_connection() as conn:

        return pd.read_sql_query(
            f"SELECT * FROM {table}",
            conn
        )


def get_full_timetable():

    query = """
    SELECT
        t.entry_id,
        t.day,
        t.start_time,
        t.end_time,
        c.course_name,
        t.course_id,
        f.faculty_name,
        t.faculty_id,
        r.room_name,
        t.room_id,
        t.section_id,
        s.program,
        s.year

    FROM timetable t

    LEFT JOIN courses c
        ON t.course_id = c.course_id

    LEFT JOIN faculty f
        ON t.faculty_id = f.faculty_id

    LEFT JOIN rooms r
        ON t.room_id = r.room_id

    LEFT JOIN sections s
        ON t.section_id = s.section_id

    ORDER BY t.day, t.start_time
    """

    with get_connection() as conn:

        return pd.read_sql_query(query, conn)


def replace_timetable(df):

    columns = TABLES["timetable"]

    missing = [c for c in columns if c not in df.columns]

    if missing:
        raise ValueError(
            f"Missing columns: {missing}"
        )

    with get_connection() as conn:

        df[columns].to_sql(
            "timetable",
            conn,
            if_exists="replace",
            index=False
        )


def save_report(df, path):

    Path(path).parent.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(path, index=False)
