from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    abort,
    request,
    jsonify
)

from database import (
    initialize_database,
    get_all_receipts,
    get_receipts_by_project,
    stage_receipt_material
)


app = Flask(__name__)


# ============================================================
# INITIALIZE SQLITE DATABASE
# ============================================================

initialize_database()


# ============================================================
# TECH CENTER PROJECTS
# ============================================================

PROJECTS = {

    "targa-butane": {
        "name": "Targa Butane Dryer MCC Building",
        "short_name": "Targa Butane",
        "number": "029434-0001-EFAB",
        "client": "Targa",
        "pm": "Leticia Zarpellon",
        "status": "Active",
        "initials": "TB",
        "open_pos": 0,
        "recent_receipts": 0,
        "awaiting_staging": 0,
        "fully_staged": 0
    },

    "bp-kaskida": {
        "name": "BP Kaskida",
        "short_name": "BP Kaskida",
        "number": "028710-0001-EFAB",
        "client": "BP",
        "pm": "Jie Deng",
        "status": "Active",
        "initials": "BP",
        "open_pos": 0,
        "recent_receipts": 0,
        "awaiting_staging": 0,
        "fully_staged": 0
    },

    "slb-hpu-skids": {
        "name": "SLB HPU Skids",
        "short_name": "SLB HPU Skids",
        "number": "027682-0003",
        "client": "SLB",
        "pm": "Jorge R. Molano",
        "status": "Active",
        "initials": "SL",
        "open_pos": 0,
        "recent_receipts": 0,
        "awaiting_staging": 0,
        "fully_staged": 0
    },

    "venture-global": {
        "name": "Venture Global LNG Expanders",
        "short_name": "Venture Global",
        "number": "030458-0001",
        "client": "Venture Global",
        "pm": "Jorge R. Molano",
        "status": "Active",
        "initials": "VG",
        "open_pos": 0,
        "recent_receipts": 0,
        "awaiting_staging": 0,
        "fully_staged": 0
    },

    "williams-aquila": {
        "name": "Williams Aquila",
        "short_name": "Williams Aquila",
        "number": "Williams Aquila",
        "client": "Williams",
        "pm": "Gina Meins",
        "status": "Active",
        "initials": "WA",
        "open_pos": 9,
        "recent_receipts": 4,
        "awaiting_staging": 3,
        "fully_staged": 18
    },

    "drone-in-the-box": {
        "name": "Drone in the Box",
        "short_name": "Drone in the Box",
        "number": "030443-0003-EFAB",
        "client": "Shell",
        "pm": "Lezan",
        "status": "Active",
        "initials": "DB",
        "open_pos": 0,
        "recent_receipts": 0,
        "awaiting_staging": 0,
        "fully_staged": 0
    }
}


# ============================================================
# PURCHASE ORDERS
#
# Demo procurement data.
# ============================================================

PURCHASE_ORDERS = {

    "targa-butane": [],
    "bp-kaskida": [],
    "slb-hpu-skids": [],
    "venture-global": [],
    "drone-in-the-box": [],

    "williams-aquila": [

        {
            "po": "45001842",
            "vendor": "Graybar",
            "part": "5094-IB32",
            "description": "Digital Input Module",
            "ordered": 20,
            "received": 10,
            "remaining": 10,
            "status": "Partial Receipt"
        },

        {
            "po": "45001857",
            "vendor": "SCP",
            "part": "5094-IF8IH",
            "description": "Analog Input Module",
            "ordered": 8,
            "received": 8,
            "remaining": 0,
            "status": "Received"
        },

        {
            "po": "45001863",
            "vendor": "Lonestar",
            "part": "5094-OB16",
            "description": "Digital Output Module",
            "ordered": 12,
            "received": 0,
            "remaining": 12,
            "status": "Awaiting Receipt"
        },

        {
            "po": "45001871",
            "vendor": "Reynolds",
            "part": "1783-SFP1GLX",
            "description": "Fiber Transceiver",
            "ordered": 6,
            "received": 3,
            "remaining": 3,
            "status": "Partial Receipt"
        }
    ]
}


# ============================================================
# PROJECT SCHEDULES
# ============================================================

PROJECT_SCHEDULES = {

    "targa-butane": [
        {
            "package": "Targa Butane Dryer MCC Building",
            "number": "029434-0001-EFAB",
            "pm": "Leticia Zarpellon",

            "risk": (
                "Review loadout and lifting plan. "
                "UL field certification delays, exterior lights, "
                "and NCR review remain items to monitor."
            ),

            "milestones": [
                {
                    "activity": "Project Initiated",
                    "percent": 100,
                    "status": "Complete",
                    "target": "12/11/25"
                },
                {
                    "activity": "Drawings IFA",
                    "percent": 100,
                    "status": "Complete",
                    "target": "02/16/26"
                },
                {
                    "activity": "Drawings IFC",
                    "percent": 100,
                    "status": "Complete",
                    "target": "04/24/26"
                },
                {
                    "activity": "Procurement",
                    "percent": 100,
                    "status": "Complete",
                    "target": "05/20/26"
                },
                {
                    "activity": "Fabrication - Building",
                    "percent": 98,
                    "status": "On Track",
                    "target": "08/28/26*"
                },
                {
                    "activity": "Fabrication - Panels",
                    "percent": 99,
                    "status": "On Track",
                    "target": "08/28/26*"
                },
                {
                    "activity": "TRA Mechanical Inspection",
                    "percent": 100,
                    "status": "Complete",
                    "target": "08/05/26"
                },
                {
                    "activity": "Internal FAT - TRA Witness",
                    "percent": 0,
                    "status": "On Track",
                    "target": "09/03/26*"
                },
                {
                    "activity": "Client FAT",
                    "percent": None,
                    "status": "On Track",
                    "target": "09/14/26"
                },
                {
                    "activity": "Shipment",
                    "percent": None,
                    "status": "On Track",
                    "target": "09/24/26*"
                },
                {
                    "activity": "Drawings As-Built",
                    "percent": None,
                    "status": "On Track",
                    "target": "TBD"
                }
            ]
        }
    ],

    "bp-kaskida": [
        {
            "package": "BP Kaskida",
            "number": "028710-0001-EFAB",
            "pm": "Jie Deng",

            "risk": (
                "Review drawings at the UL508A level prior to "
                "construction. Intertek sticker relocation "
                "may slow production."
            ),

            "milestones": [
                {
                    "activity": "Procurement - Project",
                    "percent": 100,
                    "status": "Complete",
                    "target": "Complete"
                },
                {
                    "activity":
                        "Fabrication - Phase 1 Stage 2 Chem-Inject/IJB",
                    "percent": 50,
                    "status": "Behind",
                    "target": "09/04/26*"
                },
                {
                    "activity": "Fabrication - Project",
                    "percent": 10,
                    "status": "Behind",
                    "target": "TBD"
                },
                {
                    "activity": "Internal FAT - Phase 1 Stage 2 MCC",
                    "percent": 100,
                    "status": "Complete",
                    "target": "07/07/26"
                },
                {
                    "activity":
                        "Internal FAT - Phase 1 Stage 2 Chem-Inject/IJB",
                    "percent": 0,
                    "status": "Behind",
                    "target": "09/08/26*"
                },
                {
                    "activity": "Internal FAT - Project",
                    "percent": 5,
                    "status": "On Track",
                    "target": "TBD"
                },
                {
                    "activity": "Client FAT - Phase 1 Stage 2 MCC",
                    "percent": 100,
                    "status": "Complete",
                    "target": "07/08/26"
                },
                {
                    "activity":
                        "Client FAT - Phase 1 Stage 2 Chem-Inject/IJB",
                    "percent": 0,
                    "status": "Behind",
                    "target": "09/11/26*"
                },
                {
                    "activity": "Client FAT - Project",
                    "percent": 5,
                    "status": "On Track",
                    "target": "TBD"
                },
                {
                    "activity": "Punchlist - Phase 1 Stage 2 MCC",
                    "percent": 100,
                    "status": "Complete",
                    "target": "08/07/26"
                },
                {
                    "activity":
                        "Punchlist - Phase 1 Stage 2 Chem-Inject/IJB",
                    "percent": 0,
                    "status": "Behind",
                    "target": "09/16/26*"
                },
                {
                    "activity": "Drawings As-Built - Phase 1 Stage 1",
                    "percent": 100,
                    "status": "Complete",
                    "target": "Complete"
                },
                {
                    "activity": "Drawings As-Built - Phase 1 Stage 2 MCC",
                    "percent": 75,
                    "status": "Behind",
                    "target": "08/31/26*"
                },
                {
                    "activity": "Shipment Inspection - Phase 1 Stage 2 MCC",
                    "percent": 0,
                    "status": "On Track",
                    "target": "09/14/26"
                }
            ]
        }
    ],

    "slb-hpu-skids": [
        {
            "package": "SLB HPU Skids",
            "number": "027682-0003",
            "pm": "Jorge R. Molano",

            "risk": (
                "Verify missing materials, review SLB FAT procedure, "
                "and determine whether onsite inspections are required. "
                "Partial internal QC remains a schedule risk."
            ),

            "milestones": [
                {
                    "activity": "Project Initiated",
                    "percent": 100,
                    "status": "Complete",
                    "target": "Complete"
                },
                {
                    "activity": "Drawings IFA",
                    "percent": 100,
                    "status": "Complete",
                    "target": "Complete"
                },
                {
                    "activity": "Drawings IFC",
                    "percent": 100,
                    "status": "Complete",
                    "target": "Complete"
                },
                {
                    "activity": "Procurement",
                    "percent": 98,
                    "status": "Behind",
                    "target": "TBD"
                },
                {
                    "activity": "Fabrication",
                    "percent": 90,
                    "status": "Behind",
                    "target": "TBD"
                },
                {
                    "activity": "Internal FAT",
                    "percent": 0,
                    "status": "Behind",
                    "target": "09/04/26*"
                },
                {
                    "activity": "Client FAT",
                    "percent": 0,
                    "status": "Behind",
                    "target": "09/09/26*"
                },
                {
                    "activity": "Shipment Inspection",
                    "percent": 0,
                    "status": "Behind",
                    "target": "09/14/26*"
                },
                {
                    "activity": "Drawings As-Built",
                    "percent": 0,
                    "status": "On Track",
                    "target": "09/18/26"
                }
            ]
        }
    ],

    "venture-global": [
        {
            "package": "Venture Global LNG Expanders",
            "number": "030458-0001",
            "pm": "Jorge R. Molano",

            "risk": "Coordinate potential inventory shift with BP.",

            "milestones": [
                {
                    "activity": "Project Initiated",
                    "percent": 100,
                    "status": "Complete",
                    "target": "Complete"
                },
                {
                    "activity": "Drawings IFA",
                    "percent": 100,
                    "status": "Complete",
                    "target": "Complete"
                },
                {
                    "activity": "Drawings IFC",
                    "percent": 100,
                    "status": "Complete",
                    "target": "Complete"
                },
                {
                    "activity": "Procurement - BPCS/SIS",
                    "percent": 100,
                    "status": "Complete",
                    "target": "04/27/26"
                },
                {
                    "activity": "Procurement - HIPS",
                    "percent": 100,
                    "status": "Complete",
                    "target": "05/15/26"
                },
                {
                    "activity": "Fabrication - BPCS/SIS",
                    "percent": 100,
                    "status": "Complete",
                    "target": "09/04/26"
                },
                {
                    "activity": "Fabrication - HIPS",
                    "percent": 100,
                    "status": "Complete",
                    "target": "09/04/26"
                },
                {
                    "activity": "Internal FAT - BPCS/SIS",
                    "percent": 100,
                    "status": "Complete",
                    "target": "07/14/26"
                },
                {
                    "activity": "Internal FAT - HIPS",
                    "percent": 100,
                    "status": "Complete",
                    "target": "07/14/26"
                },
                {
                    "activity": "Client FAT - Project",
                    "percent": 100,
                    "status": "Complete",
                    "target": "07/27/26"
                },
                {
                    "activity": "Punchlist Inspection",
                    "percent": 95,
                    "status": "On Track",
                    "target": "09/04/26*"
                },
                {
                    "activity": "Shipment",
                    "percent": 0,
                    "status": "On Track",
                    "target": "09/10/26*"
                },
                {
                    "activity": "Drawings As-Built",
                    "percent": 0,
                    "status": "On Track",
                    "target": "TBD"
                }
            ]
        }
    ],

    "williams-aquila": [

        {
            "package": "BESS Cabinets",
            "number": "031674-0001",
            "pm": "Gina Meins",
            "risk": "Scope change. Update Williams drawings.",

            "milestones": [
                {
                    "activity": "Project Initiated",
                    "percent": 100,
                    "status": "Complete",
                    "target": "05/22/26"
                },
                {
                    "activity": "Drawings IFA",
                    "percent": 100,
                    "status": "Complete",
                    "target": "Complete"
                },
                {
                    "activity": "Drawings IFC",
                    "percent": 75,
                    "status": "On Track",
                    "target": "09/11/26"
                },
                {
                    "activity": "Procurement",
                    "percent": 100,
                    "status": "Complete",
                    "target": "06/03/26"
                },
                {
                    "activity": "Fabrication",
                    "percent": 0,
                    "status": "On Track",
                    "target": "10/02/26*"
                },
                {
                    "activity": "Internal FAT",
                    "percent": 0,
                    "status": "On Track",
                    "target": "10/09/26*"
                },
                {
                    "activity": "Client FAT",
                    "percent": 0,
                    "status": "On Track",
                    "target": "10/13/26*"
                },
                {
                    "activity": "Shipment Inspection",
                    "percent": 0,
                    "status": "On Track",
                    "target": "10/16/26*"
                },
                {
                    "activity": "Drawings As-Built",
                    "percent": 0,
                    "status": "On Track",
                    "target": "TBD"
                }
            ]
        },

        {
            "package": "PLC Panels",
            "number": "031689-0001",
            "pm": "Gina Meins",

            "risk": (
                "Long lead items may affect the schedule. "
                "Review change order. Redesign is in progress."
            ),

            "milestones": [
                {
                    "activity": "Project Initiated",
                    "percent": 100,
                    "status": "Complete",
                    "target": "05/22/26"
                },
                {
                    "activity": "Drawings IFA",
                    "percent": 100,
                    "status": "Complete",
                    "target": "06/15/26"
                },
                {
                    "activity": "Drawings IFP - RIOs Package",
                    "percent": 50,
                    "status": "On Track",
                    "target": "09/04/26"
                },
                {
                    "activity": "Procurement - RIOs x2",
                    "percent": 100,
                    "status": "Complete",
                    "target": "06/03/26"
                },
                {
                    "activity": "Procurement - RIOs x9",
                    "percent": 0,
                    "status": "On Track",
                    "target": "06/29/26"
                },
                {
                    "activity": "Procurement - SCP",
                    "percent": 100,
                    "status": "Complete",
                    "target": "06/03/26"
                },
                {
                    "activity": "Procurement - ESD",
                    "percent": 100,
                    "status": "Complete",
                    "target": "06/03/26"
                },
                {
                    "activity": "Fabrication - RIOs x2",
                    "percent": 100,
                    "status": "Complete",
                    "target": "08/17/26"
                },
                {
                    "activity": "Fabrication - Project",
                    "percent": 0,
                    "status": "On Track",
                    "target": "TBD"
                },
                {
                    "activity": "Internal FAT - RIOs x2",
                    "percent": 0,
                    "status": "On Track",
                    "target": "09/14/26"
                },
                {
                    "activity": "Client FAT - RIOs x2",
                    "percent": 0,
                    "status": "On Track",
                    "target": "09/22/26*"
                },
                {
                    "activity": "Shipment Inspection - RIOs x2",
                    "percent": 0,
                    "status": "On Track",
                    "target": "09/30/26*"
                },
                {
                    "activity": "Drawings As-Built",
                    "percent": 0,
                    "status": "On Track",
                    "target": "TBD"
                }
            ]
        },

        {
            "package": "Server Cabinets",
            "number": "031687-0001",
            "pm": "Gina Meins",
            "risk": "Scope change.",

            "milestones": [
                {
                    "activity": "Project Initiated",
                    "percent": 100,
                    "status": "Complete",
                    "target": "05/22/26"
                },
                {
                    "activity": "Drawings IFA",
                    "percent": 100,
                    "status": "Complete",
                    "target": "08/04/26"
                },
                {
                    "activity": "Drawings IFC",
                    "percent": 100,
                    "status": "On Track",
                    "target": "08/04/26"
                },
                {
                    "activity": "Procurement - Long Lead",
                    "percent": 100,
                    "status": "Complete",
                    "target": "06/03/26"
                },
                {
                    "activity": "Procurement",
                    "percent": 85,
                    "status": "On Track",
                    "target": "09/02/26"
                },
                {
                    "activity": "Fabrication",
                    "percent": 0,
                    "status": "On Track",
                    "target": "10/15/26"
                },
                {
                    "activity": "Internal FAT",
                    "percent": 0,
                    "status": "On Track",
                    "target": "11/07/26"
                },
                {
                    "activity": "Client FAT",
                    "percent": 0,
                    "status": "On Track",
                    "target": "11/15/26"
                },
                {
                    "activity": "Shipment Inspection",
                    "percent": 0,
                    "status": "On Track",
                    "target": "11/18/26"
                },
                {
                    "activity": "Drawings As-Built",
                    "percent": 0,
                    "status": "On Track",
                    "target": "N/A"
                }
            ]
        },

        {
            "package": "FNE Cabinets",
            "number": "031791-0001",
            "pm": "Gina Meins",

            "risk": (
                "Approved drawings needed. Allocate resource "
                "and time for review."
            ),

            "milestones": [
                {
                    "activity": "Project Initiated",
                    "percent": 100,
                    "status": "Complete",
                    "target": "Complete"
                },
                {
                    "activity": "Drawings IFA",
                    "percent": 50,
                    "status": "On Track",
                    "target": "09/08/26"
                },
                {
                    "activity": "Drawings IFC",
                    "percent": 0,
                    "status": "On Track",
                    "target": "09/23/26"
                },
                {
                    "activity": "Procurement",
                    "percent": 95,
                    "status": "On Track",
                    "target": "TBD"
                },
                {
                    "activity": "Fabrication",
                    "percent": 0,
                    "status": "On Track",
                    "target": "09/23/26*"
                },
                {
                    "activity": "Internal FAT",
                    "percent": 0,
                    "status": "On Track",
                    "target": "TBD"
                },
                {
                    "activity": "Client FAT",
                    "percent": 0,
                    "status": "On Track",
                    "target": "TBD"
                },
                {
                    "activity": "Shipment Inspection",
                    "percent": 0,
                    "status": "On Track",
                    "target": "TBD"
                },
                {
                    "activity": "Drawings As-Built",
                    "percent": 0,
                    "status": "On Track",
                    "target": "TBD"
                }
            ]
        }
    ],

    "drone-in-the-box": [
        {
            "package": "Drone in the Box",
            "number": "030443-0003-EFAB",
            "pm": "Lezan",

            "risk": (
                "Coordinate heavy forklift alignment with skid arrival. "
                "Update drawings and review conduit fittings. Inspection "
                "should occur before blast and painting."
            ),

            "milestones": [
                {
                    "activity": "Project Initiated",
                    "percent": 100,
                    "status": "Complete",
                    "target": "Complete"
                },
                {
                    "activity": "Drawings IFA",
                    "percent": 100,
                    "status": "Complete",
                    "target": "Complete"
                },
                {
                    "activity": "Drawings IFC",
                    "percent": 100,
                    "status": "Complete",
                    "target": "Complete"
                },
                {
                    "activity": "Procurement - Long Lead",
                    "percent": 100,
                    "status": "Complete",
                    "target": "Complete"
                },
                {
                    "activity": "Procurement",
                    "percent": 100,
                    "status": "Complete",
                    "target": "Complete"
                },
                {
                    "activity": "Skid Inspection at Manufacturer",
                    "percent": 100,
                    "status": "Complete",
                    "target": "08/26/26"
                },
                {
                    "activity": "Receipt of Skid",
                    "percent": 0,
                    "status": "On Track",
                    "target": "09/02/26*"
                },
                {
                    "activity": "Receipt of Enclosure",
                    "percent": 0,
                    "status": "On Track",
                    "target": "09/02/26"
                },
                {
                    "activity": "Fabrication",
                    "percent": 0,
                    "status": "On Track",
                    "target": "09/03/26"
                },
                {
                    "activity": "Internal FAT",
                    "percent": 0,
                    "status": "On Track",
                    "target": "09/21/26"
                },
                {
                    "activity": "Client FAT",
                    "percent": 0,
                    "status": "On Track",
                    "target": "09/28/26"
                },
                {
                    "activity": "Shipment Inspection",
                    "percent": 0,
                    "status": "On Track",
                    "target": "09/30/26"
                },
                {
                    "activity": "Drawings As-Built",
                    "percent": 0,
                    "status": "On Track",
                    "target": "TBD"
                }
            ]
        }
    ]
}


# ============================================================
# PROJECT MENU
# ============================================================

@app.context_processor
def inject_projects_menu():

    return {
        "projects_menu": PROJECTS
    }


# ============================================================
# HOME
# ============================================================

@app.route("/")
def index():

    return redirect(
        url_for("tech_center_home")
    )


@app.route("/tech-center")
def tech_center_home():

    return render_template(
        "tech_center_home.html",
        projects=PROJECTS
    )


# ============================================================
# MATERIALS MANAGEMENT
#
# READS DIRECTLY FROM SQLITE.
# ============================================================

@app.route("/materials")
def materials():

    receipts = get_all_receipts()

    return render_template(
        "materials_management.html",
        receipts=receipts
    )


# ============================================================
# STAGE MATERIAL
#
# WRITES DIRECTLY TO SQLITE.
# ============================================================

@app.route(
    "/materials/stage",
    methods=["POST"]
)
def stage_material():

    data = request.get_json(
        silent=True
    )

    if not data:

        return jsonify({
            "success": False,
            "message":
                "No staging data was received."
        }), 400


    receipt_nbr = str(
        data.get(
            "receipt_nbr",
            ""
        )
    ).strip()


    location = str(
        data.get(
            "location",
            ""
        )
    ).strip()


    try:

        quantity = int(
            data.get(
                "quantity",
                0
            )
        )

    except (
        TypeError,
        ValueError
    ):

        quantity = 0


    result = stage_receipt_material(
        receipt_nbr=receipt_nbr,
        quantity=quantity,
        location=location,
        staged_by="Myska Nasiri"
    )


    if not result["success"]:

        if (
            result["message"]
            == "Receipt was not found."
        ):

            return jsonify(
                result
            ), 404

        return jsonify(
            result
        ), 400


    return jsonify(
        result
    ), 200


# ============================================================
# PROJECTS COMPATIBILITY ROUTE
# ============================================================

@app.route("/projects")
def projects():

    return redirect(
        url_for("tech_center_home")
    )


# ============================================================
# PROJECT DASHBOARD
# ============================================================

@app.route(
    "/projects/<project_slug>"
)
def project_dashboard(project_slug):

    project = PROJECTS.get(
        project_slug
    )

    if not project:
        abort(404)


    purchase_orders = (
        PURCHASE_ORDERS.get(
            project_slug,
            []
        )
    )


    schedule = (
        PROJECT_SCHEDULES.get(
            project_slug,
            []
        )
    )


    materials_data = (
        get_receipts_by_project(
            project_slug
        )
    )


    return render_template(
        "project_dashboard.html",

        project=project,
        project_slug=project_slug,

        purchase_orders=
            purchase_orders,

        materials=
            materials_data,

        schedule=
            schedule
    )


# ============================================================
# PROJECT PURCHASE ORDERS
# ============================================================

@app.route(
    "/projects/<project_slug>/purchase-orders"
)
def project_purchase_orders(project_slug):

    project = PROJECTS.get(
        project_slug
    )

    if not project:
        abort(404)


    purchase_orders = (
        PURCHASE_ORDERS.get(
            project_slug,
            []
        )
    )


    return render_template(
        "project_purchase_orders.html",

        project=project,

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
def project_schedule(project_slug):

    project = PROJECTS.get(
        project_slug
    )

    if not project:
        abort(404)


    schedule = (
        PROJECT_SCHEDULES.get(
            project_slug,
            []
        )
    )


    return render_template(
        "project_schedule.html",

        project=project,

        project_slug=
            project_slug,

        schedule=
            schedule
    )


# ============================================================
# PROJECT MATERIALS
#
# THIS NOW READS FROM THE SAME SQLITE DATABASE TOO.
# ============================================================

@app.route(
    "/projects/<project_slug>/materials"
)
def project_materials(project_slug):

    project = PROJECTS.get(
        project_slug
    )

    if not project:
        abort(404)


    receipt_rows = (
        get_receipts_by_project(
            project_slug
        )
    )


    # Convert the SQLite receipt structure into the field
    # names expected by the existing project_materials.html
    # template.

    materials_data = []

    for receipt in receipt_rows:

        materials_data.append({
            "receipt":
                receipt["receipt_nbr"],

            "po":
                receipt["po_nbr"],

            "part":
                receipt["inventory_id"],

            "description":
                receipt["description"],

            "received":
                receipt["receipt_qty"],

            "staged":
                receipt["staged_qty"],

            "remaining":
                receipt["remaining_to_stage"],

            "location":
                receipt["storage_location"],

            "status":
                receipt["staging_status"]
        })


    return render_template(
        "project_materials.html",

        project=project,

        project_slug=
            project_slug,

        materials=
            materials_data
    )


# ============================================================
# REPORTING
# ============================================================

@app.route("/reporting")
def reporting():

    return """
        <h2>Reporting</h2>

        <p>
            Tech Center reporting workspace coming next.
        </p>
    """


# ============================================================
# RUN FLASK
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=True,
        port=5001,
        use_reloader=False
    )