import sqlite3
import json
from pathlib import Path
from datetime import datetime


BASE_DIR = Path(__file__).resolve().parent
DATABASE_NAME = BASE_DIR / "aims_mock.db"


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():

    connection = sqlite3.connect(
        DATABASE_NAME
    )

    connection.row_factory = sqlite3.Row

    return connection


# ============================================================
# INITIALIZE REPORTING TABLE
# ============================================================

def initialize_reporting_database():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS reports (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            report_number TEXT UNIQUE NOT NULL,

            report_type TEXT NOT NULL,

            project_slug TEXT,

            project_name TEXT,

            package_name TEXT,

            status TEXT NOT NULL DEFAULT 'Draft',

            created_by TEXT,

            created_at TEXT,

            updated_at TEXT,

            submitted_at TEXT,

            completed_at TEXT,

            report_data TEXT

        )
        """
    )

    connection.commit()
    connection.close()


# ============================================================
# GENERATE REPORT NUMBER
# ============================================================

def generate_report_number(
    report_type="NCR"
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM reports
        WHERE report_type = ?
        """,
        (
            report_type,
        )
    )

    count = cursor.fetchone()[0]

    connection.close()

    next_number = count + 1

    if report_type == "NCR":

        return (
            f"NCR-{next_number:04d}"
        )

    return (
        f"RPT-{next_number:04d}"
    )


# ============================================================
# CREATE REPORT
# ============================================================

def create_report(
    report_type,
    project_slug,
    project_name,
    package_name,
    created_by="Myska Nasiri"
):

    report_number = (
        generate_report_number(
            report_type
        )
    )

    now = (
        datetime.now()
        .strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO reports (

            report_number,
            report_type,
            project_slug,
            project_name,
            package_name,
            status,
            created_by,
            created_at,
            updated_at,
            report_data

        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            report_number,
            report_type,
            project_slug,
            project_name,
            package_name,
            "Draft",
            created_by,
            now,
            now,
            json.dumps({})
        )
    )

    report_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return {
        "id": report_id,
        "report_number": report_number
    }


# ============================================================
# GET ONE REPORT
# ============================================================

def get_report(
    report_id
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM reports
        WHERE id = ?
        """,
        (
            report_id,
        )
    )

    row = cursor.fetchone()

    connection.close()

    if not row:

        return None

    report = dict(row)

    try:

        report["report_data"] = (
            json.loads(
                report.get(
                    "report_data"
                )
                or "{}"
            )
        )

    except json.JSONDecodeError:

        report["report_data"] = {}

    return report


# ============================================================
# GET ALL REPORTS
# ============================================================

def get_all_reports():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM reports
        ORDER BY id DESC
        """
    )

    rows = cursor.fetchall()

    connection.close()

    reports = []

    for row in rows:

        report = dict(row)

        try:

            report["report_data"] = (
                json.loads(
                    report.get(
                        "report_data"
                    )
                    or "{}"
                )
            )

        except json.JSONDecodeError:

            report["report_data"] = {}

        reports.append(
            report
        )

    return reports


# ============================================================
# SAVE REPORT AS DRAFT
# ============================================================

def save_report_draft(
    report_id,
    report_data
):

    now = (
        datetime.now()
        .strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE reports

        SET
            report_data = ?,
            status = ?,
            updated_at = ?

        WHERE id = ?
        """,
        (
            json.dumps(
                report_data
            ),
            "Draft",
            now,
            report_id
        )
    )

    connection.commit()
    connection.close()

    return True


# ============================================================
# SUBMIT REPORT
# ============================================================

def submit_report(
    report_id,
    report_data
):

    now = (
        datetime.now()
        .strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE reports

        SET
            report_data = ?,
            status = ?,
            updated_at = ?,
            submitted_at = ?

        WHERE id = ?
        """,
        (
            json.dumps(
                report_data
            ),
            "Submitted",
            now,
            now,
            report_id
        )
    )

    connection.commit()
    connection.close()

    return True