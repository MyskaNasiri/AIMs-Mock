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


# ============================================================
# APP
# ============================================================

app = Flask(__name__)

initialize_database()
initialize_reporting_database()


# ============================================================
# PROJECTS
# ============================================================

PROJECTS = {

    "targa-butane": {
        "name": "Targa Butane Dryer MCC Building",
        "short_name": "Targa Butane",
        "project_number": "029434-0001-EFAB",
        "number": "029434-0001-EFAB",
        "client": "Targa",
        "pm": "Leticia Zarpellon",
        "initials": "TB",
        "status": "Active"
    },

    "bp-kaskida": {
        "name": "BP Kaskida",
        "short_name": "BP Kaskida",
        "project_number": "028710-0001-EFAB",
        "number": "028710-0001-EFAB",
        "client": "BP",
        "pm": "Jie Deng",
        "initials": "BP",
        "status": "Active"
    },

    "slb-hpu-skids": {
        "name": "SLB HPU Skids",
        "short_name": "SLB HPU Skids",
        "project_number": "027682-0003",
        "number": "027682-0003",
        "client": "SLB",
        "pm": "Jorge R. Molano",
        "initials": "SL",
        "status": "Active"
    },

    "venture-global": {
        "name": "Venture Global LNG Expanders",
        "short_name": "Venture Global",
        "project_number": "030458-0001",
        "number": "030458-0001",
        "client": "Venture Global",
        "pm": "Jorge R. Molano",
        "initials": "VG",
        "status": "Active"
    },

    "williams-aquila": {
        "name": "Williams Aquila",
        "short_name": "Williams Aquila",

        # Used elsewhere in the prototype
        "project_number": "Williams Aquila",

        # Used by project_schedule.html
        "number": "Williams Aquila",

        "client": "Williams",
        "pm": "Gina Meins",
        "initials": "WA",
        "status": "Active",

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
        "number": "030443-0003-EFAB",
        "client": "Shell",
        "pm": "Lezan",
        "initials": "DB",
        "status": "Active"
    }

}


# ============================================================
# PURCHASE ORDERS
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
#
# IMPORTANT:
# project_schedule.html expects:
#
# schedule = [
#     {
#         "package": ...,
#         "project_number": ...,
#         "pm": ...,
#         "risk": ...,
#         "milestones": [
#             {
#                 "description": ...,
#                 "percent": ...,
#                 "status": ...,
#                 "date": ...
#             }
#         ]
#     }
# ]
# ============================================================

PROJECT_SCHEDULES = {

    # ========================================================
    # TARGA
    # ========================================================

    "targa-butane": [

        {
            "package": "Targa Butane Dryer MCC Building",
            "project_number": "029434-0001-EFAB",
            "pm": "Leticia Zarpellon",

            "risk": (
                "Review loadout and lifting requirements. "
                "UL certification and exterior lighting / NCR "
                "items remain under review."
            ),

            "milestones": [

                {
                    "description": "Initiated",
                    "percent": 100,
                    "status": "Complete",
                    "date": "12/11/25"
                },

                {
                    "description": "IFA",
                    "percent": 100,
                    "status": "Complete",
                    "date": "02/16/26"
                },

                {
                    "description": "IFC",
                    "percent": 100,
                    "status": "Complete",
                    "date": "04/24/26"
                },

                {
                    "description": "Procurement",
                    "percent": 100,
                    "status": "Complete",
                    "date": "05/20/26"
                },

                {
                    "description": "Fabrication Building",
                    "percent": 98,
                    "status": "On Track",
                    "date": "08/28/26*"
                },

                {
                    "description": "Fabrication Panels",
                    "percent": 99,
                    "status": "On Track",
                    "date": "08/28/26*"
                },

                {
                    "description": "TRA Mechanical Inspection",
                    "percent": 100,
                    "status": "Complete",
                    "date": "08/05/26"
                },

                {
                    "description": "Internal FAT - TRA Witness",
                    "percent": 0,
                    "status": "On Track",
                    "date": "09/03/26*"
                },

                {
                    "description": "Client FAT",
                    "percent": 0,
                    "status": "On Track",
                    "date": "09/14/26"
                },

                {
                    "description": "Shipment",
                    "percent": 0,
                    "status": "On Track",
                    "date": "09/24/26*"
                },

                {
                    "description": "As-Built",
                    "percent": 0,
                    "status": "On Track",
                    "date": "TBD"
                }

            ]
        }

    ],


    # ========================================================
    # BP KASKIDA
    # ========================================================

    "bp-kaskida": [

        {
            "package": "BP Kaskida",
            "project_number": "028710-0001-EFAB",
            "pm": "Jie Deng",

            "risk": (
                "UL508A drawing requirements and Intertek "
                "sticker coordination remain under review."
            ),

            "milestones": [

                {
                    "description": "Procurement Project",
                    "percent": 100,
                    "status": "Complete",
                    "date": "Complete"
                },

                {
                    "description": (
                        "Fabrication Phase 1 Stage 2 "
                        "Chem-Inject / IJB"
                    ),
                    "percent": 50,
                    "status": "Behind",
                    "date": "09/04/26*"
                },

                {
                    "description": "Fabrication Project",
                    "percent": 10,
                    "status": "Behind",
                    "date": "TBD"
                },

                {
                    "description": (
                        "Internal FAT Phase 1 Stage 2 MCC"
                    ),
                    "percent": 100,
                    "status": "Complete",
                    "date": "07/07/26"
                },

                {
                    "description": (
                        "Internal FAT Phase 1 Stage 2 "
                        "Chem-Inject / IJB"
                    ),
                    "percent": 0,
                    "status": "Behind",
                    "date": "09/08/26*"
                },

                {
                    "description": "Internal FAT Project",
                    "percent": 5,
                    "status": "On Track",
                    "date": "TBD"
                },

                {
                    "description": (
                        "Client FAT Phase 1 Stage 2 MCC"
                    ),
                    "percent": 100,
                    "status": "Complete",
                    "date": "07/08/26"
                },

                {
                    "description": (
                        "Client FAT Phase 1 Stage 2 "
                        "Chem-Inject / IJB"
                    ),
                    "percent": 0,
                    "status": "Behind",
                    "date": "09/11/26*"
                },

                {
                    "description": "Client FAT Project",
                    "percent": 5,
                    "status": "On Track",
                    "date": "TBD"
                },

                {
                    "description": (
                        "Punchlist Phase 1 Stage 2 MCC"
                    ),
                    "percent": 100,
                    "status": "Complete",
                    "date": "08/07/26"
                },

                {
                    "description": (
                        "Punchlist Phase 1 Stage 2 "
                        "Chem-Inject / IJB"
                    ),
                    "percent": 0,
                    "status": "Behind",
                    "date": "09/16/26*"
                },

                {
                    "description": "As-Built Phase 1 Stage 1",
                    "percent": 100,
                    "status": "Complete",
                    "date": "Complete"
                },

                {
                    "description": (
                        "As-Built Phase 1 Stage 2 MCC"
                    ),
                    "percent": 75,
                    "status": "Behind",
                    "date": "08/31/26*"
                },

                {
                    "description": (
                        "Shipment Inspection "
                        "Phase 1 Stage 2 MCC"
                    ),
                    "percent": 0,
                    "status": "On Track",
                    "date": "09/14/26"
                }

            ]
        }

    ],


    # ========================================================
    # SLB
    # ========================================================

    "slb-hpu-skids": [

        {
            "package": "SLB HPU Skids",
            "project_number": "027682-0003",
            "pm": "Jorge R. Molano",

            "risk": (
                "Missing materials, FAT procedure coordination, "
                "onsite inspections, and partial QC may affect "
                "the schedule."
            ),

            "milestones": [

                {
                    "description": "Initiated",
                    "percent": 100,
                    "status": "Complete",
                    "date": "Complete"
                },

                {
                    "description": "IFA",
                    "percent": 100,
                    "status": "Complete",
                    "date": "Complete"
                },

                {
                    "description": "IFC",
                    "percent": 100,
                    "status": "Complete",
                    "date": "Complete"
                },

                {
                    "description": "Procurement",
                    "percent": 98,
                    "status": "Behind",
                    "date": "TBD"
                },

                {
                    "description": "Fabrication",
                    "percent": 90,
                    "status": "Behind",
                    "date": "TBD"
                },

                {
                    "description": "Internal FAT",
                    "percent": 0,
                    "status": "Behind",
                    "date": "09/04/26*"
                },

                {
                    "description": "Client FAT",
                    "percent": 0,
                    "status": "Behind",
                    "date": "09/09/26*"
                },

                {
                    "description": "Shipment Inspection",
                    "percent": 0,
                    "status": "Behind",
                    "date": "09/14/26*"
                },

                {
                    "description": "As-Built",
                    "percent": 0,
                    "status": "On Track",
                    "date": "09/18/26"
                }

            ]
        }

    ],


    # ========================================================
    # VENTURE GLOBAL
    # ========================================================

    "venture-global": [

        {
            "package": "Venture Global LNG Expanders",
            "project_number": "030458-0001",
            "pm": "Jorge R. Molano",

            "risk": (
                "Inventory timing may shift due to BP "
                "fabrication priorities."
            ),

            "milestones": [

                {
                    "description": "Initiated",
                    "percent": 100,
                    "status": "Complete",
                    "date": "Complete"
                },

                {
                    "description": "IFA",
                    "percent": 100,
                    "status": "Complete",
                    "date": "Complete"
                },

                {
                    "description": "IFC",
                    "percent": 100,
                    "status": "Complete",
                    "date": "Complete"
                },

                {
                    "description": "Procurement BPCS / SIS",
                    "percent": 100,
                    "status": "Complete",
                    "date": "04/27/26"
                },

                {
                    "description": "Procurement HIPS",
                    "percent": 100,
                    "status": "Complete",
                    "date": "05/15/26"
                },

                {
                    "description": "Fabrication BPCS / SIS",
                    "percent": 100,
                    "status": "Complete",
                    "date": "09/04/26"
                },

                {
                    "description": "Fabrication HIPS",
                    "percent": 100,
                    "status": "Complete",
                    "date": "09/04/26"
                },

                {
                    "description": (
                        "Internal FAT BPCS / SIS / HIPS"
                    ),
                    "percent": 100,
                    "status": "Complete",
                    "date": "07/14/26"
                },

                {
                    "description": "Client FAT Project",
                    "percent": 100,
                    "status": "Complete",
                    "date": "07/27/26"
                },

                {
                    "description": "Punchlist",
                    "percent": 95,
                    "status": "On Track",
                    "date": "09/04/26*"
                },

                {
                    "description": "Shipment",
                    "percent": 0,
                    "status": "On Track",
                    "date": "09/10/26*"
                },

                {
                    "description": "As-Built",
                    "percent": 0,
                    "status": "On Track",
                    "date": "TBD"
                }

            ]
        }

    ],


    # ========================================================
    # WILLIAMS AQUILA
    # ========================================================

    "williams-aquila": [

        # ====================================================
        # BESS
        # ====================================================

        {
            "package": "BESS",
            "project_number": "031674-0001",
            "pm": "Gina Meins",

            "risk": (
                "BESS scope changes may require drawing updates "
                "and coordination before fabrication."
            ),

            "milestones": [

                {
                    "description": "Initiated",
                    "percent": 100,
                    "status": "Complete",
                    "date": "05/22/26"
                },

                {
                    "description": "IFA",
                    "percent": 100,
                    "status": "Complete",
                    "date": "Complete"
                },

                {
                    "description": "IFC",
                    "percent": 75,
                    "status": "On Track",
                    "date": "09/11/26"
                },

                {
                    "description": "Procurement",
                    "percent": 100,
                    "status": "Complete",
                    "date": "06/03/26"
                },

                {
                    "description": "Fabrication",
                    "percent": 0,
                    "status": "On Track",
                    "date": "10/02/26*"
                },

                {
                    "description": "Internal FAT",
                    "percent": 0,
                    "status": "On Track",
                    "date": "10/09/26*"
                },

                {
                    "description": "Client FAT",
                    "percent": 0,
                    "status": "On Track",
                    "date": "10/13/26*"
                },

                {
                    "description": "Shipment Inspection",
                    "percent": 0,
                    "status": "On Track",
                    "date": "10/16/26*"
                },

                {
                    "description": "As-Built",
                    "percent": 0,
                    "status": "On Track",
                    "date": "TBD"
                }

            ]
        },


        # ====================================================
        # PLC PANELS
        # ====================================================

        {
            "package": "PLC Panels",
            "project_number": "031689-0001",
            "pm": "Gina Meins",

            "risk": (
                "PLC package includes multiple RIO panel groups "
                "and long-lead materials that require continued "
                "tracking."
            ),

            "milestones": [

                {
                    "description": "Initiated",
                    "percent": 100,
                    "status": "Complete",
                    "date": "05/22/26"
                },

                {
                    "description": "IFA",
                    "percent": 100,
                    "status": "Complete",
                    "date": "06/15/26"
                },

                {
                    "description": "IFP RIOs Package",
                    "percent": 50,
                    "status": "On Track",
                    "date": "09/04/26"
                },

                {
                    "description": "Procurement - RIOs x2",
                    "percent": 100,
                    "status": "Complete",
                    "date": "06/03/26"
                },

                {
                    "description": "Procurement - RIOs x9",
                    "percent": 0,
                    "status": "On Track",
                    "date": "06/29/26"
                },

                {
                    "description": "Procurement - SCP",
                    "percent": 100,
                    "status": "Complete",
                    "date": "06/03/26"
                },

                {
                    "description": "Procurement - ESD",
                    "percent": 100,
                    "status": "Complete",
                    "date": "06/03/26"
                },

                {
                    "description": "Fabrication - RIOs x2",
                    "percent": 100,
                    "status": "Complete",
                    "date": "08/17/26"
                },

                {
                    "description": "Fabrication - Project",
                    "percent": 0,
                    "status": "On Track",
                    "date": "TBD"
                },

                {
                    "description": "Internal FAT - RIOs x2",
                    "percent": 0,
                    "status": "On Track",
                    "date": "09/14/26"
                },

                {
                    "description": "Client FAT - RIOs x2",
                    "percent": 0,
                    "status": "On Track",
                    "date": "09/22/26*"
                },

                {
                    "description": (
                        "Shipment Inspection - RIOs x2"
                    ),
                    "percent": 0,
                    "status": "On Track",
                    "date": "09/30/26*"
                },

                {
                    "description": "As-Built",
                    "percent": 0,
                    "status": "On Track",
                    "date": "TBD"
                }

            ]
        },


        # ====================================================
        # SERVER
        # ====================================================

        {
            "package": "Server",
            "project_number": "031687-0001",
            "pm": "Gina Meins",

            "risk": (
                "Server scope and procurement timing should "
                "continue to be reviewed as fabrication "
                "approaches."
            ),

            "milestones": [

                {
                    "description": "Initiated",
                    "percent": 100,
                    "status": "Complete",
                    "date": "05/22/26"
                },

                {
                    "description": "IFA",
                    "percent": 100,
                    "status": "Complete",
                    "date": "08/04/26"
                },

                {
                    "description": "IFC",
                    "percent": 100,
                    "status": "Complete",
                    "date": "08/04/26"
                },

                {
                    "description": "Procurement - Long Lead",
                    "percent": 100,
                    "status": "Complete",
                    "date": "06/03/26"
                },

                {
                    "description": "Procurement",
                    "percent": 85,
                    "status": "On Track",
                    "date": "09/02/26"
                },

                {
                    "description": "Fabrication",
                    "percent": 0,
                    "status": "On Track",
                    "date": "10/15/26"
                },

                {
                    "description": "Internal FAT",
                    "percent": 0,
                    "status": "On Track",
                    "date": "11/07/26"
                },

                {
                    "description": "Client FAT",
                    "percent": 0,
                    "status": "On Track",
                    "date": "11/15/26"
                },

                {
                    "description": "Shipment Inspection",
                    "percent": 0,
                    "status": "On Track",
                    "date": "11/18/26"
                },

                {
                    "description": "As-Built",
                    "percent": 0,
                    "status": "On Track",
                    "date": "N/A"
                }

            ]
        },


        # ====================================================
        # FNE
        # ====================================================

        {
            "package": "FNE",
            "project_number": "031791-0001",
            "pm": "Gina Meins",

            "risk": (
                "Approved drawings, procurement completion, "
                "and fabrication readiness remain under review."
            ),

            "milestones": [

                {
                    "description": "Initiated",
                    "percent": 100,
                    "status": "Complete",
                    "date": "Complete"
                },

                {
                    "description": "IFA",
                    "percent": 50,
                    "status": "On Track",
                    "date": "09/08/26"
                },

                {
                    "description": "IFC",
                    "percent": 0,
                    "status": "On Track",
                    "date": "09/23/26"
                },

                {
                    "description": "Procurement",
                    "percent": 95,
                    "status": "On Track",
                    "date": "TBD"
                },

                {
                    "description": "Fabrication",
                    "percent": 0,
                    "status": "On Track",
                    "date": "09/23/26*"
                },

                {
                    "description": "Internal FAT",
                    "percent": 0,
                    "status": "On Track",
                    "date": "TBD"
                },

                {
                    "description": "Client FAT",
                    "percent": 0,
                    "status": "On Track",
                    "date": "TBD"
                },

                {
                    "description": "Shipment",
                    "percent": 0,
                    "status": "On Track",
                    "date": "TBD"
                },

                {
                    "description": "As-Built",
                    "percent": 0,
                    "status": "On Track",
                    "date": "TBD"
                }

            ]
        }

    ],


    # ========================================================
    # DRONE IN THE BOX
    # ========================================================

    "drone-in-the-box": [

        {
            "package": "Drone in the Box",
            "project_number": "030443-0003-EFAB",
            "pm": "Lezan",

            "risk": (
                "Forklift and skid timing, drawing updates, "
                "conduit fittings, and enclosure inspection "
                "before blast and paint require coordination."
            ),

            "milestones": [

                {
                    "description": "Initiated",
                    "percent": 100,
                    "status": "Complete",
                    "date": "Complete"
                },

                {
                    "description": "IFA",
                    "percent": 100,
                    "status": "Complete",
                    "date": "Complete"
                },

                {
                    "description": "IFC",
                    "percent": 100,
                    "status": "Complete",
                    "date": "Complete"
                },

                {
                    "description": "Procurement Long Lead",
                    "percent": 100,
                    "status": "Complete",
                    "date": "Complete"
                },

                {
                    "description": "Procurement",
                    "percent": 100,
                    "status": "Complete",
                    "date": "Complete"
                },

                {
                    "description": "Skid Inspection Manufacturer",
                    "percent": 100,
                    "status": "Complete",
                    "date": "08/26/26"
                },

                {
                    "description": "Receipt Skid",
                    "percent": 0,
                    "status": "On Track",
                    "date": "09/02/26*"
                },

                {
                    "description": "Receipt Enclosure",
                    "percent": 0,
                    "status": "On Track",
                    "date": "09/02/26"
                },

                {
                    "description": "Fabrication",
                    "percent": 0,
                    "status": "On Track",
                    "date": "09/03/26"
                },

                {
                    "description": "Internal FAT",
                    "percent": 0,
                    "status": "On Track",
                    "date": "09/21/26"
                },

                {
                    "description": "Client FAT",
                    "percent": 0,
                    "status": "On Track",
                    "date": "09/28/26"
                },

                {
                    "description": "Shipment Inspection",
                    "percent": 0,
                    "status": "On Track",
                    "date": "09/30/26"
                },

                {
                    "description": "As-Built",
                    "percent": 0,
                    "status": "On Track",
                    "date": "TBD"
                }

            ]
        }

    ]

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
        url_for("tech_center_home")
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

    all_receipt_groups = get_receipt_groups()

    receipt_groups = [
        receipt
        for receipt in all_receipt_groups
        if not receipt["receipt_nbr"].startswith(
            "POR-DEMO-"
        )
    ]

    return render_template(
        "materials_management.html",
        receipt_groups=receipt_groups,
        receipts=get_all_receipts(),
        warehouse_materials=get_warehouse_materials()
    )


# ============================================================
# STAGE MATERIAL
# ============================================================

@app.route(
    "/materials/stage",
    methods=["POST"]
)
def stage_material():

    data = request.get_json(
        silent=True
    ) or {}

    receipt_nbr = data.get(
        "receipt_nbr"
    )

    receipt_line_id = data.get(
        "receipt_line_id"
    )

    location = data.get(
        "location"
    )

    quantity = data.get(
        "quantity"
    )

    if not receipt_nbr:

        return jsonify({
            "message": "Receipt number is required."
        }), 400

    if not receipt_line_id:

        return jsonify({
            "message": "Receipt line is required."
        }), 400

    if not location:

        return jsonify({
            "message": "Storage location is required."
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
            "message": "Enter a valid staging quantity."
        }), 400

    result = stage_receipt_material(
        receipt_nbr=receipt_nbr,
        receipt_line_id=receipt_line_id,
        quantity=quantity,
        location=location,
        staged_by="Myska Nasiri"
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
# MATERIAL DETAIL BY LINE
# ============================================================

@app.route(
    "/materials/line/<int:receipt_line_id>"
)
def material_line_detail(
    receipt_line_id
):

    material = get_material_detail(
        receipt_line_id=receipt_line_id
    )

    if not material:

        return jsonify({
            "message": "Material line was not found."
        }), 404

    return jsonify({
        "material": material
    })


# ============================================================
# MATERIAL DETAIL BY RECEIPT
# ============================================================

@app.route(
    "/materials/<receipt_nbr>"
)
def material_detail(
    receipt_nbr
):

    material = get_material_detail(
        receipt_nbr=receipt_nbr
    )

    if not material:

        return jsonify({
            "message": (
                "This receipt either was not found or "
                "contains multiple material lines. "
                "Select an individual receipt line instead."
            )
        }), 404

    return jsonify({
        "material": material
    })


# ============================================================
# MOVE MATERIAL
# ============================================================

@app.route(
    "/materials/move",
    methods=["POST"]
)
def move_material_route():

    data = request.get_json(
        silent=True
    ) or {}

    receipt_nbr = data.get(
        "receipt_nbr"
    )

    receipt_line_id = data.get(
        "receipt_line_id"
    )

    from_location = data.get(
        "from_location"
    )

    to_location = data.get(
        "to_location"
    )

    quantity = data.get(
        "quantity"
    )

    notes = data.get(
        "notes",
        ""
    ) or ""

    if not receipt_line_id:

        return jsonify({
            "message": "Receipt line is required."
        }), 400

    if not from_location:

        return jsonify({
            "message": "Current location is required."
        }), 400

    if not to_location:

        return jsonify({
            "message": "Destination location is required."
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
            "message": "Enter a valid movement quantity."
        }), 400

    result = move_material(
        receipt_nbr=receipt_nbr,
        receipt_line_id=receipt_line_id,
        from_location=from_location,
        to_location=to_location,
        quantity=quantity,
        moved_by="Myska Nasiri",
        notes=notes
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

    project = get_project_or_404(
        project_slug
    )

    if not project:

        return (
            "Project not found",
            404
        )

    schedule = PROJECT_SCHEDULES.get(
        project_slug,
        []
    )

    receipts = get_receipts_by_project(
        project_slug
    )

    return render_template(
        "project_dashboard.html",
        project=project,
        project_slug=project_slug,
        schedule=schedule,
        receipts=receipts
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

    project = get_project_or_404(
        project_slug
    )

    if not project:

        return (
            "Project not found",
            404
        )

    purchase_orders = PURCHASE_ORDERS.get(
        project_slug,
        []
    )

    return render_template(
        "project_purchase_orders.html",
        project=project,
        project_slug=project_slug,
        purchase_orders=purchase_orders
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

    project = PROJECTS.get(
        project_slug
    )

    if not project:

        return (
            "Project not found",
            404
        )

    # IMPORTANT:
    # project_schedule.html loops directly over this list.
    schedule = PROJECT_SCHEDULES.get(
        project_slug,
        []
    )

    return render_template(
        "project_schedule.html",
        project=project,
        project_slug=project_slug,
        schedule=schedule
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

    project = get_project_or_404(
        project_slug
    )

    if not project:

        return (
            "Project not found",
            404
        )

    receipts = get_receipts_by_project(
        project_slug
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
        project=project,
        project_slug=project_slug,
        materials=materials
    )


# ============================================================
# REPORTING DASHBOARD
# ============================================================

@app.route(
    "/reporting"
)
def reporting():

    reports = get_all_reports()

    return render_template(
        "reporting.html",
        reports=reports
    )


# ============================================================
# CREATE REPORT
# ============================================================

@app.route(
    "/reporting/create",
    methods=["POST"]
)
def create_reporting_record():

    data = request.get_json(
        silent=True
    ) or {}

    project_slug = data.get(
        "project_slug"
    )

    package_name = data.get(
        "package_name"
    )

    report_type = data.get(
        "report_type"
    )

    if not project_slug:

        return jsonify({
            "message": "Project is required."
        }), 400

    if not package_name:

        return jsonify({
            "message": "Package / section is required."
        }), 400

    if not report_type:

        return jsonify({
            "message": "Report type is required."
        }), 400

    project = PROJECTS.get(
        project_slug
    )

    if not project:

        return jsonify({
            "message": "Project was not found."
        }), 404

    if report_type != "NCR":

        return jsonify({
            "message": (
                "Only the NCR template is connected "
                "in this prototype."
            )
        }), 400

    try:

        result = create_report(
            report_type=report_type,
            project_slug=project_slug,
            project_name=project["short_name"],
            package_name=package_name,
            created_by="Myska Nasiri"
        )

    except Exception as error:

        print(
            "REPORT CREATE ERROR:",
            error
        )

        return jsonify({
            "message": "Unable to create report."
        }), 500

    return jsonify({

        "success": True,

        "report_id":
            result["id"],

        "report_number":
            result["report_number"],

        "redirect_url":
            url_for(
                "ncr_report",
                report_id=result["id"]
            )
    })


# ============================================================
# NCR REPORT
# ============================================================

@app.route(
    "/reporting/ncr/<int:report_id>"
)
def ncr_report(
    report_id
):

    report = get_report(
        report_id
    )

    if not report:

        return (
            "Report not found",
            404
        )

    if report.get(
        "report_type"
    ) != "NCR":

        return (
            "This report is not an NCR.",
            400
        )

    project = PROJECTS.get(
        report.get(
            "project_slug"
        )
    )

    return render_template(
        "ncr_report.html",
        report=report,
        project=project,
        project_slug=report.get(
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

    report = get_report(
        report_id
    )

    if not report:

        return jsonify({
            "message": "Report was not found."
        }), 404

    data = request.get_json(
        silent=True
    ) or {}

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
            "message": "Unable to save draft."
        }), 500

    return jsonify({
        "success": True,
        "message": "Draft saved successfully."
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

    report = get_report(
        report_id
    )

    if not report:

        return jsonify({
            "message": "Report was not found."
        }), 404

    data = request.get_json(
        silent=True
    ) or {}

    if not data.get(
        "date"
    ):

        return jsonify({
            "message": "Report date is required."
        }), 400

    if not data.get(
        "nonconformance_description"
    ):

        return jsonify({
            "message": (
                "Description of the "
                "non-conformance is required."
            )
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
            "message": "Unable to submit report."
        }), 500

    return jsonify({
        "success": True,
        "message": "Report submitted successfully."
    })


# ============================================================
# NCR TEMPLATE IMAGE
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
        mimetype="image/png"
    )


# ============================================================
# GENERATED NCR PDF
# ============================================================

@app.route(
    "/reporting/ncr/<int:report_id>/pdf"
)
def download_ncr_pdf(
    report_id
):

    report = get_report(
        report_id
    )

    if not report:

        return (
            "Report not found.",
            404
        )

    if report.get(
        "report_type"
    ) != "NCR":

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
        mimetype="application/pdf",
        as_attachment=False,
        download_name=(
            report["report_number"]
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