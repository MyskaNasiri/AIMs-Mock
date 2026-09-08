from pathlib import Path
from io import BytesIO

import fitz


BASE_DIR = Path(__file__).resolve().parent

NCR_TEMPLATE_PATH = (
    BASE_DIR
    / "static"
    / "report_templates"
    / "ncr_template.pdf"
)


# ============================================================
# CHECK TEMPLATE
# ============================================================

def ncr_template_exists():

    return NCR_TEMPLATE_PATH.exists()


# ============================================================
# RENDER TEMPLATE AS PNG
#
# This lets the browser display the ACTUAL Audubon PDF
# as the visual background while HTML fields sit over it.
# ============================================================

def render_ncr_template_image():

    if not NCR_TEMPLATE_PATH.exists():

        raise FileNotFoundError(
            "NCR template PDF was not found."
        )


    document = fitz.open(
        NCR_TEMPLATE_PATH
    )


    page = document[0]


    matrix = fitz.Matrix(
        2,
        2
    )


    pixmap = page.get_pixmap(
        matrix=matrix,
        alpha=False
    )


    image_bytes = (
        pixmap.tobytes(
            "png"
        )
    )


    document.close()


    return image_bytes


# ============================================================
# PDF TEXT HELPERS
# ============================================================

def insert_text(
    page,
    rect,
    text,
    fontsize=7,
    align=0
):

    if text is None:
        return


    text = str(
        text
    ).strip()


    if not text:
        return


    page.insert_textbox(
        fitz.Rect(
            *rect
        ),
        text,
        fontsize=fontsize,
        fontname="helv",
        color=(0, 0, 0),
        align=align
    )


def add_x(
    page,
    x,
    y,
    size=7
):

    page.insert_text(
        fitz.Point(
            x,
            y
        ),
        "X",
        fontsize=size,
        fontname="helv",
        color=(0, 0, 0)
    )


# ============================================================
# GENERATE COMPLETED NCR
# ============================================================

def generate_completed_ncr_pdf(
    report
):

    if not NCR_TEMPLATE_PATH.exists():

        raise FileNotFoundError(
            "NCR template PDF was not found."
        )


    data = (
        report.get(
            "report_data"
        )
        or {}
    )


    document = fitz.open(
        NCR_TEMPLATE_PATH
    )


    page = document[0]


    # ========================================================
    # TOP INFORMATION
    # ========================================================

    insert_text(
        page,
        (160, 102, 338, 117),
        data.get(
            "date"
        )
    )


    insert_text(
        page,
        (416, 102, 558, 117),
        report.get(
            "report_number"
        )
    )


    insert_text(
        page,
        (160, 118, 338, 132),
        report.get(
            "project_name"
        )
    )


    insert_text(
        page,
        (416, 118, 558, 132),
        data.get(
            "client"
        )
    )


    insert_text(
        page,
        (160, 133, 338, 147),
        data.get(
            "po_number"
        )
    )


    insert_text(
        page,
        (416, 133, 558, 147),
        data.get(
            "vendor"
        )
    )


    insert_text(
        page,
        (160, 148, 338, 162),
        data.get(
            "item_number"
        )
    )


    insert_text(
        page,
        (416, 148, 558, 162),
        data.get(
            "location"
        )
    )


    insert_text(
        page,
        (160, 163, 338, 177),
        data.get(
            "tag_number"
        )
    )


    insert_text(
        page,
        (416, 163, 558, 177),
        data.get(
            "contact"
        )
    )


    insert_text(
        page,
        (160, 178, 338, 193),
        data.get(
            "description"
        )
    )


    insert_text(
        page,
        (416, 178, 558, 193),
        data.get(
            "phone"
        )
    )


    insert_text(
        page,
        (160, 194, 338, 208),
        data.get(
            "specification"
        )
    )


    insert_text(
        page,
        (416, 194, 558, 208),
        data.get(
            "drawing"
        )
    )


    insert_text(
        page,
        (160, 209, 338, 223),
        data.get(
            "code"
        )
    )


    # Attachments checkboxes

    if data.get(
        "attachments"
    ) == "Yes":

        add_x(
            page,
            451,
            220
        )


    if data.get(
        "attachments"
    ) == "No":

        add_x(
            page,
            497,
            220
        )


    # ========================================================
    # DESCRIPTION
    # ========================================================

    insert_text(
        page,
        (84, 240, 552, 294),
        data.get(
            "nonconformance_description"
        ),
        fontsize=7
    )


    insert_text(
        page,
        (129, 299, 378, 312),
        data.get(
            "issuer"
        )
    )


    insert_text(
        page,
        (448, 299, 558, 312),
        data.get(
            "issue_date"
        )
    )


    # ========================================================
    # SEVERITY
    # ========================================================

    severity = (
        data.get(
            "severity"
        )
    )


    if severity == "Minor":

        add_x(
            page,
            160,
            325
        )


    elif severity == "Major":

        add_x(
            page,
            219,
            325
        )


    # ========================================================
    # CAUSE / TYPE
    # ========================================================

    causes = (
        data.get(
            "causes"
        )
        or []
    )


    cause_positions = {

        "Specification Violation":
            (88, 354),

        "Code Violation":
            (88, 369),

        "Fabrication Error":
            (88, 384),

        "Test Failure":
            (88, 399),

        "Material Defect":
            (248, 354),

        "Major Weld Repair":
            (248, 369),

        "Dimensional Error":
            (248, 384),

        "Procedural Violation":
            (248, 399),

        "Documentation Error":
            (387, 354),

        "Missing Items / Parts":
            (387, 369),

        "Damaged Items / Parts":
            (387, 384),

        "Other":
            (387, 399)
    }


    for cause in causes:

        position = (
            cause_positions.get(
                cause
            )
        )


        if position:

            add_x(
                page,
                position[0],
                position[1]
            )


    # ========================================================
    # PROPOSED CORRECTIVE ACTION
    # ========================================================

    corrective_action = (
        data.get(
            "corrective_action"
        )
    )


    corrective_positions = {

        "Use As Is":
            (244, 414),

        "Rework":
            (328, 414),

        "Replace":
            (396, 414),

        "Re-Test":
            (472, 414)
    }


    position = (
        corrective_positions.get(
            corrective_action
        )
    )


    if position:

        add_x(
            page,
            position[0],
            position[1]
        )


    insert_text(
        page,
        (84, 419, 552, 472),
        data.get(
            "corrective_comments"
        ),
        fontsize=7
    )


    insert_text(
        page,
        (129, 477, 410, 490),
        data.get(
            "corrective_vendor"
        )
    )


    insert_text(
        page,
        (448, 477, 558, 490),
        data.get(
            "corrective_date"
        )
    )


    # ========================================================
    # DISPOSITION
    # ========================================================

    disposition = (
        data.get(
            "disposition"
        )
    )


    disposition_positions = {

        "Use As Is":
            (244, 503),

        "Rework":
            (328, 503),

        "Replace":
            (396, 503),

        "Re-Test":
            (472, 503)
    }


    position = (
        disposition_positions.get(
            disposition
        )
    )


    if position:

        add_x(
            page,
            position[0],
            position[1]
        )


    insert_text(
        page,
        (84, 509, 552, 561),
        data.get(
            "disposition_comments"
        ),
        fontsize=7
    )


    insert_text(
        page,
        (169, 566, 410, 580),
        data.get(
            "approval"
        )
    )


    insert_text(
        page,
        (448, 566, 558, 580),
        data.get(
            "approval_date"
        )
    )


    insert_text(
        page,
        (169, 581, 410, 595),
        data.get(
            "client_approval"
        )
    )


    insert_text(
        page,
        (448, 581, 558, 595),
        data.get(
            "client_approval_date"
        )
    )


    # ========================================================
    # CLOSURE
    # ========================================================

    follow_up = (
        data.get(
            "follow_up"
        )
    )


    follow_up_positions = {

        "Yes":
            (440, 609),

        "No":
            (484, 609),

        "N/A":
            (528, 609)
    }


    position = (
        follow_up_positions.get(
            follow_up
        )
    )


    if position:

        add_x(
            page,
            position[0],
            position[1]
        )


    insert_text(
        page,
        (84, 614, 552, 666),
        data.get(
            "closure"
        ),
        fontsize=7
    )


    insert_text(
        page,
        (191, 671, 410, 684),
        data.get(
            "inspector"
        )
    )


    insert_text(
        page,
        (448, 671, 558, 684),
        data.get(
            "inspection_date"
        )
    )


    insert_text(
        page,
        (191, 686, 410, 699),
        data.get(
            "client_representative"
        )
    )


    insert_text(
        page,
        (448, 686, 558, 699),
        data.get(
            "client_representative_date"
        )
    )


    # ========================================================
    # DISTRIBUTION
    # ========================================================

    distribution = (
        data.get(
            "distribution"
        )
        or []
    )


    distribution_positions = {

        "Vendor":
            (115, 718),

        "Engineering":
            (177, 718),

        "Purchasing":
            (258, 718),

        "Expediting":
            (329, 718),

        "Inspection":
            (399, 718),

        "Job Site":
            (466, 718),

        "Client":
            (526, 718)
    }


    for recipient in distribution:

        position = (
            distribution_positions.get(
                recipient
            )
        )


        if position:

            add_x(
                page,
                position[0],
                position[1],
                size=6
            )


    # ========================================================
    # OUTPUT
    # ========================================================

    output = BytesIO()


    document.save(
        output
    )


    document.close()


    output.seek(
        0
    )


    return output.getvalue()