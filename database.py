from pathlib import Path
import sqlite3
from datetime import datetime


# ============================================================
# DATABASE LOCATION
#
# Always use the aims_mock.db file located beside database.py.
# This prevents Flask and the terminal from accidentally opening
# different SQLite database files.
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
DATABASE_NAME = BASE_DIR / "aims_mock.db"


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():
    connection = sqlite3.connect(
        DATABASE_NAME,
        timeout=10
    )

    connection.row_factory = sqlite3.Row

    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    return connection


# ============================================================
# CREATE TABLES
# ============================================================

def create_tables():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS receipts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            receipt_nbr TEXT UNIQUE NOT NULL,

            status TEXT,
            receipt_date TEXT,
            vendor TEXT,

            project_slug TEXT,
            project TEXT,

            po_nbr TEXT,

            inventory_id TEXT,
            description TEXT,

            warehouse TEXT,
            acumatica_location TEXT,

            uom TEXT,

            ordered_qty INTEGER,
            open_qty INTEGER,
            receipt_qty INTEGER,

            staged_qty INTEGER DEFAULT 0,
            remaining_to_stage INTEGER DEFAULT 0,

            staging_status TEXT,

            acumatica_updated TEXT,
            aims_pulled_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS staging_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            receipt_nbr TEXT NOT NULL,

            quantity INTEGER NOT NULL,
            uom TEXT,

            location TEXT NOT NULL,

            staged_by TEXT,
            staged_at TEXT,

            FOREIGN KEY (receipt_nbr)
                REFERENCES receipts(receipt_nbr)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS storage_locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            receipt_nbr TEXT NOT NULL,

            location TEXT NOT NULL,

            quantity INTEGER DEFAULT 0,

            FOREIGN KEY (receipt_nbr)
                REFERENCES receipts(receipt_nbr)
        )
    """)

    connection.commit()
    connection.close()


# ============================================================
# SEED DEMO RECEIPTS
#
# IMPORTANT:
# INSERT OR IGNORE means existing receipt records are NOT reset.
# If you stage material and restart Flask, the staged quantities
# stored in SQLite remain unchanged.
# ============================================================

def seed_receipts():
    connection = get_connection()
    cursor = connection.cursor()

    receipts = [
        (
            "POR00004320",
            "Released",
            "09/03/2026",
            "Graybar",
            "williams-aquila",
            "Williams Aquila",
            "45001842",
            "5094-IB32",
            "Digital Input Module",
            "DROPSHIP",
            "MAIN - Primary Location",
            "EA",
            20,
            10,
            10,
            6,
            4,
            "Partially Staged",
            "09/03/2026 8:42 AM",
            "09/03/2026 8:45 AM"
        ),

        (
            "POR00004321",
            "Released",
            "09/03/2026",
            "SCP",
            "williams-aquila",
            "Williams Aquila",
            "45001857",
            "5094-IF8IH",
            "Analog Input Module",
            "DROPSHIP",
            "MAIN - Primary Location",
            "EA",
            8,
            0,
            8,
            8,
            0,
            "Fully Staged",
            "09/03/2026 9:06 AM",
            "09/03/2026 9:10 AM"
        ),

        (
            "POR00004322",
            "Released",
            "09/03/2026",
            "Reynolds",
            "williams-aquila",
            "Williams Aquila",
            "45001871",
            "1783-SFP1GLX",
            "Fiber Transceiver",
            "DROPSHIP",
            "MAIN - Primary Location",
            "EA",
            6,
            3,
            3,
            0,
            3,
            "Awaiting Staging",
            "09/03/2026 9:31 AM",
            "09/03/2026 9:35 AM"
        )
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO receipts (
            receipt_nbr,
            status,
            receipt_date,
            vendor,
            project_slug,
            project,
            po_nbr,
            inventory_id,
            description,
            warehouse,
            acumatica_location,
            uom,
            ordered_qty,
            open_qty,
            receipt_qty,
            staged_qty,
            remaining_to_stage,
            staging_status,
            acumatica_updated,
            aims_pulled_at
        )
        VALUES (
            ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?,
            ?, ?
        )
    """, receipts)

    connection.commit()
    connection.close()


# ============================================================
# SEED STORAGE LOCATION DATA
# ============================================================

def seed_storage_locations():
    connection = get_connection()
    cursor = connection.cursor()

    locations = [
        (
            "POR00004320",
            "Rack 1 / Shelf A",
            6
        ),
        (
            "POR00004321",
            "Rack 1 / Shelf B",
            8
        )
    ]

    for receipt_nbr, location, quantity in locations:

        existing = cursor.execute("""
            SELECT id
            FROM storage_locations
            WHERE receipt_nbr = ?
            AND location = ?
        """, (
            receipt_nbr,
            location
        )).fetchone()

        if not existing:

            cursor.execute("""
                INSERT INTO storage_locations (
                    receipt_nbr,
                    location,
                    quantity
                )
                VALUES (?, ?, ?)
            """, (
                receipt_nbr,
                location,
                quantity
            ))

    connection.commit()
    connection.close()


# ============================================================
# SEED STAGING HISTORY
# ============================================================

def seed_staging_history():
    connection = get_connection()
    cursor = connection.cursor()

    history = [
        (
            "POR00004320",
            6,
            "EA",
            "Rack 1 / Shelf A",
            "Myska Nasiri",
            "09/03/2026 9:58 AM"
        ),

        (
            "POR00004321",
            8,
            "EA",
            "Rack 1 / Shelf B",
            "Myska Nasiri",
            "09/03/2026 9:18 AM"
        )
    ]

    for (
        receipt_nbr,
        quantity,
        uom,
        location,
        staged_by,
        staged_at
    ) in history:

        existing = cursor.execute("""
            SELECT id
            FROM staging_history
            WHERE receipt_nbr = ?
            AND quantity = ?
            AND location = ?
            AND staged_at = ?
        """, (
            receipt_nbr,
            quantity,
            location,
            staged_at
        )).fetchone()

        if not existing:

            cursor.execute("""
                INSERT INTO staging_history (
                    receipt_nbr,
                    quantity,
                    uom,
                    location,
                    staged_by,
                    staged_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                receipt_nbr,
                quantity,
                uom,
                location,
                staged_by,
                staged_at
            ))

    connection.commit()
    connection.close()


# ============================================================
# GET RECEIPT LOCATIONS
# ============================================================

def get_receipt_locations(cursor, receipt_nbr):

    rows = cursor.execute("""
        SELECT
            location,
            quantity
        FROM storage_locations
        WHERE receipt_nbr = ?
        ORDER BY id
    """, (
        receipt_nbr,
    )).fetchall()

    locations = []

    for row in rows:

        locations.append({
            "location": row["location"],
            "quantity": row["quantity"]
        })

    return locations


# ============================================================
# GET RECEIPT STAGING HISTORY
# ============================================================

def get_receipt_history(cursor, receipt_nbr):

    rows = cursor.execute("""
        SELECT
            quantity,
            uom,
            location,
            staged_by,
            staged_at
        FROM staging_history
        WHERE receipt_nbr = ?
        ORDER BY id DESC
    """, (
        receipt_nbr,
    )).fetchall()

    history = []

    for row in rows:

        history.append({
            "quantity": row["quantity"],
            "uom": row["uom"],
            "location": row["location"],
            "user": row["staged_by"],
            "time": row["staged_at"]
        })

    return history


# ============================================================
# GET ALL RECEIPTS
#
# Used by the Materials Management page.
# ============================================================

def get_all_receipts():

    connection = get_connection()
    cursor = connection.cursor()

    receipt_rows = cursor.execute("""
        SELECT *
        FROM receipts
        ORDER BY receipt_nbr
    """).fetchall()

    receipts = []

    for row in receipt_rows:

        receipt = dict(row)

        # ----------------------------------------------------
        # TECH CENTER STORAGE LOCATIONS
        # ----------------------------------------------------

        location_rows = cursor.execute("""
            SELECT
                location,
                quantity
            FROM storage_locations
            WHERE receipt_nbr = ?
            ORDER BY id
        """, (
            receipt["receipt_nbr"],
        )).fetchall()

        locations = {}

        for location_row in location_rows:

            locations[
                location_row["location"]
            ] = location_row["quantity"]

        receipt["locations"] = locations

        # ----------------------------------------------------
        # DISPLAY LOCATION
        # ----------------------------------------------------

        if len(locations) == 0:

            receipt["storage_location"] = (
                "Not Assigned"
            )

        elif len(locations) == 1:

            receipt["storage_location"] = next(
                iter(locations)
            )

        else:

            receipt["storage_location"] = (
                "Multiple Locations"
            )

        # ----------------------------------------------------
        # STAGING HISTORY
        # ----------------------------------------------------

        history_rows = cursor.execute("""
            SELECT
                quantity,
                uom,
                location,
                staged_by,
                staged_at
            FROM staging_history
            WHERE receipt_nbr = ?
            ORDER BY id DESC
        """, (
            receipt["receipt_nbr"],
        )).fetchall()

        staging_history = []

        for history_row in history_rows:

            staging_history.append({
                "quantity":
                    history_row["quantity"],

                "uom":
                    history_row["uom"],

                "location":
                    history_row["location"],

                "user":
                    history_row["staged_by"],

                "time":
                    history_row["staged_at"]
            })

        receipt["staging_history"] = (
            staging_history
        )

        receipts.append(receipt)

    connection.close()

    return receipts


# ============================================================
# GET RECEIPTS BY PROJECT
# ============================================================

def get_receipts_by_project(project_slug):

    all_receipts = get_all_receipts()

    return [
        receipt
        for receipt in all_receipts
        if receipt["project_slug"] == project_slug
    ]


# ============================================================
# STAGE MATERIAL
#
# THIS FUNCTION WRITES DIRECTLY INTO SQLITE.
# ============================================================

def stage_receipt_material(
    receipt_nbr,
    quantity,
    location,
    staged_by="Myska Nasiri"
):

    connection = get_connection()
    cursor = connection.cursor()

    try:

        # ----------------------------------------------------
        # LOCK FOR WRITE
        # ----------------------------------------------------

        cursor.execute(
            "BEGIN IMMEDIATE"
        )

        # ----------------------------------------------------
        # GET RECEIPT FROM SQLITE
        # ----------------------------------------------------

        receipt = cursor.execute("""
            SELECT *
            FROM receipts
            WHERE receipt_nbr = ?
        """, (
            receipt_nbr,
        )).fetchone()

        if not receipt:

            connection.rollback()

            return {
                "success": False,
                "message":
                    "Receipt was not found."
            }

        # ----------------------------------------------------
        # VALIDATE LOCATION
        # ----------------------------------------------------

        if not location:

            connection.rollback()

            return {
                "success": False,
                "message":
                    "Select a Tech Center storage location."
            }

        # ----------------------------------------------------
        # VALIDATE QUANTITY
        # ----------------------------------------------------

        if quantity <= 0:

            connection.rollback()

            return {
                "success": False,
                "message":
                    "Staging quantity must be greater than zero."
            }

        current_staged_qty = (
            receipt["staged_qty"]
        )

        receipt_qty = (
            receipt["receipt_qty"]
        )

        remaining_to_stage = (
            receipt["remaining_to_stage"]
        )

        if quantity > remaining_to_stage:

            connection.rollback()

            return {
                "success": False,
                "message":
                    "Staging quantity cannot exceed "
                    "the quantity remaining from this receipt."
            }

        # ----------------------------------------------------
        # CALCULATE NEW QUANTITIES
        # ----------------------------------------------------

        new_staged_qty = (
            current_staged_qty
            + quantity
        )

        new_remaining_qty = (
            receipt_qty
            - new_staged_qty
        )

        # ----------------------------------------------------
        # DETERMINE STATUS
        # ----------------------------------------------------

        if new_remaining_qty == 0:

            new_status = "Fully Staged"

        elif new_staged_qty > 0:

            new_status = "Partially Staged"

        else:

            new_status = "Awaiting Staging"

        # ----------------------------------------------------
        # UPDATE RECEIPT
        # ----------------------------------------------------

        cursor.execute("""
            UPDATE receipts
            SET
                staged_qty = ?,
                remaining_to_stage = ?,
                staging_status = ?
            WHERE receipt_nbr = ?
        """, (
            new_staged_qty,
            new_remaining_qty,
            new_status,
            receipt_nbr
        ))

        # ----------------------------------------------------
        # UPDATE STORAGE LOCATION
        # ----------------------------------------------------

        existing_location = cursor.execute("""
            SELECT
                id,
                quantity
            FROM storage_locations
            WHERE receipt_nbr = ?
            AND location = ?
        """, (
            receipt_nbr,
            location
        )).fetchone()

        if existing_location:

            new_location_quantity = (
                existing_location["quantity"]
                + quantity
            )

            cursor.execute("""
                UPDATE storage_locations
                SET quantity = ?
                WHERE id = ?
            """, (
                new_location_quantity,
                existing_location["id"]
            ))

        else:

            cursor.execute("""
                INSERT INTO storage_locations (
                    receipt_nbr,
                    location,
                    quantity
                )
                VALUES (?, ?, ?)
            """, (
                receipt_nbr,
                location,
                quantity
            ))

        # ----------------------------------------------------
        # ADD STAGING HISTORY ENTRY
        # ----------------------------------------------------

        staging_time = datetime.now().strftime(
            "%m/%d/%Y %I:%M %p"
        )

        cursor.execute("""
            INSERT INTO staging_history (
                receipt_nbr,
                quantity,
                uom,
                location,
                staged_by,
                staged_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            receipt_nbr,
            quantity,
            receipt["uom"],
            location,
            staged_by,
            staging_time
        ))

        # ----------------------------------------------------
        # COMMIT EVERYTHING
        # ----------------------------------------------------

        connection.commit()

        # ----------------------------------------------------
        # GET UPDATED LOCATIONS
        # ----------------------------------------------------

        locations = get_receipt_locations(
            cursor,
            receipt_nbr
        )

        # ----------------------------------------------------
        # GET UPDATED HISTORY
        # ----------------------------------------------------

        history = get_receipt_history(
            cursor,
            receipt_nbr
        )

        # ----------------------------------------------------
        # DETERMINE DISPLAY LOCATION
        # ----------------------------------------------------

        if len(locations) == 0:

            storage_location = (
                "Not Assigned"
            )

        elif len(locations) == 1:

            storage_location = (
                locations[0]["location"]
            )

        else:

            storage_location = (
                "Multiple Locations"
            )

        # ----------------------------------------------------
        # RETURN UPDATED VALUES TO JAVASCRIPT
        # ----------------------------------------------------

        return {
            "success": True,

            "message":
                "Material staged successfully.",

            "receipt_nbr":
                receipt_nbr,

            "receipt_qty":
                receipt_qty,

            "staged_qty":
                new_staged_qty,

            "remaining_to_stage":
                new_remaining_qty,

            "storage_location":
                storage_location,

            "staging_status":
                new_status,

            "locations":
                locations,

            "history":
                history
        }

    except Exception as error:

        connection.rollback()

        print(
            "DATABASE STAGING ERROR:",
            error
        )

        return {
            "success": False,
            "message":
                "Unable to save staging activity."
        }

    finally:

        connection.close()


# ============================================================
# SHOW RECEIPTS IN TERMINAL
# ============================================================

def show_receipts():

    connection = get_connection()
    cursor = connection.cursor()

    receipts = cursor.execute("""
        SELECT
            receipt_nbr,
            vendor,
            inventory_id,
            receipt_qty,
            staged_qty,
            remaining_to_stage,
            staging_status
        FROM receipts
        ORDER BY receipt_nbr
    """).fetchall()

    print("\nReceipts currently stored:\n")

    for receipt in receipts:

        print(
            receipt["receipt_nbr"],
            "|",
            receipt["vendor"],
            "|",
            receipt["inventory_id"],
            "| Received:",
            receipt["receipt_qty"],
            "| Staged:",
            receipt["staged_qty"],
            "| Remaining:",
            receipt["remaining_to_stage"],
            "|",
            receipt["staging_status"]
        )

    connection.close()


# ============================================================
# INITIALIZE DATABASE
# ============================================================

def initialize_database():

    create_tables()
    seed_receipts()
    seed_storage_locations()
    seed_staging_history()


# ============================================================
# RUN DATABASE.PY DIRECTLY
# ============================================================

if __name__ == "__main__":

    initialize_database()
    show_receipts()

    print(
        "\nAIMS mock database initialized successfully."
    )