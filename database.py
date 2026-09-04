from pathlib import Path
import sqlite3
from datetime import datetime


# ============================================================
# DATABASE LOCATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
DATABASE_NAME = BASE_DIR / "aims_mock.db"


# ============================================================
# CONNECTION
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
# HELPERS
# ============================================================

def table_exists(
    cursor,
    table_name
):

    result = cursor.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        AND name = ?
        """,
        (table_name,)
    ).fetchone()

    return result is not None


def now_string():

    return datetime.now().strftime(
        "%m/%d/%Y %I:%M %p"
    )


# ============================================================
# NEW RECEIPT STRUCTURE
#
# Receipt Header
#       ↓
# Receipt Lines
#       ↓
# Locations / Staging / Movement
# ============================================================

def create_tables():

    connection = get_connection()
    cursor = connection.cursor()


    # --------------------------------------------------------
    # RECEIPT HEADERS
    # --------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS receipt_headers (

            receipt_nbr TEXT PRIMARY KEY,

            status TEXT,
            receipt_date TEXT,
            vendor TEXT,

            project_slug TEXT,
            project TEXT,

            po_nbr TEXT,

            warehouse TEXT,
            acumatica_location TEXT,

            acumatica_updated TEXT,
            aims_pulled_at TEXT,

            is_demo INTEGER DEFAULT 0
        )
        """
    )


    # --------------------------------------------------------
    # RECEIPT LINES
    # --------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS receipt_lines (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            receipt_nbr TEXT NOT NULL,

            line_nbr INTEGER NOT NULL,

            inventory_id TEXT,
            description TEXT,

            package_name TEXT,
            project_number TEXT,

            barcode TEXT,

            uom TEXT DEFAULT 'EA',

            ordered_qty INTEGER DEFAULT 0,
            open_qty INTEGER DEFAULT 0,
            receipt_qty INTEGER DEFAULT 0,

            staged_qty INTEGER DEFAULT 0,
            remaining_to_stage INTEGER DEFAULT 0,

            staging_status TEXT DEFAULT 'Awaiting Staging',

            FOREIGN KEY (receipt_nbr)
                REFERENCES receipt_headers(receipt_nbr),

            UNIQUE (
                receipt_nbr,
                line_nbr
            )
        )
        """
    )


    # --------------------------------------------------------
    # STORAGE LOCATIONS
    # --------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS material_locations (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            receipt_line_id INTEGER NOT NULL,

            location TEXT NOT NULL,

            quantity INTEGER DEFAULT 0,

            FOREIGN KEY (receipt_line_id)
                REFERENCES receipt_lines(id)
                ON DELETE CASCADE,

            UNIQUE (
                receipt_line_id,
                location
            )
        )
        """
    )


    # --------------------------------------------------------
    # STAGING HISTORY
    # --------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS line_staging_history (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            receipt_line_id INTEGER NOT NULL,

            quantity INTEGER NOT NULL,

            uom TEXT,

            location TEXT NOT NULL,

            staged_by TEXT,
            staged_at TEXT,

            notes TEXT,

            FOREIGN KEY (receipt_line_id)
                REFERENCES receipt_lines(id)
                ON DELETE CASCADE
        )
        """
    )


    # --------------------------------------------------------
    # MATERIAL MOVEMENT HISTORY
    # --------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS line_material_movements (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            receipt_line_id INTEGER NOT NULL,

            from_location TEXT,
            to_location TEXT,

            quantity INTEGER NOT NULL,

            uom TEXT,

            movement_type TEXT,

            moved_by TEXT,
            moved_at TEXT,

            notes TEXT,

            FOREIGN KEY (receipt_line_id)
                REFERENCES receipt_lines(id)
                ON DELETE CASCADE
        )
        """
    )


    connection.commit()
    connection.close()


# ============================================================
# RECEIPT HEADER SEED HELPER
# ============================================================

def add_receipt_header(
    cursor,
    receipt_nbr,
    status,
    receipt_date,
    vendor,
    project_slug,
    project,
    po_nbr,
    warehouse="DROPSHIP",
    acumatica_location="MAIN - Primary Location",
    acumatica_updated="",
    aims_pulled_at="",
    is_demo=1
):

    cursor.execute(
        """
        INSERT OR IGNORE INTO receipt_headers (

            receipt_nbr,
            status,
            receipt_date,
            vendor,

            project_slug,
            project,

            po_nbr,

            warehouse,
            acumatica_location,

            acumatica_updated,
            aims_pulled_at,

            is_demo
        )

        VALUES (
            ?, ?, ?, ?,
            ?, ?,
            ?,
            ?, ?,
            ?, ?,
            ?
        )
        """,

        (
            receipt_nbr,
            status,
            receipt_date,
            vendor,

            project_slug,
            project,

            po_nbr,

            warehouse,
            acumatica_location,

            acumatica_updated,
            aims_pulled_at,

            is_demo
        )
    )


# ============================================================
# RECEIPT LINE SEED HELPER
# ============================================================

def add_receipt_line(
    cursor,
    receipt_nbr,
    line_nbr,
    inventory_id,
    description,
    package_name,
    project_number,
    barcode,
    ordered_qty,
    open_qty,
    receipt_qty,
    staged_qty,
    staging_status,
    uom="EA"
):

    remaining_to_stage = max(
        receipt_qty - staged_qty,
        0
    )


    cursor.execute(
        """
        INSERT OR IGNORE INTO receipt_lines (

            receipt_nbr,
            line_nbr,

            inventory_id,
            description,

            package_name,
            project_number,

            barcode,

            uom,

            ordered_qty,
            open_qty,
            receipt_qty,

            staged_qty,
            remaining_to_stage,

            staging_status
        )

        VALUES (
            ?, ?,
            ?, ?,
            ?, ?,
            ?,
            ?,
            ?, ?, ?,
            ?, ?,
            ?
        )
        """,

        (
            receipt_nbr,
            line_nbr,

            inventory_id,
            description,

            package_name,
            project_number,

            barcode,

            uom,

            ordered_qty,
            open_qty,
            receipt_qty,

            staged_qty,
            remaining_to_stage,

            staging_status
        )
    )


# ============================================================
# LOCATION SEED HELPER
# ============================================================

def add_location(
    cursor,
    receipt_nbr,
    line_nbr,
    location,
    quantity
):

    line = cursor.execute(
        """
        SELECT id
        FROM receipt_lines
        WHERE receipt_nbr = ?
        AND line_nbr = ?
        """,
        (
            receipt_nbr,
            line_nbr
        )
    ).fetchone()


    if not line:
        return


    cursor.execute(
        """
        INSERT OR IGNORE INTO material_locations (
            receipt_line_id,
            location,
            quantity
        )
        VALUES (?, ?, ?)
        """,
        (
            line["id"],
            location,
            quantity
        )
    )


# ============================================================
# HISTORY SEED HELPER
# ============================================================

def add_initial_history(
    cursor,
    receipt_nbr,
    line_nbr,
    quantity,
    location,
    timestamp,
    user="Myska Nasiri",
    uom="EA",
    notes=""
):

    if quantity <= 0:
        return


    line = cursor.execute(
        """
        SELECT id
        FROM receipt_lines
        WHERE receipt_nbr = ?
        AND line_nbr = ?
        """,
        (
            receipt_nbr,
            line_nbr
        )
    ).fetchone()


    if not line:
        return


    existing = cursor.execute(
        """
        SELECT id
        FROM line_staging_history

        WHERE receipt_line_id = ?
        AND quantity = ?
        AND location = ?
        AND staged_at = ?
        """,
        (
            line["id"],
            quantity,
            location,
            timestamp
        )
    ).fetchone()


    if not existing:

        cursor.execute(
            """
            INSERT INTO line_staging_history (

                receipt_line_id,
                quantity,
                uom,

                location,

                staged_by,
                staged_at,

                notes
            )

            VALUES (
                ?, ?, ?,
                ?,
                ?, ?,
                ?
            )
            """,

            (
                line["id"],
                quantity,
                uom,

                location,

                user,
                timestamp,

                notes
            )
        )


    existing_move = cursor.execute(
        """
        SELECT id
        FROM line_material_movements

        WHERE receipt_line_id = ?
        AND from_location = ?
        AND to_location = ?
        AND quantity = ?
        AND moved_at = ?
        """,
        (
            line["id"],
            "Receiving & Staging",
            location,
            quantity,
            timestamp
        )
    ).fetchone()


    if not existing_move:

        cursor.execute(
            """
            INSERT INTO line_material_movements (

                receipt_line_id,

                from_location,
                to_location,

                quantity,
                uom,

                movement_type,

                moved_by,
                moved_at,

                notes
            )

            VALUES (
                ?,
                ?, ?,
                ?, ?,
                ?,
                ?, ?,
                ?
            )
            """,

            (
                line["id"],

                "Receiving & Staging",
                location,

                quantity,
                uom,

                "Initial Staging",

                user,
                timestamp,

                notes
            )
        )


# ============================================================
# SEED DEMO RECEIPTS
# ============================================================

def seed_demo_receipts():

    connection = get_connection()
    cursor = connection.cursor()


    # ========================================================
    # POR00004320
    #
    # WILLIAMS
    # FULLY STAGED
    # ========================================================

    add_receipt_header(
        cursor,
        "POR00004320",
        "Released",
        "09/03/2026",
        "Graybar",
        "williams-aquila",
        "Williams Aquila",
        "45001842",
        acumatica_updated=
            "09/03/2026 8:42 AM",
        aims_pulled_at=
            "09/03/2026 8:45 AM",
        is_demo=0
    )

    add_receipt_line(
        cursor,
        "POR00004320",
        1,
        "5094-IB32",
        "Digital Input Module",
        "PLC Panels",
        "031689-0001",
        "AIMS-5094-IB32-001",
        20,
        10,
        10,
        10,
        "Fully Staged"
    )

    add_location(
        cursor,
        "POR00004320",
        1,
        "Rack 1 / Shelf A",
        10
    )

    add_initial_history(
        cursor,
        "POR00004320",
        1,
        10,
        "Rack 1 / Shelf A",
        "09/03/2026 9:58 AM"
    )


    # ========================================================
    # POR00004321
    #
    # WILLIAMS
    # FULLY STAGED
    # ========================================================

    add_receipt_header(
        cursor,
        "POR00004321",
        "Released",
        "09/03/2026",
        "SCP",
        "williams-aquila",
        "Williams Aquila",
        "45001857",
        acumatica_updated=
            "09/03/2026 9:06 AM",
        aims_pulled_at=
            "09/03/2026 9:10 AM",
        is_demo=0
    )

    add_receipt_line(
        cursor,
        "POR00004321",
        1,
        "5094-IF8IH",
        "Analog Input Module",
        "PLC Panels",
        "031689-0001",
        "AIMS-5094-IF8IH-001",
        8,
        0,
        8,
        8,
        "Fully Staged"
    )

    add_location(
        cursor,
        "POR00004321",
        1,
        "Rack 1 / Shelf B",
        8
    )

    add_initial_history(
        cursor,
        "POR00004321",
        1,
        8,
        "Rack 1 / Shelf B",
        "09/03/2026 9:18 AM"
    )


    # ========================================================
    # POR00004322
    #
    # WILLIAMS
    # FRESH RECEIPT - AWAITING STAGING
    # ========================================================

    add_receipt_header(
        cursor,
        "POR00004322",
        "Released",
        "09/03/2026",
        "Reynolds",
        "williams-aquila",
        "Williams Aquila",
        "45001871",
        acumatica_updated=
            "09/03/2026 9:31 AM",
        aims_pulled_at=
            "09/03/2026 9:35 AM",
        is_demo=0
    )

    add_receipt_line(
        cursor,
        "POR00004322",
        1,
        "1783-SFP1GLX",
        "Fiber Transceiver",
        "PLC Panels",
        "031689-0001",
        "AIMS-1783-SFP1GLX-001",
        6,
        3,
        3,
        0,
        "Awaiting Staging"
    )


    # ========================================================
    # POR00004323
    #
    # WILLIAMS
    # NEW RECEIPT - AWAITING STAGING
    # ========================================================

    add_receipt_header(
        cursor,
        "POR00004323",
        "Released",
        "09/04/2026",
        "Graybar",
        "williams-aquila",
        "Williams Aquila",
        "45001883",
        acumatica_updated=
            "09/04/2026 7:41 AM",
        aims_pulled_at=
            "09/04/2026 7:45 AM"
    )

    add_receipt_line(
        cursor,
        "POR00004323",
        1,
        "5094-OB16",
        "Digital Output Module",
        "PLC Panels",
        "031689-0001",
        "AIMS-5094-OB16-001",
        20,
        0,
        20,
        0,
        "Awaiting Staging"
    )


    # ========================================================
    # POR00004324
    #
    # WILLIAMS
    # PARTIALLY STAGED
    # TWO STORAGE LOCATIONS
    # ========================================================

    add_receipt_header(
        cursor,
        "POR00004324",
        "Released",
        "09/04/2026",
        "Reynolds",
        "williams-aquila",
        "Williams Aquila",
        "45001884",
        acumatica_updated=
            "09/04/2026 8:12 AM",
        aims_pulled_at=
            "09/04/2026 8:15 AM"
    )

    add_receipt_line(
        cursor,
        "POR00004324",
        1,
        "5094-MB",
        "Mounting Base",
        "PLC Panels",
        "031689-0001",
        "AIMS-5094-MB-001",
        12,
        0,
        12,
        8,
        "Partially Staged"
    )

    add_location(
        cursor,
        "POR00004324",
        1,
        "Rack 1 / Shelf A",
        5
    )

    add_location(
        cursor,
        "POR00004324",
        1,
        "Rack 2 / Shelf A",
        3
    )

    add_initial_history(
        cursor,
        "POR00004324",
        1,
        5,
        "Rack 1 / Shelf A",
        "09/04/2026 8:30 AM"
    )

    add_initial_history(
        cursor,
        "POR00004324",
        1,
        3,
        "Rack 2 / Shelf A",
        "09/04/2026 8:35 AM"
    )


    # ========================================================
    # POR00004325
    #
    # TARGA
    # FULLY STAGED
    # ========================================================

    add_receipt_header(
        cursor,
        "POR00004325",
        "Released",
        "09/04/2026",
        "Graybar",
        "targa-butane",
        "Targa Butane",
        "45001901",
        acumatica_updated=
            "09/04/2026 8:22 AM",
        aims_pulled_at=
            "09/04/2026 8:25 AM"
    )

    add_receipt_line(
        cursor,
        "POR00004325",
        1,
        "1492-J4",
        "Terminal Block",
        "MCC Building",
        "029434-0001-EFAB",
        "AIMS-1492-J4-001",
        24,
        0,
        24,
        24,
        "Fully Staged"
    )

    add_location(
        cursor,
        "POR00004325",
        1,
        "Rack 2 / Shelf A",
        24
    )

    add_initial_history(
        cursor,
        "POR00004325",
        1,
        24,
        "Rack 2 / Shelf A",
        "09/04/2026 8:52 AM"
    )


    # ========================================================
    # POR00004326
    #
    # BP KASKIDA
    # PARTIAL DELIVERY EXAMPLE
    #
    # ORDERED: 20
    # ACTUALLY RECEIVED: 10
    #
    # ONLY THE 10 RECEIVED UNITS MAY BE STAGED.
    # ========================================================

    add_receipt_header(
        cursor,
        "POR00004326",
        "Released",
        "09/04/2026",
        "Summit",
        "bp-kaskida",
        "BP Kaskida",
        "45001912",
        acumatica_updated=
            "09/04/2026 9:02 AM",
        aims_pulled_at=
            "09/04/2026 9:05 AM"
    )

    add_receipt_line(
        cursor,
        "POR00004326",
        1,
        "AB-1769-PA4",
        "CompactLogix Power Supply",
        "Phase 1 Stage 2 Chem-Inject / IJB",
        "028710-0001-EFAB",
        "AIMS-BP-1769-PA4-001",
        20,
        10,
        10,
        4,
        "Partially Staged"
    )

    add_location(
        cursor,
        "POR00004326",
        1,
        "Rack 2 / Shelf B",
        4
    )

    add_initial_history(
        cursor,
        "POR00004326",
        1,
        4,
        "Rack 2 / Shelf B",
        "09/04/2026 9:18 AM"
    )


    # ========================================================
    # POR00004327
    #
    # SLB
    # SOME MATERIAL ALREADY MOVED TO ASSEMBLY FLOOR
    # ========================================================

    add_receipt_header(
        cursor,
        "POR00004327",
        "Released",
        "09/04/2026",
        "AWC",
        "slb-hpu-skids",
        "SLB HPU Skids",
        "45001918",
        acumatica_updated=
            "09/04/2026 9:30 AM",
        aims_pulled_at=
            "09/04/2026 9:33 AM"
    )

    add_receipt_line(
        cursor,
        "POR00004327",
        1,
        "SCE-24EL2008LP",
        "Electrical Enclosure",
        "HPU Skids",
        "027682-0003",
        "AIMS-SLB-SCE-001",
        6,
        0,
        6,
        6,
        "Fully Staged"
    )

    add_location(
        cursor,
        "POR00004327",
        1,
        "Rack 3 / Shelf A",
        2
    )

    add_location(
        cursor,
        "POR00004327",
        1,
        "Assembly Floor",
        4
    )

    add_initial_history(
        cursor,
        "POR00004327",
        1,
        6,
        "Rack 3 / Shelf A",
        "09/04/2026 9:42 AM"
    )


    # Add demonstration movement from rack to assembly floor.

    slb_line = cursor.execute(
        """
        SELECT id
        FROM receipt_lines
        WHERE receipt_nbr = ?
        AND line_nbr = ?
        """,
        (
            "POR00004327",
            1
        )
    ).fetchone()


    if slb_line:

        existing = cursor.execute(
            """
            SELECT id
            FROM line_material_movements

            WHERE receipt_line_id = ?
            AND from_location = ?
            AND to_location = ?
            AND quantity = ?
            """,
            (
                slb_line["id"],
                "Rack 3 / Shelf A",
                "Assembly Floor",
                4
            )
        ).fetchone()


        if not existing:

            cursor.execute(
                """
                INSERT INTO line_material_movements (

                    receipt_line_id,

                    from_location,
                    to_location,

                    quantity,
                    uom,

                    movement_type,

                    moved_by,
                    moved_at,

                    notes
                )

                VALUES (
                    ?,
                    ?, ?,
                    ?, ?,
                    ?,
                    ?, ?,
                    ?
                )
                """,

                (
                    slb_line["id"],

                    "Rack 3 / Shelf A",
                    "Assembly Floor",

                    4,
                    "EA",

                    "Material Move",

                    "Myska Nasiri",
                    "09/04/2026 10:15 AM",

                    "Released to HPU skid assembly."
                )
            )


    # ========================================================
    # POR00004328
    #
    # VENTURE GLOBAL
    # FULLY STAGED ACROSS TWO LOCATIONS
    # ========================================================

    add_receipt_header(
        cursor,
        "POR00004328",
        "Released",
        "09/04/2026",
        "Graybar",
        "venture-global",
        "Venture Global",
        "45001924",
        acumatica_updated=
            "09/04/2026 10:02 AM",
        aims_pulled_at=
            "09/04/2026 10:05 AM"
    )

    add_receipt_line(
        cursor,
        "POR00004328",
        1,
        "VG-HIPS-CTRL",
        "HIPS Control Component",
        "HIPS",
        "030458-0001",
        "AIMS-VG-HIPS-CTRL-001",
        16,
        0,
        16,
        16,
        "Fully Staged"
    )

    add_location(
        cursor,
        "POR00004328",
        1,
        "Rack 3 / Shelf A",
        8
    )

    add_location(
        cursor,
        "POR00004328",
        1,
        "Rack 3 / Shelf B",
        8
    )

    add_initial_history(
        cursor,
        "POR00004328",
        1,
        8,
        "Rack 3 / Shelf A",
        "09/04/2026 10:20 AM"
    )

    add_initial_history(
        cursor,
        "POR00004328",
        1,
        8,
        "Rack 3 / Shelf B",
        "09/04/2026 10:24 AM"
    )


    # ========================================================
    # POR00004329
    #
    # DRONE IN THE BOX
    # FRESH / UNSTAGED
    # ========================================================

    add_receipt_header(
        cursor,
        "POR00004329",
        "Released",
        "09/04/2026",
        "Industrial Networking",
        "drone-in-the-box",
        "Drone in the Box",
        "45001931",
        acumatica_updated=
            "09/04/2026 10:42 AM",
        aims_pulled_at=
            "09/04/2026 10:45 AM"
    )

    add_receipt_line(
        cursor,
        "POR00004329",
        1,
        "1783-ETAP",
        "EtherNet/IP Tap",
        "Drone Enclosure",
        "030443-0003-EFAB",
        "AIMS-DB-1783-ETAP-001",
        4,
        0,
        4,
        0,
        "Awaiting Staging"
    )


    # ========================================================
    # POR00004330
    #
    # ⭐ MULTI-PART RECEIPT DEMO
    #
    # ONE RECEIPT
    # FOUR DIFFERENT MATERIAL LINES
    # ========================================================

    add_receipt_header(
        cursor,
        "POR00004330",
        "Released",
        "09/04/2026",
        "Graybar",
        "williams-aquila",
        "Williams Aquila",
        "45001940",
        acumatica_updated=
            "09/04/2026 11:14 AM",
        aims_pulled_at=
            "09/04/2026 11:17 AM"
    )


    # LINE 1
    # Fully staged

    add_receipt_line(
        cursor,
        "POR00004330",
        1,
        "5094-IB32",
        "Digital Input Module",
        "PLC Panels",
        "031689-0001",
        "AIMS-5094-IB32-04330",
        12,
        0,
        12,
        12,
        "Fully Staged"
    )

    add_location(
        cursor,
        "POR00004330",
        1,
        "Rack 1 / Shelf A",
        12
    )

    add_initial_history(
        cursor,
        "POR00004330",
        1,
        12,
        "Rack 1 / Shelf A",
        "09/04/2026 11:32 AM"
    )


    # LINE 2
    # Partially staged

    add_receipt_line(
        cursor,
        "POR00004330",
        2,
        "5094-OB16",
        "Digital Output Module",
        "PLC Panels",
        "031689-0001",
        "AIMS-5094-OB16-04330",
        8,
        0,
        8,
        4,
        "Partially Staged"
    )

    add_location(
        cursor,
        "POR00004330",
        2,
        "Rack 1 / Shelf B",
        4
    )

    add_initial_history(
        cursor,
        "POR00004330",
        2,
        4,
        "Rack 1 / Shelf B",
        "09/04/2026 11:35 AM"
    )


    # LINE 3
    # Not staged yet

    add_receipt_line(
        cursor,
        "POR00004330",
        3,
        "5094-IF8IH",
        "Analog Input Module",
        "PLC Panels",
        "031689-0001",
        "AIMS-5094-IF8IH-04330",
        4,
        0,
        4,
        0,
        "Awaiting Staging"
    )


    # LINE 4
    # Fully staged

    add_receipt_line(
        cursor,
        "POR00004330",
        4,
        "1783-SFP1GLX",
        "Fiber Transceiver",
        "PLC Panels",
        "031689-0001",
        "AIMS-1783-SFP1GLX-04330",
        6,
        0,
        6,
        6,
        "Fully Staged"
    )

    add_location(
        cursor,
        "POR00004330",
        4,
        "Rack 2 / Shelf A",
        6
    )

    add_initial_history(
        cursor,
        "POR00004330",
        4,
        6,
        "Rack 2 / Shelf A",
        "09/04/2026 11:40 AM"
    )


    # ========================================================
    # POR00004331
    #
    # MULTI-PART TARGA RECEIPT
    #
    # SECOND EXAMPLE SO MULTI-LINE DOESN'T LOOK LIKE
    # A ONE-OFF SPECIAL CASE.
    # ========================================================

    add_receipt_header(
        cursor,
        "POR00004331",
        "Released",
        "09/04/2026",
        "Graybar",
        "targa-butane",
        "Targa Butane",
        "45001945",
        acumatica_updated=
            "09/04/2026 11:46 AM",
        aims_pulled_at=
            "09/04/2026 11:49 AM"
    )


    add_receipt_line(
        cursor,
        "POR00004331",
        1,
        "1492-J4",
        "Terminal Block",
        "MCC Building",
        "029434-0001-EFAB",
        "AIMS-TB-1492-J4-04331",
        30,
        0,
        30,
        0,
        "Awaiting Staging"
    )


    add_receipt_line(
        cursor,
        "POR00004331",
        2,
        "1492-EBJ3",
        "End Barrier",
        "MCC Building",
        "029434-0001-EFAB",
        "AIMS-TB-1492-EBJ3-04331",
        10,
        0,
        10,
        0,
        "Awaiting Staging"
    )


    add_receipt_line(
        cursor,
        "POR00004331",
        3,
        "1492-EAJ35",
        "End Anchor",
        "MCC Building",
        "029434-0001-EFAB",
        "AIMS-TB-1492-EAJ35-04331",
        10,
        0,
        10,
        0,
        "Awaiting Staging"
    )


    connection.commit()
    connection.close()


# ============================================================
# GET LOCATIONS FOR ONE RECEIPT LINE
# ============================================================

def get_line_locations(
    cursor,
    receipt_line_id
):

    rows = cursor.execute(
        """
        SELECT
            location,
            quantity

        FROM material_locations

        WHERE receipt_line_id = ?
        AND quantity > 0

        ORDER BY location
        """,
        (receipt_line_id,)
    ).fetchall()


    return [
        {
            "location":
                row["location"],

            "quantity":
                row["quantity"]
        }

        for row in rows
    ]


# ============================================================
# GET STAGING HISTORY FOR ONE LINE
# ============================================================

def get_line_staging_history(
    cursor,
    receipt_line_id
):

    rows = cursor.execute(
        """
        SELECT
            quantity,
            uom,
            location,
            staged_by,
            staged_at,
            notes

        FROM line_staging_history

        WHERE receipt_line_id = ?

        ORDER BY id
        """,
        (receipt_line_id,)
    ).fetchall()


    return [
        {
            "quantity":
                row["quantity"],

            "uom":
                row["uom"],

            "location":
                row["location"],

            "user":
                row["staged_by"],

            "time":
                row["staged_at"],

            "notes":
                row["notes"]
        }

        for row in rows
    ]


# ============================================================
# GET MOVEMENT HISTORY
# ============================================================

def get_material_movement_history(
    cursor,
    receipt_line_id
):

    rows = cursor.execute(
        """
        SELECT
            from_location,
            to_location,

            quantity,
            uom,

            movement_type,

            moved_by,
            moved_at,

            notes

        FROM line_material_movements

        WHERE receipt_line_id = ?

        ORDER BY id DESC
        """,
        (receipt_line_id,)
    ).fetchall()


    return [
        {
            "from_location":
                row["from_location"],

            "to_location":
                row["to_location"],

            "quantity":
                row["quantity"],

            "uom":
                row["uom"],

            "movement_type":
                row["movement_type"],

            "moved_by":
                row["moved_by"],

            "moved_at":
                row["moved_at"],

            "notes":
                row["notes"]
        }

        for row in rows
    ]


# ============================================================
# DISPLAY LOCATION HELPER
# ============================================================

def get_display_location(
    locations
):

    if not locations:

        return "Not Assigned"


    if len(locations) == 1:

        return locations[0]["location"]


    return "Multiple Locations"


# ============================================================
# FLATTEN RECEIPT LINE
#
# This lets the existing Flask templates continue to receive
# familiar fields while also gaining receipt_line_id.
# ============================================================

def build_line_record(
    cursor,
    row
):

    locations = get_line_locations(
        cursor,
        row["line_id"]
    )


    staging_history = (
        get_line_staging_history(
            cursor,
            row["line_id"]
        )
    )


    return {

        "receipt_line_id":
            row["line_id"],

        "line_nbr":
            row["line_nbr"],


        "receipt_nbr":
            row["receipt_nbr"],

        "status":
            row["status"],

        "receipt_date":
            row["receipt_date"],

        "vendor":
            row["vendor"],


        "project_slug":
            row["project_slug"],

        "project":
            row["project"],


        "po_nbr":
            row["po_nbr"],


        "inventory_id":
            row["inventory_id"],

        "description":
            row["description"],


        "package_name":
            row["package_name"],

        "project_number":
            row["project_number"],


        "barcode":
            row["barcode"],


        "warehouse":
            row["warehouse"],

        "acumatica_location":
            row["acumatica_location"],


        "uom":
            row["uom"],


        "ordered_qty":
            row["ordered_qty"],

        "open_qty":
            row["open_qty"],

        "receipt_qty":
            row["receipt_qty"],


        "staged_qty":
            row["staged_qty"],

        "remaining_to_stage":
            row["remaining_to_stage"],


        "staging_status":
            row["staging_status"],


        "storage_location":
            get_display_location(
                locations
            ),


        "locations":
            {
                item["location"]:
                    item["quantity"]

                for item in locations
            },


        "location_list":
            locations,


        "staging_history":
            staging_history,


        "acumatica_updated":
            row["acumatica_updated"],

        "aims_pulled_at":
            row["aims_pulled_at"],


        "is_demo":
            bool(
                row["is_demo"]
            )
    }


# ============================================================
# BASE RECEIPT LINE QUERY
# ============================================================

RECEIPT_LINE_QUERY = """
    SELECT

        l.id AS line_id,
        l.line_nbr,

        h.receipt_nbr,
        h.status,
        h.receipt_date,
        h.vendor,

        h.project_slug,
        h.project,

        h.po_nbr,

        l.inventory_id,
        l.description,

        l.package_name,
        l.project_number,

        l.barcode,

        h.warehouse,
        h.acumatica_location,

        l.uom,

        l.ordered_qty,
        l.open_qty,
        l.receipt_qty,

        l.staged_qty,
        l.remaining_to_stage,

        l.staging_status,

        h.acumatica_updated,
        h.aims_pulled_at,

        h.is_demo

    FROM receipt_lines l

    JOIN receipt_headers h
        ON h.receipt_nbr =
           l.receipt_nbr
"""


# ============================================================
# GET ALL RECEIPT LINES
# ============================================================

def get_all_receipts():

    connection = get_connection()
    cursor = connection.cursor()


    rows = cursor.execute(
        RECEIPT_LINE_QUERY +
        """
        ORDER BY
            h.receipt_date DESC,
            h.receipt_nbr DESC,
            l.line_nbr
        """
    ).fetchall()


    result = [

        build_line_record(
            cursor,
            row
        )

        for row in rows
    ]


    connection.close()

    return result


# ============================================================
# GET RECEIPTS GROUPED BY RECEIPT
#
# This is what we'll use for the upgraded Receiving & Staging
# UI in the next step.
# ============================================================

def get_receipt_groups():

    connection = get_connection()
    cursor = connection.cursor()


    headers = cursor.execute(
        """
        SELECT *
        FROM receipt_headers
        ORDER BY
            receipt_date DESC,
            receipt_nbr DESC
        """
    ).fetchall()


    groups = []


    for header in headers:

        line_rows = cursor.execute(
            RECEIPT_LINE_QUERY +
            """
            WHERE h.receipt_nbr = ?

            ORDER BY l.line_nbr
            """,
            (
                header["receipt_nbr"],
            )
        ).fetchall()


        lines = [

            build_line_record(
                cursor,
                row
            )

            for row in line_rows
        ]


        if not lines:
            continue


        total_receipt_qty = sum(
            line["receipt_qty"]
            for line in lines
        )


        total_staged_qty = sum(
            line["staged_qty"]
            for line in lines
        )


        total_remaining = sum(
            line["remaining_to_stage"]
            for line in lines
        )


        if total_remaining == 0:

            overall_status = (
                "Fully Staged"
            )

        elif total_staged_qty == 0:

            overall_status = (
                "Awaiting Staging"
            )

        else:

            overall_status = (
                "Partially Staged"
            )


        groups.append({

            "receipt_nbr":
                header["receipt_nbr"],

            "status":
                header["status"],

            "receipt_date":
                header["receipt_date"],

            "vendor":
                header["vendor"],

            "project_slug":
                header["project_slug"],

            "project":
                header["project"],

            "po_nbr":
                header["po_nbr"],

            "warehouse":
                header["warehouse"],

            "acumatica_location":
                header[
                    "acumatica_location"
                ],

            "acumatica_updated":
                header[
                    "acumatica_updated"
                ],

            "aims_pulled_at":
                header[
                    "aims_pulled_at"
                ],

            "is_demo":
                bool(
                    header["is_demo"]
                ),

            "line_count":
                len(lines),

            "total_receipt_qty":
                total_receipt_qty,

            "total_staged_qty":
                total_staged_qty,

            "total_remaining":
                total_remaining,

            "staging_status":
                overall_status,

            "lines":
                lines
        })


    connection.close()

    return groups


# ============================================================
# GET LINES BY PROJECT
# ============================================================

def get_receipts_by_project(
    project_slug
):

    connection = get_connection()
    cursor = connection.cursor()


    rows = cursor.execute(
        RECEIPT_LINE_QUERY +
        """
        WHERE h.project_slug = ?

        ORDER BY
            h.receipt_date DESC,
            h.receipt_nbr DESC,
            l.line_nbr
        """,
        (
            project_slug,
        )
    ).fetchall()


    result = [

        build_line_record(
            cursor,
            row
        )

        for row in rows
    ]


    connection.close()

    return result


# ============================================================
# RESOLVE RECEIPT LINE
#
# Backward compatibility:
# If receipt_line_id is omitted, a single-line receipt can
# still be located by receipt number.
# ============================================================

def resolve_receipt_line(
    cursor,
    receipt_nbr=None,
    receipt_line_id=None
):

    if receipt_line_id:

        return cursor.execute(
            """
            SELECT *
            FROM receipt_lines
            WHERE id = ?
            """,
            (
                receipt_line_id,
            )
        ).fetchone()


    if not receipt_nbr:

        return None


    rows = cursor.execute(
        """
        SELECT *
        FROM receipt_lines

        WHERE receipt_nbr = ?

        ORDER BY line_nbr
        """,
        (
            receipt_nbr,
        )
    ).fetchall()


    if len(rows) == 1:

        return rows[0]


    return None


# ============================================================
# STAGE MATERIAL
# ============================================================

def stage_receipt_material(
    receipt_nbr,
    quantity,
    location,
    staged_by="Myska Nasiri",
    receipt_line_id=None
):

    connection = get_connection()
    cursor = connection.cursor()


    try:

        line = resolve_receipt_line(
            cursor,
            receipt_nbr=
                receipt_nbr,
            receipt_line_id=
                receipt_line_id
        )


        if not line:

            line_count = cursor.execute(
                """
                SELECT COUNT(*) AS count
                FROM receipt_lines
                WHERE receipt_nbr = ?
                """,
                (
                    receipt_nbr,
                )
            ).fetchone()["count"]


            if line_count > 1:

                return {
                    "success": False,
                    "message":
                        "This receipt contains multiple material lines. Select the material line to stage."
                }


            return {
                "success": False,
                "message":
                    "Receipt line was not found."
            }


        quantity = int(
            quantity
        )


        if quantity <= 0:

            return {
                "success": False,
                "message":
                    "Staging quantity must be greater than zero."
            }


        if not location:

            return {
                "success": False,
                "message":
                    "Select a storage location."
            }


        remaining_qty = (
            line[
                "remaining_to_stage"
            ]
        )


        if quantity > remaining_qty:

            return {
                "success": False,

                "message":
                    "Staging quantity cannot exceed the quantity actually received and remaining to stage."
            }


        new_staged_qty = (
            line["staged_qty"] +
            quantity
        )


        new_remaining_qty = max(
            line["receipt_qty"] -
            new_staged_qty,
            0
        )


        if new_remaining_qty == 0:

            new_status = (
                "Fully Staged"
            )

        elif new_staged_qty > 0:

            new_status = (
                "Partially Staged"
            )

        else:

            new_status = (
                "Awaiting Staging"
            )


        cursor.execute(
            """
            UPDATE receipt_lines

            SET
                staged_qty = ?,
                remaining_to_stage = ?,
                staging_status = ?

            WHERE id = ?
            """,
            (
                new_staged_qty,
                new_remaining_qty,
                new_status,
                line["id"]
            )
        )


        existing_location = (
            cursor.execute(
                """
                SELECT
                    id,
                    quantity

                FROM material_locations

                WHERE receipt_line_id = ?
                AND location = ?
                """,
                (
                    line["id"],
                    location
                )
            ).fetchone()
        )


        if existing_location:

            cursor.execute(
                """
                UPDATE material_locations

                SET quantity =
                    quantity + ?

                WHERE id = ?
                """,
                (
                    quantity,
                    existing_location[
                        "id"
                    ]
                )
            )

        else:

            cursor.execute(
                """
                INSERT INTO material_locations (

                    receipt_line_id,
                    location,
                    quantity
                )

                VALUES (?, ?, ?)
                """,
                (
                    line["id"],
                    location,
                    quantity
                )
            )


        timestamp = now_string()


        cursor.execute(
            """
            INSERT INTO line_staging_history (

                receipt_line_id,

                quantity,
                uom,

                location,

                staged_by,
                staged_at,

                notes
            )

            VALUES (
                ?,
                ?, ?,
                ?,
                ?, ?,
                ?
            )
            """,
            (
                line["id"],

                quantity,
                line["uom"],

                location,

                staged_by,
                timestamp,

                ""
            )
        )


        cursor.execute(
            """
            INSERT INTO line_material_movements (

                receipt_line_id,

                from_location,
                to_location,

                quantity,
                uom,

                movement_type,

                moved_by,
                moved_at,

                notes
            )

            VALUES (
                ?,
                ?, ?,
                ?, ?,
                ?,
                ?, ?,
                ?
            )
            """,
            (
                line["id"],

                "Receiving & Staging",
                location,

                quantity,
                line["uom"],

                "Initial Staging",

                staged_by,
                timestamp,

                ""
            )
        )


        connection.commit()


        locations = get_line_locations(
            cursor,
            line["id"]
        )


        history = (
            get_line_staging_history(
                cursor,
                line["id"]
            )
        )


        return {

            "success": True,

            "message":
                "Material staged successfully.",


            "receipt_line_id":
                line["id"],

            "receipt_nbr":
                receipt_nbr,

            "line_nbr":
                line["line_nbr"],


            "receipt_qty":
                line["receipt_qty"],

            "staged_qty":
                new_staged_qty,

            "remaining_to_stage":
                new_remaining_qty,


            "staging_status":
                new_status,


            "storage_location":
                get_display_location(
                    locations
                ),


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
# WAREHOUSE MATERIALS
# ============================================================

def get_warehouse_materials():

    connection = get_connection()
    cursor = connection.cursor()


    rows = cursor.execute(
        RECEIPT_LINE_QUERY +
        """
        WHERE l.staged_qty > 0

        ORDER BY
            h.project,
            l.inventory_id,
            h.receipt_nbr,
            l.line_nbr
        """
    ).fetchall()


    materials = []


    for row in rows:

        locations = (
            get_line_locations(
                cursor,
                row["line_id"]
            )
        )


        total_on_hand = sum(
            item["quantity"]
            for item in locations
        )


        assembly_qty = sum(
            item["quantity"]
            for item in locations
            if item["location"]
            == "Assembly Floor"
        )


        warehouse_qty = (
            total_on_hand -
            assembly_qty
        )


        materials.append({

            "receipt_line_id":
                row["line_id"],

            "line_nbr":
                row["line_nbr"],


            "receipt_nbr":
                row["receipt_nbr"],

            "po_nbr":
                row["po_nbr"],


            "inventory_id":
                row["inventory_id"],

            "description":
                row["description"],

            "barcode":
                row["barcode"],


            "project_slug":
                row["project_slug"],

            "project":
                row["project"],


            "package_name":
                row["package_name"],

            "project_number":
                row["project_number"],


            "vendor":
                row["vendor"],


            "uom":
                row["uom"],


            "warehouse_qty":
                warehouse_qty,

            "assembly_qty":
                assembly_qty,

            "total_on_hand":
                total_on_hand,


            "locations":
                locations,


            "is_demo":
                bool(
                    row["is_demo"]
                )
        })


    connection.close()

    return materials


# ============================================================
# MATERIAL DETAIL
# ============================================================

def get_material_detail(
    receipt_nbr=None,
    receipt_line_id=None
):

    connection = get_connection()
    cursor = connection.cursor()


    if receipt_line_id:

        row = cursor.execute(
            RECEIPT_LINE_QUERY +
            """
            WHERE l.id = ?
            """,
            (
                receipt_line_id,
            )
        ).fetchone()

    else:

        rows = cursor.execute(
            RECEIPT_LINE_QUERY +
            """
            WHERE h.receipt_nbr = ?

            ORDER BY l.line_nbr
            """,
            (
                receipt_nbr,
            )
        ).fetchall()


        if len(rows) != 1:

            connection.close()

            return None


        row = rows[0]


    if not row:

        connection.close()

        return None


    locations = get_line_locations(
        cursor,
        row["line_id"]
    )


    movement_history = (
        get_material_movement_history(
            cursor,
            row["line_id"]
        )
    )


    total_on_hand = sum(
        item["quantity"]
        for item in locations
    )


    assembly_qty = sum(
        item["quantity"]
        for item in locations
        if item["location"]
        == "Assembly Floor"
    )


    warehouse_qty = (
        total_on_hand -
        assembly_qty
    )


    material = {

        "receipt_line_id":
            row["line_id"],

        "line_nbr":
            row["line_nbr"],


        "receipt_nbr":
            row["receipt_nbr"],

        "po_nbr":
            row["po_nbr"],


        "inventory_id":
            row["inventory_id"],

        "description":
            row["description"],


        "barcode":
            row["barcode"],


        "project_slug":
            row["project_slug"],

        "project":
            row["project"],


        "package_name":
            row["package_name"],

        "project_number":
            row["project_number"],


        "vendor":
            row["vendor"],


        "uom":
            row["uom"],


        "ordered_qty":
            row["ordered_qty"],

        "open_qty":
            row["open_qty"],

        "receipt_qty":
            row["receipt_qty"],


        "staged_qty":
            row["staged_qty"],

        "remaining_to_stage":
            row[
                "remaining_to_stage"
            ],


        "staging_status":
            row["staging_status"],


        "warehouse_qty":
            warehouse_qty,

        "assembly_qty":
            assembly_qty,

        "total_on_hand":
            total_on_hand,


        "locations":
            locations,


        "movement_history":
            movement_history,


        "is_demo":
            bool(
                row["is_demo"]
            )
    }


    connection.close()

    return material


# ============================================================
# MOVE / CORRECT MATERIAL
# ============================================================

def move_material(
    receipt_nbr,
    from_location,
    to_location,
    quantity,
    moved_by="Myska Nasiri",
    notes="",
    receipt_line_id=None
):

    connection = get_connection()
    cursor = connection.cursor()


    try:

        line = resolve_receipt_line(
            cursor,
            receipt_nbr=
                receipt_nbr,
            receipt_line_id=
                receipt_line_id
        )


        if not line:

            return {
                "success": False,
                "message":
                    "Material line was not found."
            }


        quantity = int(
            quantity
        )


        if quantity <= 0:

            return {
                "success": False,
                "message":
                    "Move quantity must be greater than zero."
            }


        if not from_location:

            return {
                "success": False,
                "message":
                    "Select the current location."
            }


        if not to_location:

            return {
                "success": False,
                "message":
                    "Select a destination location."
            }


        if (
            from_location ==
            to_location
        ):

            return {
                "success": False,
                "message":
                    "The destination must be different from the current location."
            }


        source = cursor.execute(
            """
            SELECT
                id,
                quantity

            FROM material_locations

            WHERE receipt_line_id = ?
            AND location = ?
            """,
            (
                line["id"],
                from_location
            )
        ).fetchone()


        if not source:

            return {
                "success": False,
                "message":
                    "The material is not stored at the selected source location."
            }


        if quantity > source["quantity"]:

            return {
                "success": False,

                "message":
                    "Move quantity cannot exceed the quantity available at this location."
            }


        new_source_qty = (
            source["quantity"] -
            quantity
        )


        if new_source_qty == 0:

            cursor.execute(
                """
                DELETE FROM material_locations
                WHERE id = ?
                """,
                (
                    source["id"],
                )
            )

        else:

            cursor.execute(
                """
                UPDATE material_locations

                SET quantity = ?

                WHERE id = ?
                """,
                (
                    new_source_qty,
                    source["id"]
                )
            )


        destination = cursor.execute(
            """
            SELECT
                id,
                quantity

            FROM material_locations

            WHERE receipt_line_id = ?
            AND location = ?
            """,
            (
                line["id"],
                to_location
            )
        ).fetchone()


        if destination:

            cursor.execute(
                """
                UPDATE material_locations

                SET quantity =
                    quantity + ?

                WHERE id = ?
                """,
                (
                    quantity,
                    destination["id"]
                )
            )

        else:

            cursor.execute(
                """
                INSERT INTO material_locations (

                    receipt_line_id,
                    location,
                    quantity
                )

                VALUES (?, ?, ?)
                """,
                (
                    line["id"],
                    to_location,
                    quantity
                )
            )


        timestamp = now_string()


        cursor.execute(
            """
            INSERT INTO line_material_movements (

                receipt_line_id,

                from_location,
                to_location,

                quantity,
                uom,

                movement_type,

                moved_by,
                moved_at,

                notes
            )

            VALUES (
                ?,
                ?, ?,
                ?, ?,
                ?,
                ?, ?,
                ?
            )
            """,
            (
                line["id"],

                from_location,
                to_location,

                quantity,
                line["uom"],

                "Material Move",

                moved_by,
                timestamp,

                notes
            )
        )


        connection.commit()


        locations = get_line_locations(
            cursor,
            line["id"]
        )


        movement_history = (
            get_material_movement_history(
                cursor,
                line["id"]
            )
        )


        total_on_hand = sum(
            item["quantity"]
            for item in locations
        )


        assembly_qty = sum(
            item["quantity"]
            for item in locations
            if item["location"]
            == "Assembly Floor"
        )


        warehouse_qty = (
            total_on_hand -
            assembly_qty
        )


        return {

            "success": True,

            "message":
                "Material moved successfully.",


            "receipt_line_id":
                line["id"],

            "receipt_nbr":
                line["receipt_nbr"],

            "line_nbr":
                line["line_nbr"],


            "locations":
                locations,


            "warehouse_qty":
                warehouse_qty,

            "assembly_qty":
                assembly_qty,

            "total_on_hand":
                total_on_hand,


            "movement_history":
                movement_history
        }


    except Exception as error:

        connection.rollback()

        print(
            "DATABASE MOVE ERROR:",
            error
        )


        return {
            "success": False,
            "message":
                "Unable to move material."
        }


    finally:

        connection.close()


# ============================================================
# SHOW RECEIPT SUMMARY IN TERMINAL
# ============================================================

def show_receipts():

    groups = get_receipt_groups()


    print(
        "\nRECEIPTS CURRENTLY STORED:\n"
    )


    for receipt in groups:

        print(
            receipt["receipt_nbr"],
            "|",
            receipt["project"],
            "|",
            receipt["vendor"],
            "| Lines:",
            receipt["line_count"],
            "|",
            receipt["staging_status"]
        )


        for line in receipt["lines"]:

            print(
                "   Line",
                line["line_nbr"],
                "|",
                line["inventory_id"],
                "| Received:",
                line["receipt_qty"],
                "| Staged:",
                line["staged_qty"],
                "| Remaining:",
                line["remaining_to_stage"],
                "|",
                line["staging_status"]
            )


# ============================================================
# SHOW WAREHOUSE MATERIALS
# ============================================================

def show_warehouse_materials():

    materials = get_warehouse_materials()


    print(
        "\nWAREHOUSE MATERIALS:\n"
    )


    for material in materials:

        print(
            material["inventory_id"],
            "|",
            material["project"],
            "|",
            material["package_name"],
            "| Receipt:",
            material["receipt_nbr"],
            "Line",
            material["line_nbr"],
            "| Warehouse:",
            material["warehouse_qty"],
            "| Assembly:",
            material["assembly_qty"],
            "| Total:",
            material["total_on_hand"],
            material["uom"]
        )


# ============================================================
# INITIALIZE
# ============================================================

def initialize_database():

    create_tables()

    seed_demo_receipts()


# ============================================================
# RUN DATABASE.PY DIRECTLY
# ============================================================

if __name__ == "__main__":

    initialize_database()

    show_receipts()

    show_warehouse_materials()

    print(
        "\nAIMS mock database initialized successfully."
    )