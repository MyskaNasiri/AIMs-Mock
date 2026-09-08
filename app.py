from io import BytesIO

from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    redirect,
    url_for,
    send_file,
    Response
)

from database import (
    initialize_database,
    get_all_receipts,
    get_receipt_groups,
    get_receipts_by_project,
    stage_receipt_material,
    get_warehouse_materials,
    get_material_detail,
    move_material
)

from reporting_db import (
    initialize_reporting_database,
    create_report,
    get_report,
    get_all_reports,
    save_report_draft,
    submit_report
)

from reporting_pdf import (
    ncr_template_exists,
    render_ncr_template_image,
    generate_completed_ncr_pdf
)


app = Flask(__name__)


# ============================================================
# INITIALIZE DATABASES
# ============================================================

initialize_database()
initialize_reporting_database()


# ============================================================
# PROJECT DATA
# ============================================================

PROJECTS = {

    "targa-butane": {
        "name": "Targa Butane Dryer MCC Building",
        "short_name": "Targa Butane",
        "project_number": "029434-0001-EFAB",
        "client": "Targa",
        "pm": "Leticia Zarpellon",
        "initials": "TB"
    },

    "bp-kaskida": {
        "name": "BP Kaskida",
        "short_name": "BP Kaskida",
        "project_number": "028710-0001-EFAB",
        "client": "BP",
        "pm": "Jie Deng",
        "initials": "BP"
    },

    "slb-hpu-skids": {
        "name": "SLB HPU Skids",
        "short_name": "SLB HPU Skids",
        "project_number": "027682-0003",
        "client": "SLB",
        "pm": "Jorge R. Molano",
        "initials": "SL"
    },

    "venture-global": {
        "name": "Venture Global LNG Expanders",
        "short_name": "Venture Global",
        "project_number": "030458-0001",
        "client": "Venture Global",
        "pm": "Jorge R. Molano",
        "initials": "VG"
    },

    "williams-aquila": {
        "name": "Williams Aquila",
        "short_name": "Williams Aquila",
        "project_number": "Williams Aquila",
        "client": "Williams",
        "pm": "Gina Meins",
        "initials": "WA",

        "packages": [
            {
                "name": "BESS",
                "project_number": "031674-0001"
            },
            {
                "name": "PLC Panels",
                "project_number": "031689-0001"
            },
            {
                "name": "Server",
                "project_number": "031687-0001"
            },
            {
                "name": "FNE",
                "project_number": "031791-0001"
            }
        ]
    },

    "drone-in-the-box": {
        "name": "Drone in the Box",
        "short_name": "Drone in the Box",
        "project_number": "030443-0003-EFAB",
        "client": "Shell",
        "pm": "Lezan",
        "initials": "DB"
    }

}


# ============================================================
# PURCHASE ORDER DEMO DATA
# ============================================================

PURCHASE_ORDERS = {

    "williams-aquila": [

        {
            "po_number": "45001842",
            "vendor": "Graybar",
            "part_number": "5094-IB32",
            "description": "Digital Input Module",
            "ordered_qty": 20,
            "received_qty": 10,
            "remaining_qty": 10,
            "status": "Partial Receipt"
        },

        {
            "po_number": "45001857",
            "vendor": "SCP",
            "part_number": "5094-IF8IH",
            "description": "Analog Input Module",
            "ordered_qty": 8,
            "received_qty": 8,
            "remaining_qty": 0,
            "status": "Received"
        },

        {
            "po_number": "45001863",
            "vendor": "Lonestar",
            "part_number": "5094-OB16",
            "description": "Digital Output Module",
            "ordered_qty": 12,
            "received_qty": 0,
            "remaining_qty": 12,
            "status": "Awaiting Receipt"
        },

        {
            "po_number": "45001871",
            "vendor": "Reynolds",
            "part_number": "1783-SFP1GLX",
            "description": "Fiber Transceiver",
            "ordered_qty": 6,
            "received_qty": 3,
            "remaining_qty": 3,
            "status": "Partial Receipt"
        }

    ]

}


# ============================================================
# PROJECT SCHEDULES
# ============================================================

PROJECT_SCHEDULES = {

    "targa-butane": {

        "risks": [
            "Review loadout and lifting requirements.",
            "Monitor potential UL field certification delays.",
            "Exterior lights and NCR items remain under review."
        ],

        "milestones": [

            {
                "activity": "Initiated",
                "progress": 100,
                "status": "Complete",
                "date": "12/11/25"
            },

            {
                "activity": "IFA",
                "progress": 100,
                "status": "Complete",
                "date": "02/16/26"
            },

            {
                "activity": "IFC",
                "progress": 100,
                "status": "Complete",
                "date": "04/24/26"
            },

            {
                "activity": "Procurement",
                "progress": 100,
                "status": "Complete",
                "date": "05/20/26"
            },

            {
                "activity": "Fabrication Building",
                "progress": 98,
                "status": "On Track",
                "date": "08/28/26*"
            },

            {
                "activity": "Fabrication Panels",
                "progress": 99,
                "status": "On Track",
                "date": "08/28/26*"
            },

            {
                "activity": "TRA Mechanical Inspection",
                "progress": 100,
                "status": "Complete",
                "date": "08/05/26"
            },

            {
                "activity": "Internal FAT TRA Witness",
                "progress": 0,
                "status": "On Track",
                "date": "09/03/26*"
            },

            {
                "activity": "Client FAT",
                "progress": 0,
                "status": "On Track",
                "date": "09/14/26"
            },

            {
                "activity": "Shipment",
                "progress": 0,
                "status": "On Track",
                "date": "09/24/26*"
            },

            {
                "activity": "As-Built",
                "progress": 0,
                "status": "On Track",
                "date": "TBD"
            }

        ]
    },


    "bp-kaskida": {

        "risks": [
            "UL508A drawing requirements remain under review.",
            "Intertek sticker relocation requires coordination."
        ],

        "milestones": [

            {
                "activity": "Procurement Project",
                "progress": 100,
                "status": "Complete",
                "date": "Complete"
            },

            {
                "activity": "Fabrication Phase 1 Stage 2 Chem-Inject / IJB",
                "progress": 50,
                "status": "Behind",
                "date": "09/04/26*"
            },

            {
                "activity": "Fabrication Project",
                "progress": 10,
                "status": "Behind",
                "date": "TBD"
            },

            {
                "activity": "Internal FAT Phase 1 Stage 2 MCC",
                "progress": 100,
                "status": "Complete",
                "date": "07/07/26"
            },

            {
                "activity": "Internal FAT Phase 1 Stage 2 Chem-Inject / IJB",
                "progress": 0,
                "status": "Behind",
                "date": "09/08/26*"
            },

            {
                "activity": "Internal FAT Project",
                "progress": 5,
                "status": "On Track",
                "date": "TBD"
            },

            {
                "activity": "Client FAT Phase 1 Stage 2 MCC",
                "progress": 100,
                "status": "Complete",
                "date": "07/08/26"
            },

            {
                "activity": "Client FAT Phase 1 Stage 2 Chem-Inject / IJB",
                "progress": 0,
                "status": "Behind",
                "date": "09/11/26*"
            },

            {
                "activity": "Client FAT Project",
                "progress": 5,
                "status": "On Track",
                "date": "TBD"
            },

            {
                "activity": "Punchlist Phase 1 Stage 2 MCC",
                "progress": 100,
                "status": "Complete",
                "date": "08/07/26"
            },

            {
                "activity": "Punchlist Phase 1 Stage 2 Chem-Inject / IJB",
                "progress": 0,
                "status": "Behind",
                "date": "09/16/26*"
            },

            {
                "activity": "As-Built Phase 1 Stage 1",
                "progress": 100,
                "status": "Complete",
                "date": "Complete"
            },

            {
                "activity": "As-Built Phase 1 Stage 2 MCC",
                "progress": 75,
                "status": "Behind",
                "date": "08/31/26*"
            },

            {
                "activity": "Shipment Inspection Phase 1 Stage 2 MCC",
                "progress": 0,
                "status": "On Track",
                "date": "09/14/26"
            }

        ]
    },


    "slb-hpu-skids": {

        "risks": [
            "Missing materials may affect fabrication.",
            "FAT procedure still requires coordination.",
            "Onsite inspections and partial QC remain under review."
        ],

        "milestones": [

            {
                "activity": "Initiated",
                "progress": 100,
                "status": "Complete",
                "date": "Complete"
            },

            {
                "activity": "IFA",
                "progress": 100,
                "status": "Complete",
                "date": "Complete"
            },

            {
                "activity": "IFC",
                "progress": 100,
                "status": "Complete",
                "date": "Complete"
            },

            {
                "activity": "Procurement",
                "progress": 98,
                "status": "Behind",
                "date": "TBD"
            },

            {
                "activity": "Fabrication",
                "progress": 90,
                "status": "Behind",
                "date": "TBD"
            },

            {
                "activity": "Internal FAT",
                "progress": 0,
                "status": "Behind",
                "date": "09/04/26*"
            },

            {
                "activity": "Client FAT",
                "progress": 0,
                "status": "Behind",
                "date": "09/09/26*"
            },

            {
                "activity": "Shipment Inspection",
                "progress": 0,
                "status": "Behind",
                "date": "09/14/26*"
            },

            {
                "activity": "As-Built",
                "progress": 0,
                "status": "On Track",
                "date": "09/18/26"
            }

        ]
    },


    "venture-global": {

        "risks": [
            "Inventory timing may shift due to BP fabrication priorities."
        ],

        "milestones": [

            {
                "activity": "Initiated",
                "progress": 100,
                "status": "Complete",
                "date": "Complete"
            },

            {
                "activity": "IFA",
                "progress": 100,
                "status": "Complete",
                "date": "Complete"
            },

            {
                "activity": "IFC",
                "progress": 100,
                "status": "Complete",
                "date": "Complete"
            },

            {
                "activity": "Procurement BPCS / SIS",
                "progress": 100,
                "status": "Complete",
                "date": "04/27/26"
            },

            {
                "activity": "Procurement HIPS",
                "progress": 100,
                "status": "Complete",
                "date": "05/15/26"
            },

            {
                "activity": "Fabrication BPCS / SIS",
                "progress": 100,
                "status": "Complete",
                "date": "09/04/26"
            },

            {
                "activity": "Fabrication HIPS",
                "progress": 100,
                "status": "Complete",
                "date": "09/04/26"
            },

            {
                "activity": "Internal FAT BPCS / SIS / HIPS",
                "progress": 100,
                "status": "Complete",
                "date": "07/14/26"
            },

            {
                "activity": "Client FAT Project",
                "progress": 100,
                "status": "Complete",
                "date": "07/27/26"
            },

            {
                "activity": "Punchlist",
                "progress": 95,
                "status": "On Track",
                "date": "09/04/26*"
            },

            {
                "activity": "Shipment",
                "progress": 0,
                "status": "On Track",
                "date": "09/10/26*"
            },

            {
                "activity": "As-Built",
                "progress": 0,
                "status": "On Track",
                "date": "TBD"
            }

        ]
    },


    "williams-aquila": {

        "risks": [
            "BESS scope changes may require drawing updates.",
            "PLC package includes long-lead items and redesign risk.",
            "Server scope changes remain under review.",
            "FNE approved drawings and resource review remain open."
        ],

        "milestones": [

            # =================================================
            # BESS
            # =================================================

            {
                "package": "BESS",
                "project_number": "031674-0001",
                "activity": "Initiated",
                "progress": 100,
                "status": "Complete",
                "date": "05/22/26"
            },

            {
                "package": "BESS",
                "project_number": "031674-0001",
                "activity": "IFA",
                "progress": 100,
                "status": "Complete",
                "date": "Complete"
            },

            {
                "package": "BESS",
                "project_number": "031674-0001",
                "activity": "IFC",
                "progress": 75,
                "status": "On Track",
                "date": "09/11/26"
            },

            {
                "package": "BESS",
                "project_number": "031674-0001",
                "activity": "Procurement",
                "progress": 100,
                "status": "Complete",
                "date": "06/03/26"
            },

            {
                "package": "BESS",
                "project_number": "031674-0001",
                "activity": "Fabrication",
                "progress": 0,
                "status": "On Track",
                "date": "10/02/26*"
            },

            {
                "package": "BESS",
                "project_number": "031674-0001",
                "activity": "Internal FAT",
                "progress": 0,
                "status": "On Track",
                "date": "10/09/26*"
            },

            {
                "package": "BESS",
                "project_number": "031674-0001",
                "activity": "Client FAT",
                "progress": 0,
                "status": "On Track",
                "date": "10/13/26*"
            },

            {
                "package": "BESS",
                "project_number": "031674-0001",
                "activity": "Shipment Inspection",
                "progress": 0,
                "status": "On Track",
                "date": "10/16/26*"
            },

            {
                "package": "BESS",
                "project_number": "031674-0001",
                "activity": "As-Built",
                "progress": 0,
                "status": "On Track",
                "date": "TBD"
            },


            # =================================================
            # PLC PANELS
            # =================================================

            {
                "package": "PLC Panels",
                "project_number": "031689-0001",
                "activity": "Initiated",
                "progress": 100,
                "status": "Complete",
                "date": "05/22/26"
            },

            {
                "package": "PLC Panels",
                "project_number": "031689-0001",
                "activity": "IFA",
                "progress": 100,
                "status": "Complete",
                "date": "06/15/26"
            },

            {
                "package": "PLC Panels",
                "project_number": "031689-0001",
                "activity": "IFP RIOs Package",
                "progress": 50,
                "status": "On Track",
                "date": "09/04/26"
            },

            {
                "package": "PLC Panels",
                "project_number": "031689-0001",
                "activity": "Procurement RIOs x2",
                "progress": 100,
                "status": "Complete",
                "date": "06/03/26"
            },

            {
                "package": "PLC Panels",
                "project_number": "031689-0001",
                "activity": "Procurement RIOs x9",
                "progress": 0,
                "status": "On Track",
                "date": "06/29/26"
            },

            {
                "package": "PLC Panels",
                "project_number": "031689-0001",
                "activity": "Procurement SCP",
                "progress": 100,
                "status": "Complete",
                "date": "06/03/26"
            },

            {
                "package": "PLC Panels",
                "project_number": "031689-0001",
                "activity": "Procurement ESD",
                "progress": 100,
                "status": "Complete",
                "date": "06/03/26"
            },

            {
                "package": "PLC Panels",
                "project_number": "031689-0001",
                "activity": "Fabrication RIOs x2",
                "progress": 100,
                "status": "Complete",
                "date": "08/17/26"
            },

            {
                "package": "PLC Panels",
                "project_number": "031689-0001",
                "activity": "Fabrication Project",
                "progress": 0,
                "status": "On Track",
                "date": "TBD"
            },

            {
                "package": "PLC Panels",
                "project_number": "031689-0001",
                "activity": "Internal FAT RIOs x2",
                "progress": 0,
                "status": "On Track",
                "date": "09/14/26"
            },

            {
                "package": "PLC Panels",
                "project_number": "031689-0001",
                "activity": "Client FAT RIOs x2",
                "progress": 0,
                "status": "On Track",
                "date": "09/22/26*"
            },

            {
                "package": "PLC Panels",
                "project_number": "031689-0001",
                "activity": "Shipment Inspection RIOs x2",
                "progress": 0,
                "status": "On Track",
                "date": "09/30/26*"
            },

            {
                "package": "PLC Panels",
                "project_number": "031689-0001",
                "activity": "As-Built",
                "progress": 0,
                "status": "On Track",
                "date": "TBD"
            },


            # =================================================
            # SERVER
            # =================================================

            {
                "package": "Server",
                "project_number": "031687-0001",
                "activity": "Initiated",
                "progress": 100,
                "status": "Complete",
                "date": "05/22/26"
            },

            {
                "package": "Server",
                "project_number": "031687-0001",
                "activity": "IFA",
                "progress": 100,
                "status": "Complete",
                "date": "08/04/26"
            },

            {
                "package": "Server",
                "project_number": "031687-0001",
                "activity": "IFC",
                "progress": 100,
                "status": "On Track",
                "date": "08/04/26"
            },

            {
                "package": "Server",
                "project_number": "031687-0001",
                "activity": "Procurement Long Lead",
                "progress": 100,
                "status": "Complete",
                "date": "06/03/26"
            },

            {
                "package": "Server",
                "project_number": "031687-0001",
                "activity": "Procurement",
                "progress": 85,
                "status": "On Track",
                "date": "09/02/26"
            },

            {
                "package": "Server",
                "project_number": "031687-0001",
                "activity": "Fabrication",
                "progress": 0,
                "status": "On Track",
                "date": "10/15/26"
            },

            {
                "package": "Server",
                "project_number": "031687-0001",
                "activity": "Internal FAT",
                "progress": 0,
                "status": "On Track",
                "date": "11/07/26"
            },

            {
                "package": "Server",
                "project_number": "031687-0001",
                "activity": "Client FAT",
                "progress": 0,
                "status": "On Track",
                "date": "11/15/26"
            },

            {
                "package": "Server",
                "project_number": "031687-0001",
                "activity": "Shipment Inspection",
                "progress": 0,
                "status": "On Track",
                "date": "11/18/26"
            },

            {
                "package": "Server",
                "project_number": "031687-0001",
                "activity": "As-Built",
                "progress": 0,
                "status": "On Track",
                "date": "N/A"
            },


            # =================================================
            # FNE
            # =================================================

            {
                "package": "FNE",
                "project_number": "031791-0001",
                "activity": "Initiated",
                "progress": 100,
                "status": "Complete",
                "date": "Complete"
            },

            {
                "package": "FNE",
                "project_number": "031791-0001",
                "activity": "IFA",
                "progress": 50,
                "status": "On Track",
                "date": "09/08/26"
            },

            {
                "package": "FNE",
                "project_number": "031791-0001",
                "activity": "IFC",
                "progress": 0,
                "status": "On Track",
                "date": "09/23/26"
            },

            {
                "package": "FNE",
                "project_number": "031791-0001",
                "activity": "Procurement",
                "progress": 95,
                "status": "On Track",
                "date": "TBD"
            },

            {
                "package": "FNE",
                "project_number": "031791-0001",
                "activity": "Fabrication",
                "progress": 0,
                "status": "On Track",
                "date": "09/23/26*"
            },

            {
                "package": "FNE",
                "project_number": "031791-0001",
                "activity": "Internal FAT",
                "progress": 0,
                "status": "On Track",
                "date": "TBD"
            },

            {
                "package": "FNE",
                "project_number": "031791-0001",
                "activity": "Client FAT",
                "progress": 0,
                "status": "On Track",
                "date": "TBD"
            },

            {
                "package": "FNE",
                "project_number": "031791-0001",
                "activity": "Shipment",
                "progress": 0,
                "status": "On Track",
                "date": "TBD"
            },

            {
                "package": "FNE",
                "project_number": "031791-0001",
                "activity": "As-Built",
                "progress": 0,
                "status": "On Track",
                "date": "TBD"
            }

        ]
    },


    "drone-in-the-box": {

        "risks": [
            "Forklift and skid arrival timing may affect fabrication.",
            "Update drawings as field conditions change.",
            "Conduit fittings remain under review.",
            "Inspect enclosure before blast and paint."
        ],

        "milestones": [

            {
                "activity": "Initiated",
                "progress": 100,
                "status": "Complete",
                "date": "Complete"
            },

            {
                "activity": "IFA",
                "progress": 100,
                "status": "Complete",
                "date": "Complete"
            },

            {
                "activity": "IFC",
                "progress": 100,
                "status": "Complete",
                "date": "Complete"
            },

            {
                "activity": "Procurement Long Lead",
                "progress": 100,
                "status": "Complete",
                "date": "Complete"
            },

            {
                "activity": "Procurement",
                "progress": 100,
                "status": "Complete",
                "date": "Complete"
            },

            {
                "activity": "Skid Inspection Manufacturer",
                "progress": 100,
                "status": "Complete",
                "date": "08/26/26"
            },

            {
                "activity": "Receipt Skid",
                "progress": 0,
                "status": "On Track",
                "date": "09/02/26*"
            },

            {
                "activity": "Receipt Enclosure",
                "progress": 0,
                "status": "On Track",
                "date": "09/02/26"
            },

            {
                "activity": "Fabrication",
                "progress": 0,
                "status": "On Track",
                "date": "09/03/26"
            },

            {
                "activity": "Internal FAT",
                "progress": 0,
                "status": "On Track",
                "date": "09/21/26"
            },

            {
                "activity": "Client FAT",
                "progress": 0,
                "status": "On Track",
                "date": "09/28/26"
            },

            {
                "activity": "Shipment Inspection",
                "progress": 0,
                "status": "On Track",
                "date": "09/30/26"
            },

            {
                "activity": "As-Built",
                "progress": 0,
                "status": "On Track",
                "date": "TBD"
            }

        ]
    }

}


# ============================================================
# GLOBAL PROJECT MENU
# ============================================================

@app.context_processor
def inject_projects_menu():

    return {
        "projects_menu": PROJECTS
    }


# ============================================================
# ROOT
# ============================================================

@app.route("/")
def index():

    return redirect(
        url_for(
            "tech_center_home"
        )
    )


# ============================================================
# TECH CENTER HOME
# ============================================================

@app.route("/tech-center")
def tech_center_home():

    return render_template(
        "tech_center_home.html",
        projects=PROJECTS,
        schedules=PROJECT_SCHEDULES
    )


# ============================================================
# MATERIALS MANAGEMENT
# ============================================================

@app.route("/materials")
def materials():

    all_receipt_groups = (
        get_receipt_groups()
    )


    receipt_groups = [

        receipt

        for receipt
        in all_receipt_groups

        if not
        receipt["receipt_nbr"]
        .startswith(
            "POR-DEMO-"
        )
    ]


    warehouse_materials = (
        get_warehouse_materials()
    )


    return render_template(

        "materials_management.html",

        receipt_groups=
            receipt_groups,

        receipts=
            get_all_receipts(),

        warehouse_materials=
            warehouse_materials
    )


# ============================================================
# STAGE RECEIPT MATERIAL
# ============================================================

@app.route(
    "/materials/stage",
    methods=["POST"]
)
def stage_material():

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )


    receipt_nbr = (
        data.get(
            "receipt_nbr"
        )
    )


    receipt_line_id = (
        data.get(
            "receipt_line_id"
        )
    )


    location = (
        data.get(
            "location"
        )
    )


    quantity = (
        data.get(
            "quantity"
        )
    )


    if not receipt_nbr:

        return jsonify({
            "message":
                "Receipt number is required."
        }), 400


    if not receipt_line_id:

        return jsonify({
            "message":
                "Receipt line is required."
        }), 400


    if not location:

        return jsonify({
            "message":
                "Storage location is required."
        }), 400


    try:

        quantity = float(
            quantity
        )

    except (
        TypeError,
        ValueError
    ):

        return jsonify({
            "message":
                "Enter a valid staging quantity."
        }), 400


    result = (
        stage_receipt_material(

            receipt_nbr=
                receipt_nbr,

            receipt_line_id=
                receipt_line_id,

            quantity=
                quantity,

            location=
                location,

            staged_by=
                "Myska Nasiri"
        )
    )


    if not result.get(
        "success"
    ):

        return jsonify(
            result
        ), 400


    return jsonify(
        result
    )


# ============================================================
# MATERIAL DETAIL BY RECEIPT LINE
# ============================================================

@app.route(
    "/materials/line/<int:receipt_line_id>"
)
def material_line_detail(
    receipt_line_id
):

    material = (
        get_material_detail(
            receipt_line_id=
                receipt_line_id
        )
    )


    if not material:

        return jsonify({
            "message":
                "Material line was not found."
        }), 404


    return jsonify({
        "material":
            material
    })


# ============================================================
# LEGACY MATERIAL DETAIL BY RECEIPT
# ============================================================

@app.route(
    "/materials/<receipt_nbr>"
)
def material_detail(
    receipt_nbr
):

    material = (
        get_material_detail(
            receipt_nbr=
                receipt_nbr
        )
    )


    if not material:

        return jsonify({
            "message":
                "This receipt either was not found or contains "
                "multiple material lines. Select an individual "
                "receipt line instead."
        }), 404


    return jsonify({
        "material":
            material
    })


# ============================================================
# MOVE / RESTAGE MATERIAL
# ============================================================

@app.route(
    "/materials/move",
    methods=["POST"]
)
def move_material_route():

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )


    receipt_nbr = (
        data.get(
            "receipt_nbr"
        )
    )


    receipt_line_id = (
        data.get(
            "receipt_line_id"
        )
    )


    from_location = (
        data.get(
            "from_location"
        )
    )


    to_location = (
        data.get(
            "to_location"
        )
    )


    quantity = (
        data.get(
            "quantity"
        )
    )


    notes = (
        data.get(
            "notes",
            ""
        )
        or ""
    )


    if not receipt_line_id:

        return jsonify({
            "message":
                "Receipt line is required."
        }), 400


    if not from_location:

        return jsonify({
            "message":
                "Current location is required."
        }), 400


    if not to_location:

        return jsonify({
            "message":
                "Destination location is required."
        }), 400


    try:

        quantity = float(
            quantity
        )

    except (
        TypeError,
        ValueError
    ):

        return jsonify({
            "message":
                "Enter a valid movement quantity."
        }), 400


    result = (
        move_material(

            receipt_nbr=
                receipt_nbr,

            receipt_line_id=
                receipt_line_id,

            from_location=
                from_location,

            to_location=
                to_location,

            quantity=
                quantity,

            moved_by=
                "Myska Nasiri",

            notes=
                notes
        )
    )


    if not result.get(
        "success"
    ):

        return jsonify(
            result
        ), 400


    return jsonify(
        result
    )


# ============================================================
# PROJECT HELPER
# ============================================================

def get_project_or_404(
    project_slug
):

    return PROJECTS.get(
        project_slug
    )


# ============================================================
# PROJECT DASHBOARD
# ============================================================

@app.route(
    "/projects/<project_slug>"
)
def project_dashboard(
    project_slug
):

    project = (
        get_project_or_404(
            project_slug
        )
    )


    if not project:

        return (
            "Project not found",
            404
        )


    schedule = (
        PROJECT_SCHEDULES.get(
            project_slug,
            {}
        )
    )


    receipts = (
        get_receipts_by_project(
            project_slug
        )
    )


    return render_template(

        "project_dashboard.html",

        project=
            project,

        project_slug=
            project_slug,

        schedule=
            schedule,

        receipts=
            receipts
    )


# ============================================================
# PROJECT PURCHASE ORDERS
# ============================================================

@app.route(
    "/projects/<project_slug>/purchase-orders"
)
def project_purchase_orders(
    project_slug
):

    project = (
        get_project_or_404(
            project_slug
        )
    )


    if not project:

        return (
            "Project not found",
            404
        )


    purchase_orders = (
        PURCHASE_ORDERS.get(
            project_slug,
            []
        )
    )


    return render_template(

        "project_purchase_orders.html",

        project=
            project,

        project_slug=
            project_slug,

        purchase_orders=
            purchase_orders
    )


# ============================================================
# PROJECT SCHEDULE
# ============================================================

@app.route(
    "/projects/<project_slug>/schedule"
)
def project_schedule(
    project_slug
):

    project = (
        get_project_or_404(
            project_slug
        )
    )


    if not project:

        return (
            "Project not found",
            404
        )


    schedule = (
        PROJECT_SCHEDULES.get(
            project_slug,
            {
                "risks": [],
                "milestones": []
            }
        )
    )


    return render_template(

        "project_schedule.html",

        project=
            project,

        project_slug=
            project_slug,

        schedule=
            schedule
    )


# ============================================================
# PROJECT MATERIALS
# ============================================================

@app.route(
    "/projects/<project_slug>/materials"
)
def project_materials(
    project_slug
):

    project = (
        get_project_or_404(
            project_slug
        )
    )


    if not project:

        return (
            "Project not found",
            404
        )


    receipts = (
        get_receipts_by_project(
            project_slug
        )
    )


    materials = []


    for receipt in receipts:

        materials.append({

            "receipt_line_id":
                receipt.get(
                    "receipt_line_id"
                ),

            "line_nbr":
                receipt.get(
                    "line_nbr"
                ),

            "receipt_nbr":
                receipt.get(
                    "receipt_nbr"
                ),

            "po_nbr":
                receipt.get(
                    "po_nbr"
                ),

            "inventory_id":
                receipt.get(
                    "inventory_id"
                ),

            "description":
                receipt.get(
                    "description"
                ),

            "package_name":
                receipt.get(
                    "package_name"
                ),

            "project_number":
                receipt.get(
                    "project_number"
                ),

            "receipt_qty":
                receipt.get(
                    "receipt_qty",
                    0
                ),

            "staged_qty":
                receipt.get(
                    "staged_qty",
                    0
                ),

            "remaining_to_stage":
                receipt.get(
                    "remaining_to_stage",
                    0
                ),

            "staging_status":
                receipt.get(
                    "staging_status"
                ),

            "storage_location":
                receipt.get(
                    "storage_location",
                    "Not Staged"
                ),

            "locations":
                receipt.get(
                    "location_list",
                    []
                ),

            "uom":
                receipt.get(
                    "uom",
                    "EA"
                ),

            "is_demo":
                receipt.get(
                    "is_demo",
                    0
                )

        })


    return render_template(

        "project_materials.html",

        project=
            project,

        project_slug=
            project_slug,

        materials=
            materials
    )


# ============================================================
# REPORTING DASHBOARD
# ============================================================

@app.route(
    "/reporting"
)
def reporting():

    reports = (
        get_all_reports()
    )


    return render_template(

        "reporting.html",

        reports=
            reports
    )


# ============================================================
# CREATE NEW REPORT
# ============================================================

@app.route(
    "/reporting/create",
    methods=["POST"]
)
def create_reporting_record():

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )


    project_slug = (
        data.get(
            "project_slug"
        )
    )


    package_name = (
        data.get(
            "package_name"
        )
    )


    report_type = (
        data.get(
            "report_type"
        )
    )


    if not project_slug:

        return jsonify({
            "message":
                "Project is required."
        }), 400


    if not package_name:

        return jsonify({
            "message":
                "Package / section is required."
        }), 400


    if not report_type:

        return jsonify({
            "message":
                "Report type is required."
        }), 400


    project = (
        PROJECTS.get(
            project_slug
        )
    )


    if not project:

        return jsonify({
            "message":
                "Project was not found."
        }), 404


    if report_type != "NCR":

        return jsonify({
            "message":
                "Only the NCR template is connected "
                "in this prototype."
        }), 400


    try:

        result = (
            create_report(

                report_type=
                    report_type,

                project_slug=
                    project_slug,

                project_name=
                    project["short_name"],

                package_name=
                    package_name,

                created_by=
                    "Myska Nasiri"
            )
        )

    except Exception as error:

        print(
            "REPORT CREATE ERROR:",
            error
        )

        return jsonify({
            "message":
                "Unable to create report."
        }), 500


    return jsonify({

        "success":
            True,

        "report_id":
            result["id"],

        "report_number":
            result["report_number"],

        "redirect_url":
            url_for(
                "ncr_report",
                report_id=
                    result["id"]
            )
    })


# ============================================================
# NCR DIGITAL REPORT
# ============================================================

@app.route(
    "/reporting/ncr/<int:report_id>"
)
def ncr_report(
    report_id
):

    report = (
        get_report(
            report_id
        )
    )


    if not report:

        return (
            "Report not found",
            404
        )


    if (
        report.get(
            "report_type"
        )
        != "NCR"
    ):

        return (
            "This report is not an NCR.",
            400
        )


    project = (
        PROJECTS.get(
            report.get(
                "project_slug"
            )
        )
    )


    return render_template(

        "ncr_report.html",

        report=
            report,

        project=
            project,

        project_slug=
            report.get(
                "project_slug"
            )
    )


# ============================================================
# SAVE NCR DRAFT
# ============================================================

@app.route(
    "/reporting/ncr/<int:report_id>/save",
    methods=["POST"]
)
def save_ncr_report(
    report_id
):

    report = (
        get_report(
            report_id
        )
    )


    if not report:

        return jsonify({
            "message":
                "Report was not found."
        }), 404


    data = (
        request.get_json(
            silent=True
        )
        or {}
    )


    try:

        save_report_draft(
            report_id,
            data
        )

    except Exception as error:

        print(
            "REPORT SAVE ERROR:",
            error
        )

        return jsonify({
            "message":
                "Unable to save draft."
        }), 500


    return jsonify({

        "success":
            True,

        "message":
            "Draft saved successfully."
    })


# ============================================================
# SUBMIT NCR
# ============================================================

@app.route(
    "/reporting/ncr/<int:report_id>/submit",
    methods=["POST"]
)
def submit_ncr_report(
    report_id
):

    report = (
        get_report(
            report_id
        )
    )


    if not report:

        return jsonify({
            "message":
                "Report was not found."
        }), 404


    data = (
        request.get_json(
            silent=True
        )
        or {}
    )


    if not data.get(
        "date"
    ):

        return jsonify({
            "message":
                "Report date is required."
        }), 400


    if not data.get(
        "nonconformance_description"
    ):

        return jsonify({
            "message":
                "Description of the non-conformance is required."
        }), 400


    try:

        submit_report(
            report_id,
            data
        )

    except Exception as error:

        print(
            "REPORT SUBMIT ERROR:",
            error
        )

        return jsonify({
            "message":
                "Unable to submit report."
        }), 500


    return jsonify({

        "success":
            True,

        "message":
            "Report submitted successfully."
    })


# ============================================================
# NCR TEMPLATE IMAGE
#
# Converts the actual NCR PDF template to an image so it can
# appear as the background of the fillable browser page.
# ============================================================

@app.route(
    "/reporting/ncr/template-image"
)
def ncr_template_image():

    if not ncr_template_exists():

        return (
            "NCR template PDF not found.",
            404
        )


    try:

        image_bytes = (
            render_ncr_template_image()
        )

    except Exception as error:

        print(
            "NCR TEMPLATE IMAGE ERROR:",
            error
        )

        return (
            "Unable to render NCR template.",
            500
        )


    return Response(
        image_bytes,
        mimetype=
            "image/png"
    )


# ============================================================
# GENERATED COMPLETED NCR PDF
#
# Writes the saved report information onto a copy of the
# original Audubon NCR template.
# ============================================================

@app.route(
    "/reporting/ncr/<int:report_id>/pdf"
)
def download_ncr_pdf(
    report_id
):

    report = (
        get_report(
            report_id
        )
    )


    if not report:

        return (
            "Report not found.",
            404
        )


    if (
        report.get(
            "report_type"
        )
        != "NCR"
    ):

        return (
            "This report is not an NCR.",
            400
        )


    if not ncr_template_exists():

        return (
            "NCR template PDF not found.",
            404
        )


    try:

        pdf_bytes = (
            generate_completed_ncr_pdf(
                report
            )
        )

    except Exception as error:

        print(
            "NCR PDF ERROR:",
            error
        )

        return (
            "Unable to generate NCR PDF.",
            500
        )


    return send_file(

        BytesIO(
            pdf_bytes
        ),

        mimetype=
            "application/pdf",

        as_attachment=
            False,

        download_name=
            (
                report[
                    "report_number"
                ]
                + ".pdf"
            )
    )


# ============================================================
# RUN APP
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=True,
        port=5001,
        use_reloader=False
    )