from io import BytesIO
from datetime import datetime, date

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
# Demo/faux PO data used to populate the prototype Material Management
# workspace. Receipt quantities, backorder quantities, and expected dates
# below are mock operational data for demonstration only.

PURCHASE_ORDERS = {
    "williams-aquila": [
        {"po_number":"PO-00004621","vendor":"Graybar","part_number":"1492-J4","description":"Terminal Block","uom":"EA","ordered_qty":50,"received_qty":50,"delivery_date":"09/10/2026","backordered_qty":0,"expected_date":None,"package_name":"PLC Panels"},
        {"po_number":"PO-00004621","vendor":"Graybar","part_number":"1492-EBJ3","description":"End Barrier","uom":"EA","ordered_qty":25,"received_qty":25,"delivery_date":"09/10/2026","backordered_qty":0,"expected_date":None,"package_name":"PLC Panels"},
        {"po_number":"PO-00004621","vendor":"Graybar","part_number":"1492-CJLJ6-4","description":"Center Jumper","uom":"EA","ordered_qty":30,"received_qty":30,"delivery_date":"09/10/2026","backordered_qty":0,"expected_date":None,"package_name":"PLC Panels"},
        {"po_number":"PO-00004621","vendor":"Graybar","part_number":"1492-SPM1C020","description":"Miniature Circuit Breaker","uom":"EA","ordered_qty":20,"received_qty":20,"delivery_date":"09/10/2026","backordered_qty":0,"expected_date":None,"package_name":"PLC Panels"},
        {"po_number":"PO-00004621","vendor":"Graybar","part_number":"199-DR1","description":"DIN Rail","uom":"EA","ordered_qty":12,"received_qty":12,"delivery_date":"09/10/2026","backordered_qty":0,"expected_date":None,"package_name":"PLC Panels"},
        {"po_number":"PO-00004621","vendor":"Graybar","part_number":"A1X4LG6","description":"Wiring Duct","uom":"EA","ordered_qty":10,"received_qty":10,"delivery_date":"09/10/2026","backordered_qty":0,"expected_date":None,"package_name":"PLC Panels"},

        {"po_number":"PO-00004718","vendor":"Lonestar Electric","part_number":"1783-ETAP","description":"EtherNet/IP Tap","uom":"EA","ordered_qty":12,"received_qty":6,"delivery_date":"09/16/2026","backordered_qty":0,"expected_date":None,"package_name":"PLC Panels"},
        {"po_number":"PO-00004718","vendor":"Lonestar Electric","part_number":"1585J-M8TBJM-2","description":"Industrial Ethernet Patch Cord","uom":"EA","ordered_qty":20,"received_qty":20,"delivery_date":"09/16/2026","backordered_qty":0,"expected_date":None,"package_name":"PLC Panels"},
        {"po_number":"PO-00004718","vendor":"Lonestar Electric","part_number":"1783-US05T","description":"Stratix Unmanaged Ethernet Switch","uom":"EA","ordered_qty":4,"received_qty":4,"delivery_date":"09/16/2026","backordered_qty":0,"expected_date":None,"package_name":"PLC Panels"},
        {"po_number":"PO-00004718","vendor":"Lonestar Electric","part_number":"1585D-M4TBJM-5","description":"Industrial Ethernet Cable","uom":"EA","ordered_qty":16,"received_qty":8,"delivery_date":"09/16/2026","backordered_qty":0,"expected_date":None,"package_name":"PLC Panels"},
        {"po_number":"PO-00004718","vendor":"Lonestar Electric","part_number":"1783-SFP1GLX","description":"Fiber SFP Transceiver","uom":"EA","ordered_qty":8,"received_qty":4,"delivery_date":"09/16/2026","backordered_qty":0,"expected_date":None,"package_name":"PLC Panels"},
        {"po_number":"PO-00004718","vendor":"Lonestar Electric","part_number":"AP-LC6-LDSM-G","description":"LC 6-Position Adapter Plate","uom":"EA","ordered_qty":2,"received_qty":2,"delivery_date":"09/16/2026","backordered_qty":0,"expected_date":None,"package_name":"PLC Panels"},

        {"po_number":"PO-00004781","vendor":"The Reynolds Company","part_number":"5094-RTB32V","description":"5094 RTB 32 Input Screw","uom":"EA","ordered_qty":8,"received_qty":2,"delivery_date":"09/18/2026","backordered_qty":0,"expected_date":None,"package_name":"PLC Panels"},
        {"po_number":"PO-00004781","vendor":"The Reynolds Company","part_number":"5094-IB32","description":"FLEX 5000 32-Point Digital Input Module","uom":"EA","ordered_qty":8,"received_qty":8,"delivery_date":"09/18/2026","backordered_qty":0,"expected_date":None,"package_name":"PLC Panels"},
        {"po_number":"PO-00004781","vendor":"The Reynolds Company","part_number":"5094-OB16","description":"FLEX 5000 16-Point Digital Output Module","uom":"EA","ordered_qty":4,"received_qty":4,"delivery_date":"09/18/2026","backordered_qty":0,"expected_date":None,"package_name":"PLC Panels"},
        {"po_number":"PO-00004781","vendor":"The Reynolds Company","part_number":"5094-IF8IH","description":"FLEX 5000 Isolated Analog Input Module","uom":"EA","ordered_qty":6,"received_qty":3,"delivery_date":"09/18/2026","backordered_qty":0,"expected_date":None,"package_name":"PLC Panels"},
        {"po_number":"PO-00004781","vendor":"The Reynolds Company","part_number":"5094-OF8IH","description":"FLEX 5000 Isolated Analog Output Module","uom":"EA","ordered_qty":2,"received_qty":0,"delivery_date":"09/18/2026","backordered_qty":0,"expected_date":None,"package_name":"PLC Panels"},
        {"po_number":"PO-00004781","vendor":"The Reynolds Company","part_number":"5094-AEN2TR","description":"FLEX 5000 EtherNet/IP Adapter","uom":"EA","ordered_qty":4,"received_qty":4,"delivery_date":"09/18/2026","backordered_qty":0,"expected_date":None,"package_name":"PLC Panels"},
        {"po_number":"PO-00004781","vendor":"The Reynolds Company","part_number":"5094-MB","description":"FLEX 5000 Mounting Base","uom":"EA","ordered_qty":26,"received_qty":18,"delivery_date":"09/18/2026","backordered_qty":0,"expected_date":None,"package_name":"PLC Panels"},
        {"po_number":"PO-00004781","vendor":"The Reynolds Company","part_number":"5094-RTB3W","description":"FLEX 5000 Removable Terminal Block","uom":"EA","ordered_qty":6,"received_qty":0,"delivery_date":"09/18/2026","backordered_qty":6,"expected_date":"10/15/2026","package_name":"PLC Panels"},

        {"po_number":"PO-00004822","vendor":"Summit Electric Supply","part_number":"1756-EN2TR","description":"ControlLogix EtherNet/IP Module","uom":"EA","ordered_qty":4,"received_qty":0,"delivery_date":"10/08/2026","backordered_qty":0,"expected_date":None,"package_name":"BESS"},
        {"po_number":"PO-00004822","vendor":"Summit Electric Supply","part_number":"1756-PA75","description":"ControlLogix Power Supply","uom":"EA","ordered_qty":2,"received_qty":0,"delivery_date":"10/08/2026","backordered_qty":0,"expected_date":None,"package_name":"BESS"},
        {"po_number":"PO-00004822","vendor":"Summit Electric Supply","part_number":"1756-A10","description":"ControlLogix 10-Slot Chassis","uom":"EA","ordered_qty":2,"received_qty":0,"delivery_date":"10/08/2026","backordered_qty":0,"expected_date":None,"package_name":"BESS"},
        {"po_number":"PO-00004822","vendor":"Summit Electric Supply","part_number":"1756-L83E","description":"ControlLogix 5580 Controller","uom":"EA","ordered_qty":2,"received_qty":0,"delivery_date":"10/08/2026","backordered_qty":0,"expected_date":None,"package_name":"BESS"},
        {"po_number":"PO-00004822","vendor":"Summit Electric Supply","part_number":"1606-XLE120E","description":"24 VDC Power Supply","uom":"EA","ordered_qty":4,"received_qty":0,"delivery_date":"10/08/2026","backordered_qty":0,"expected_date":None,"package_name":"BESS"},

        {"po_number":"PO-00004840","vendor":"Saginaw Control & Engineering","part_number":"SCE-72EL6018LP","description":"Electrical Enclosure","uom":"EA","ordered_qty":3,"received_qty":1,"delivery_date":"10/12/2026","backordered_qty":0,"expected_date":None,"package_name":"FNE"},
        {"po_number":"PO-00004840","vendor":"Saginaw Control & Engineering","part_number":"SCE-72P60","description":"Enclosure Subpanel","uom":"EA","ordered_qty":3,"received_qty":1,"delivery_date":"10/12/2026","backordered_qty":0,"expected_date":None,"package_name":"FNE"},
        {"po_number":"PO-00004840","vendor":"Saginaw Control & Engineering","part_number":"SCE-ELJMFK","description":"Enclosure Joining Kit","uom":"EA","ordered_qty":6,"received_qty":2,"delivery_date":"10/12/2026","backordered_qty":0,"expected_date":None,"package_name":"FNE"},
        {"po_number":"PO-00004840","vendor":"Saginaw Control & Engineering","part_number":"SCE-LFLK","description":"Floor Stand Leg Kit","uom":"EA","ordered_qty":6,"received_qty":2,"delivery_date":"10/12/2026","backordered_qty":0,"expected_date":None,"package_name":"FNE"},

        {"po_number":"PO-00004855","vendor":"Graybar","part_number":"1492-W4","description":"Feed-Through Terminal Block","uom":"EA","ordered_qty":100,"received_qty":100,"delivery_date":"09/24/2026","backordered_qty":0,"expected_date":None,"package_name":"Server"},
        {"po_number":"PO-00004855","vendor":"Graybar","part_number":"1492-EBJ3","description":"End Barrier","uom":"EA","ordered_qty":40,"received_qty":40,"delivery_date":"09/24/2026","backordered_qty":0,"expected_date":None,"package_name":"Server"},
        {"po_number":"PO-00004855","vendor":"Graybar","part_number":"1492-CJLJ6-4","description":"Center Jumper","uom":"EA","ordered_qty":25,"received_qty":25,"delivery_date":"09/24/2026","backordered_qty":0,"expected_date":None,"package_name":"Server"},
        {"po_number":"PO-00004855","vendor":"Graybar","part_number":"1492-SPM1C020","description":"Miniature Circuit Breaker","uom":"EA","ordered_qty":20,"received_qty":20,"delivery_date":"09/24/2026","backordered_qty":0,"expected_date":None,"package_name":"Server"},
        {"po_number":"PO-00004855","vendor":"Graybar","part_number":"199-DR1","description":"DIN Rail","uom":"EA","ordered_qty":12,"received_qty":12,"delivery_date":"09/24/2026","backordered_qty":0,"expected_date":None,"package_name":"Server"},
        {"po_number":"PO-00004855","vendor":"Graybar","part_number":"A1X4LG6","description":"Wiring Duct","uom":"EA","ordered_qty":10,"received_qty":10,"delivery_date":"09/24/2026","backordered_qty":0,"expected_date":None,"package_name":"Server"},
    ],

    "targa-butane": [
        {"po_number":"PO-00004648","vendor":"Summit Electric Supply","part_number":"A1008CHNF","description":"NEMA Enclosure","uom":"EA","ordered_qty":4,"received_qty":4,"delivery_date":"08/28/2026","backordered_qty":0,"expected_date":None,"package_name":"COMMS Cabinets"},
        {"po_number":"PO-00004648","vendor":"Summit Electric Supply","part_number":"A10P8","description":"Enclosure Panel","uom":"EA","ordered_qty":4,"received_qty":4,"delivery_date":"08/28/2026","backordered_qty":0,"expected_date":None,"package_name":"COMMS Cabinets"},
        {"po_number":"PO-00004648","vendor":"Summit Electric Supply","part_number":"A10R86","description":"Enclosure Rain Hood","uom":"EA","ordered_qty":4,"received_qty":4,"delivery_date":"08/28/2026","backordered_qty":0,"expected_date":None,"package_name":"COMMS Cabinets"},
        {"po_number":"PO-00004744","vendor":"Saginaw Control & Engineering","part_number":"SCE-84XM2418","description":"Floor-Mount Enclosure","uom":"EA","ordered_qty":2,"received_qty":0,"delivery_date":"09/22/2026","backordered_qty":2,"expected_date":"10/14/2026","package_name":"MSTG-COMM-1"},
        {"po_number":"PO-00004744","vendor":"Saginaw Control & Engineering","part_number":"SCE-84P24","description":"Enclosure Subpanel","uom":"EA","ordered_qty":2,"received_qty":0,"delivery_date":"09/22/2026","backordered_qty":2,"expected_date":"10/14/2026","package_name":"MSTG-COMM-1"},
        {"po_number":"PO-00004744","vendor":"Saginaw Control & Engineering","part_number":"SCE-FS84","description":"Floor Stand Kit","uom":"EA","ordered_qty":2,"received_qty":0,"delivery_date":"09/22/2026","backordered_qty":2,"expected_date":"10/14/2026","package_name":"MSTG-COMM-1"},
        {"po_number":"PO-00004752","vendor":"Graybar","part_number":"800T-FX6A5","description":"Emergency Stop Push Button","uom":"EA","ordered_qty":8,"received_qty":8,"delivery_date":"09/11/2026","backordered_qty":0,"expected_date":None,"package_name":"Controls"},
        {"po_number":"PO-00004752","vendor":"Graybar","part_number":"800T-XA","description":"Contact Block","uom":"EA","ordered_qty":16,"received_qty":16,"delivery_date":"09/11/2026","backordered_qty":0,"expected_date":None,"package_name":"Controls"},
        {"po_number":"PO-00004752","vendor":"Graybar","part_number":"800T-N26","description":"Legend Plate","uom":"EA","ordered_qty":8,"received_qty":8,"delivery_date":"09/11/2026","backordered_qty":0,"expected_date":None,"package_name":"Controls"},
        {"po_number":"PO-00004811","vendor":"WESCO","part_number":"700-HLT1Z24","description":"General Purpose Relay","uom":"EA","ordered_qty":48,"received_qty":20,"delivery_date":"10/09/2026","backordered_qty":0,"expected_date":None,"package_name":"Controls"},
        {"po_number":"PO-00004811","vendor":"WESCO","part_number":"700-HN126","description":"Relay Socket","uom":"EA","ordered_qty":48,"received_qty":20,"delivery_date":"10/09/2026","backordered_qty":0,"expected_date":None,"package_name":"Controls"},
        {"po_number":"PO-00004811","vendor":"WESCO","part_number":"1492-J4","description":"Terminal Block","uom":"EA","ordered_qty":80,"received_qty":40,"delivery_date":"10/09/2026","backordered_qty":0,"expected_date":None,"package_name":"Controls"},
    ],

    "bp-kaskida": [
        {"po_number":"PO-00004673","vendor":"The Reynolds Company","part_number":"5094-IB16","description":"Digital Input Module","uom":"EA","ordered_qty":16,"received_qty":10,"delivery_date":"10/06/2026","backordered_qty":0,"expected_date":None,"package_name":"I/O"},
        {"po_number":"PO-00004673","vendor":"The Reynolds Company","part_number":"5094-OB16","description":"Digital Output Module","uom":"EA","ordered_qty":12,"received_qty":6,"delivery_date":"10/06/2026","backordered_qty":0,"expected_date":None,"package_name":"I/O"},
        {"po_number":"PO-00004673","vendor":"The Reynolds Company","part_number":"5094-MB","description":"Mounting Base","uom":"EA","ordered_qty":28,"received_qty":16,"delivery_date":"10/06/2026","backordered_qty":0,"expected_date":None,"package_name":"I/O"},
        {"po_number":"PO-00004673","vendor":"The Reynolds Company","part_number":"5094-AEN2TR","description":"EtherNet/IP Adapter","uom":"EA","ordered_qty":4,"received_qty":2,"delivery_date":"10/06/2026","backordered_qty":0,"expected_date":None,"package_name":"I/O"},
        {"po_number":"PO-00004690","vendor":"Graybar","part_number":"1492-SPM1C020","description":"Miniature Circuit Breaker","uom":"EA","ordered_qty":30,"received_qty":30,"delivery_date":"08/20/2026","backordered_qty":0,"expected_date":None,"package_name":"Panel Hardware"},
        {"po_number":"PO-00004690","vendor":"Graybar","part_number":"1492-J4","description":"Terminal Block","uom":"EA","ordered_qty":120,"received_qty":120,"delivery_date":"08/20/2026","backordered_qty":0,"expected_date":None,"package_name":"Panel Hardware"},
        {"po_number":"PO-00004690","vendor":"Graybar","part_number":"1492-EBJ3","description":"End Barrier","uom":"EA","ordered_qty":40,"received_qty":40,"delivery_date":"08/20/2026","backordered_qty":0,"expected_date":None,"package_name":"Panel Hardware"},
        {"po_number":"PO-00004795","vendor":"WESCO","part_number":"1756-PA75","description":"ControlLogix Power Supply","uom":"EA","ordered_qty":6,"received_qty":0,"delivery_date":"09/20/2026","backordered_qty":0,"expected_date":None,"package_name":"ControlLogix"},
        {"po_number":"PO-00004795","vendor":"WESCO","part_number":"1756-L83E","description":"ControlLogix Controller","uom":"EA","ordered_qty":2,"received_qty":0,"delivery_date":"09/20/2026","backordered_qty":0,"expected_date":None,"package_name":"ControlLogix"},
        {"po_number":"PO-00004795","vendor":"WESCO","part_number":"1756-EN2TR","description":"EtherNet/IP Module","uom":"EA","ordered_qty":4,"received_qty":0,"delivery_date":"09/20/2026","backordered_qty":0,"expected_date":None,"package_name":"ControlLogix"},
        {"po_number":"PO-00004804","vendor":"WESCO","part_number":"1756-A10","description":"ControlLogix 10-Slot Chassis","uom":"EA","ordered_qty":3,"received_qty":0,"delivery_date":"10/15/2026","backordered_qty":0,"expected_date":None,"package_name":"ControlLogix"},
        {"po_number":"PO-00004804","vendor":"WESCO","part_number":"1756-A7","description":"ControlLogix 7-Slot Chassis","uom":"EA","ordered_qty":2,"received_qty":0,"delivery_date":"10/15/2026","backordered_qty":0,"expected_date":None,"package_name":"ControlLogix"},
        {"po_number":"PO-00004804","vendor":"WESCO","part_number":"1756-TBCH","description":"Removable Terminal Block","uom":"EA","ordered_qty":10,"received_qty":0,"delivery_date":"10/15/2026","backordered_qty":0,"expected_date":None,"package_name":"ControlLogix"},
    ],

    "slb-hpu-skids": [
        {"po_number":"PO-00004684","vendor":"Graybar","part_number":"1492-JD3","description":"Disconnect Terminal Block","uom":"EA","ordered_qty":36,"received_qty":36,"delivery_date":"08/25/2026","backordered_qty":0,"expected_date":None,"package_name":"HPU Skids"},
        {"po_number":"PO-00004684","vendor":"Graybar","part_number":"1492-J4","description":"Terminal Block","uom":"EA","ordered_qty":90,"received_qty":90,"delivery_date":"08/25/2026","backordered_qty":0,"expected_date":None,"package_name":"HPU Skids"},
        {"po_number":"PO-00004684","vendor":"Graybar","part_number":"1492-EBJ3","description":"End Barrier","uom":"EA","ordered_qty":30,"received_qty":30,"delivery_date":"08/25/2026","backordered_qty":0,"expected_date":None,"package_name":"HPU Skids"},
        {"po_number":"PO-00004702","vendor":"WESCO","part_number":"1734-AENTR","description":"POINT I/O Ethernet Adapter","uom":"EA","ordered_qty":10,"received_qty":0,"delivery_date":"10/05/2026","backordered_qty":0,"expected_date":None,"package_name":"Remote I/O"},
        {"po_number":"PO-00004702","vendor":"WESCO","part_number":"1734-TB","description":"POINT I/O Terminal Base","uom":"EA","ordered_qty":40,"received_qty":0,"delivery_date":"10/05/2026","backordered_qty":0,"expected_date":None,"package_name":"Remote I/O"},
        {"po_number":"PO-00004702","vendor":"WESCO","part_number":"1734-EP24DC","description":"POINT I/O Expansion Power Supply","uom":"EA","ordered_qty":6,"received_qty":0,"delivery_date":"10/05/2026","backordered_qty":0,"expected_date":None,"package_name":"Remote I/O"},
        {"po_number":"PO-00004767","vendor":"The Reynolds Company","part_number":"1734-IB8","description":"POINT I/O Digital Input Module","uom":"EA","ordered_qty":24,"received_qty":12,"delivery_date":"09/14/2026","backordered_qty":0,"expected_date":None,"package_name":"Remote I/O"},
        {"po_number":"PO-00004767","vendor":"The Reynolds Company","part_number":"1734-OB8","description":"POINT I/O Digital Output Module","uom":"EA","ordered_qty":16,"received_qty":8,"delivery_date":"09/14/2026","backordered_qty":0,"expected_date":None,"package_name":"Remote I/O"},
        {"po_number":"PO-00004767","vendor":"The Reynolds Company","part_number":"1734-IE4C","description":"POINT I/O Analog Input Module","uom":"EA","ordered_qty":8,"received_qty":4,"delivery_date":"09/14/2026","backordered_qty":0,"expected_date":None,"package_name":"Remote I/O"},
        {"po_number":"PO-00004832","vendor":"Summit Electric Supply","part_number":"HBL460P9W","description":"Industrial Plug","uom":"EA","ordered_qty":6,"received_qty":6,"delivery_date":"09/28/2026","backordered_qty":0,"expected_date":None,"package_name":"Power Distribution"},
        {"po_number":"PO-00004832","vendor":"Summit Electric Supply","part_number":"HBL460R9W","description":"Industrial Receptacle","uom":"EA","ordered_qty":6,"received_qty":6,"delivery_date":"09/28/2026","backordered_qty":0,"expected_date":None,"package_name":"Power Distribution"},
        {"po_number":"PO-00004832","vendor":"Summit Electric Supply","part_number":"HBL60CM33","description":"Watertight Connector","uom":"EA","ordered_qty":12,"received_qty":12,"delivery_date":"09/28/2026","backordered_qty":0,"expected_date":None,"package_name":"Power Distribution"},
    ],

    "venture-global": [
        {"po_number":"PO-00004657","vendor":"The Reynolds Company","part_number":"1756-L83E","description":"ControlLogix Controller","uom":"EA","ordered_qty":2,"received_qty":2,"delivery_date":"08/18/2026","backordered_qty":0,"expected_date":None,"package_name":"PLC"},
        {"po_number":"PO-00004657","vendor":"The Reynolds Company","part_number":"1756-EN2TR","description":"EtherNet/IP Module","uom":"EA","ordered_qty":4,"received_qty":4,"delivery_date":"08/18/2026","backordered_qty":0,"expected_date":None,"package_name":"PLC"},
        {"po_number":"PO-00004657","vendor":"The Reynolds Company","part_number":"1756-PA75","description":"ControlLogix Power Supply","uom":"EA","ordered_qty":2,"received_qty":2,"delivery_date":"08/18/2026","backordered_qty":0,"expected_date":None,"package_name":"PLC"},
        {"po_number":"PO-00004731","vendor":"Graybar","part_number":"1756-IF8","description":"Analog Input Module","uom":"EA","ordered_qty":8,"received_qty":8,"delivery_date":"09/04/2026","backordered_qty":0,"expected_date":None,"package_name":"I/O"},
        {"po_number":"PO-00004731","vendor":"Graybar","part_number":"1756-TBCH","description":"Removable Terminal Block","uom":"EA","ordered_qty":16,"received_qty":16,"delivery_date":"09/04/2026","backordered_qty":0,"expected_date":None,"package_name":"I/O"},
        {"po_number":"PO-00004731","vendor":"Graybar","part_number":"1492-J4","description":"Terminal Block","uom":"EA","ordered_qty":100,"received_qty":100,"delivery_date":"09/04/2026","backordered_qty":0,"expected_date":None,"package_name":"I/O"},
        {"po_number":"PO-00004772","vendor":"WESCO","part_number":"1756-OF8","description":"Analog Output Module","uom":"EA","ordered_qty":8,"received_qty":4,"delivery_date":"10/02/2026","backordered_qty":0,"expected_date":None,"package_name":"I/O"},
        {"po_number":"PO-00004772","vendor":"WESCO","part_number":"1756-IB16","description":"Digital Input Module","uom":"EA","ordered_qty":12,"received_qty":6,"delivery_date":"10/02/2026","backordered_qty":0,"expected_date":None,"package_name":"I/O"},
        {"po_number":"PO-00004772","vendor":"WESCO","part_number":"1756-OB16E","description":"Digital Output Module","uom":"EA","ordered_qty":12,"received_qty":6,"delivery_date":"10/02/2026","backordered_qty":0,"expected_date":None,"package_name":"I/O"},
        {"po_number":"PO-00004816","vendor":"Saginaw Control & Engineering","part_number":"SCE-60EL4818LP","description":"Electrical Enclosure","uom":"EA","ordered_qty":2,"received_qty":0,"delivery_date":"10/20/2026","backordered_qty":1,"expected_date":"11/03/2026","package_name":"Enclosures"},
        {"po_number":"PO-00004816","vendor":"Saginaw Control & Engineering","part_number":"SCE-60P48","description":"Enclosure Subpanel","uom":"EA","ordered_qty":2,"received_qty":0,"delivery_date":"10/20/2026","backordered_qty":1,"expected_date":"11/03/2026","package_name":"Enclosures"},
        {"po_number":"PO-00004816","vendor":"Saginaw Control & Engineering","part_number":"SCE-FS60","description":"Floor Stand Kit","uom":"EA","ordered_qty":2,"received_qty":0,"delivery_date":"10/20/2026","backordered_qty":0,"expected_date":None,"package_name":"Enclosures"},
    ],

    "drone-in-the-box": [
        {"po_number":"PO-00004666","vendor":"Summit Electric Supply","part_number":"A48H3612SS6LP","description":"Stainless Steel Enclosure","uom":"EA","ordered_qty":1,"received_qty":1,"delivery_date":"08/31/2026","backordered_qty":0,"expected_date":None,"package_name":"Drone Cabinet"},
        {"po_number":"PO-00004666","vendor":"Summit Electric Supply","part_number":"A48P36","description":"Enclosure Panel","uom":"EA","ordered_qty":1,"received_qty":1,"delivery_date":"08/31/2026","backordered_qty":0,"expected_date":None,"package_name":"Drone Cabinet"},
        {"po_number":"PO-00004666","vendor":"Summit Electric Supply","part_number":"A48R36","description":"Rain Hood","uom":"EA","ordered_qty":1,"received_qty":1,"delivery_date":"08/31/2026","backordered_qty":0,"expected_date":None,"package_name":"Drone Cabinet"},
        {"po_number":"PO-00004763","vendor":"Summit Electric Supply","part_number":"HBLDS3","description":"Disconnect Switch","uom":"EA","ordered_qty":4,"received_qty":4,"delivery_date":"09/12/2026","backordered_qty":0,"expected_date":None,"package_name":"Power"},
        {"po_number":"PO-00004763","vendor":"Summit Electric Supply","part_number":"HBL460P9W","description":"Industrial Plug","uom":"EA","ordered_qty":4,"received_qty":4,"delivery_date":"09/12/2026","backordered_qty":0,"expected_date":None,"package_name":"Power"},
        {"po_number":"PO-00004763","vendor":"Summit Electric Supply","part_number":"HBL460R9W","description":"Industrial Receptacle","uom":"EA","ordered_qty":4,"received_qty":4,"delivery_date":"09/12/2026","backordered_qty":0,"expected_date":None,"package_name":"Power"},
        {"po_number":"PO-00004788","vendor":"Graybar","part_number":"1585D-M4TBJM-5","description":"Industrial Ethernet Cable","uom":"EA","ordered_qty":12,"received_qty":5,"delivery_date":"09/19/2026","backordered_qty":0,"expected_date":None,"package_name":"Networking"},
        {"po_number":"PO-00004788","vendor":"Graybar","part_number":"1783-US05T","description":"Unmanaged Ethernet Switch","uom":"EA","ordered_qty":2,"received_qty":1,"delivery_date":"09/19/2026","backordered_qty":0,"expected_date":None,"package_name":"Networking"},
        {"po_number":"PO-00004788","vendor":"Graybar","part_number":"1585J-M8TBJM-2","description":"Ethernet Patch Cord","uom":"EA","ordered_qty":10,"received_qty":5,"delivery_date":"09/19/2026","backordered_qty":0,"expected_date":None,"package_name":"Networking"},
        {"po_number":"PO-00004828","vendor":"WESCO","part_number":"1606-XLE120E","description":"24 VDC Power Supply","uom":"EA","ordered_qty":3,"received_qty":0,"delivery_date":"10/16/2026","backordered_qty":0,"expected_date":None,"package_name":"Controls"},
        {"po_number":"PO-00004828","vendor":"WESCO","part_number":"1769-L33ER","description":"CompactLogix Controller","uom":"EA","ordered_qty":1,"received_qty":0,"delivery_date":"10/16/2026","backordered_qty":0,"expected_date":None,"package_name":"Controls"},
        {"po_number":"PO-00004828","vendor":"WESCO","part_number":"1769-IF4","description":"Analog Input Module","uom":"EA","ordered_qty":2,"received_qty":0,"delivery_date":"10/16/2026","backordered_qty":0,"expected_date":None,"package_name":"Controls"},
    ],
}


# ============================================================
# DELIVERY TICKETS / RECEIVING VERIFICATION (DEMO DATA)
# ============================================================
# Faux prototype records used only to make the mock receiving workflow realistic.
# Acumatica is still treated as the proposed source for PO / line-item data.

DELIVERY_TICKETS = {
    "williams-aquila": [
        {"ticket_number":"DT-1041","date":"09/10/2026","po_number":"PO-00004621","vendor":"Graybar","received_by":"Tech Center Receiving","lines":[{"part_number":"1492-J4","qty":50},{"part_number":"1492-EBJ3","qty":25},{"part_number":"1492-CJLJ6-4","qty":30},{"part_number":"1492-SPM1C020","qty":20},{"part_number":"199-DR1","qty":12},{"part_number":"A1X4LG6","qty":10}]},
        {"ticket_number":"DT-1046","date":"09/16/2026","po_number":"PO-00004718","vendor":"Lonestar Electric","received_by":"Tech Center Receiving","lines":[{"part_number":"1783-ETAP","qty":6},{"part_number":"1585J-M8TBJM-2","qty":20},{"part_number":"1783-US05T","qty":4},{"part_number":"1585D-M4TBJM-5","qty":8},{"part_number":"1783-SFP1GLX","qty":4},{"part_number":"AP-LC6-LDSM-G","qty":2}]},
        {"ticket_number":"DT-1050","date":"09/18/2026","po_number":"PO-00004781","vendor":"The Reynolds Company","received_by":"Tech Center Receiving","lines":[{"part_number":"5094-RTB32V","qty":2},{"part_number":"5094-IB32","qty":8},{"part_number":"5094-OB16","qty":4},{"part_number":"5094-IF8IH","qty":3},{"part_number":"5094-AEN2TR","qty":4},{"part_number":"5094-MB","qty":18}]},
        {"ticket_number":"DT-1057","date":"09/24/2026","po_number":"PO-00004855","vendor":"Graybar","received_by":"Tech Center Receiving","lines":[{"part_number":"1492-W4","qty":100},{"part_number":"1492-EBJ3","qty":40},{"part_number":"1492-CJLJ6-4","qty":25},{"part_number":"1492-SPM1C020","qty":20},{"part_number":"199-DR1","qty":12},{"part_number":"A1X4LG6","qty":10}]},
        {"ticket_number":"DT-1062","date":"09/29/2026","po_number":"PO-00004840","vendor":"Saginaw Control & Engineering","received_by":"Tech Center Receiving","lines":[{"part_number":"SCE-72EL6018LP","qty":1},{"part_number":"SCE-72P60","qty":1},{"part_number":"SCE-ELJMFK","qty":2},{"part_number":"SCE-LFLK","qty":2}]},
    ],
    "targa-butane": [
        {"ticket_number":"DT-1018","date":"08/28/2026","po_number":"PO-00004648","vendor":"Summit Electric Supply","received_by":"Tech Center Receiving","lines":[{"part_number":"A1008CHNF","qty":4},{"part_number":"A10P8","qty":4},{"part_number":"A10R86","qty":4}]},
        {"ticket_number":"DT-1034","date":"09/11/2026","po_number":"PO-00004752","vendor":"Graybar","received_by":"Tech Center Receiving","lines":[{"part_number":"800T-FX6A5","qty":8},{"part_number":"800T-XA","qty":16},{"part_number":"800T-N26","qty":8}]},
        {"ticket_number":"DT-1060","date":"09/29/2026","po_number":"PO-00004811","vendor":"WESCO","received_by":"Tech Center Receiving","lines":[{"part_number":"700-HLT1Z24","qty":20},{"part_number":"700-HN126","qty":20},{"part_number":"1492-J4","qty":40}]},
    ],
    "bp-kaskida": [
        {"ticket_number":"DT-1007","date":"08/20/2026","po_number":"PO-00004690","vendor":"Graybar","received_by":"Tech Center Receiving","lines":[{"part_number":"1492-SPM1C020","qty":30},{"part_number":"1492-J4","qty":120},{"part_number":"1492-EBJ3","qty":40}]},
        {"ticket_number":"DT-1064","date":"09/30/2026","po_number":"PO-00004673","vendor":"The Reynolds Company","received_by":"Tech Center Receiving","lines":[{"part_number":"5094-IB16","qty":10},{"part_number":"5094-OB16","qty":6},{"part_number":"5094-MB","qty":16},{"part_number":"5094-AEN2TR","qty":2}]},
    ],
    "slb-hpu-skids": [
        {"ticket_number":"DT-1012","date":"08/25/2026","po_number":"PO-00004684","vendor":"Graybar","received_by":"Tech Center Receiving","lines":[{"part_number":"1492-JD3","qty":36},{"part_number":"1492-J4","qty":90},{"part_number":"1492-EBJ3","qty":30}]},
        {"ticket_number":"DT-1044","date":"09/14/2026","po_number":"PO-00004767","vendor":"The Reynolds Company","received_by":"Tech Center Receiving","lines":[{"part_number":"1734-IB8","qty":12},{"part_number":"1734-OB8","qty":8},{"part_number":"1734-IE4C","qty":4}]},
        {"ticket_number":"DT-1059","date":"09/28/2026","po_number":"PO-00004832","vendor":"Summit Electric Supply","received_by":"Tech Center Receiving","lines":[{"part_number":"HBL460P9W","qty":6},{"part_number":"HBL460R9W","qty":6},{"part_number":"HBL60CM33","qty":12}]},
    ],
    "venture-global": [
        {"ticket_number":"DT-1003","date":"08/18/2026","po_number":"PO-00004657","vendor":"The Reynolds Company","received_by":"Tech Center Receiving","lines":[{"part_number":"1756-L83E","qty":2},{"part_number":"1756-EN2TR","qty":4},{"part_number":"1756-PA75","qty":2}]},
        {"ticket_number":"DT-1025","date":"09/04/2026","po_number":"PO-00004731","vendor":"Graybar","received_by":"Tech Center Receiving","lines":[{"part_number":"1756-IF8","qty":8},{"part_number":"1756-TBCH","qty":16},{"part_number":"1492-J4","qty":100}]},
        {"ticket_number":"DT-1063","date":"09/30/2026","po_number":"PO-00004772","vendor":"WESCO","received_by":"Tech Center Receiving","lines":[{"part_number":"1756-OF8","qty":4},{"part_number":"1756-IB16","qty":6},{"part_number":"1756-OB16E","qty":6}]},
    ],
    "drone-in-the-box": [
        {"ticket_number":"DT-1020","date":"08/31/2026","po_number":"PO-00004666","vendor":"Summit Electric Supply","received_by":"Tech Center Receiving","lines":[{"part_number":"A48H3612SS6LP","qty":1},{"part_number":"A48P36","qty":1},{"part_number":"A48R36","qty":1}]},
        {"ticket_number":"DT-1037","date":"09/12/2026","po_number":"PO-00004763","vendor":"Summit Electric Supply","received_by":"Tech Center Receiving","lines":[{"part_number":"HBLDS3","qty":4},{"part_number":"HBL460P9W","qty":4},{"part_number":"HBL460R9W","qty":4}]},
        {"ticket_number":"DT-1051","date":"09/19/2026","po_number":"PO-00004788","vendor":"Graybar","received_by":"Tech Center Receiving","lines":[{"part_number":"1585D-M4TBJM-5","qty":5},{"part_number":"1783-US05T","qty":1},{"part_number":"1585J-M8TBJM-2","qty":5}]},
    ],
}


def parse_material_date(value):
    if not value:
        return None
    for fmt in ("%m/%d/%Y", "%m/%d/%y", "%Y-%m-%d"):
        try:
            return datetime.strptime(str(value), fmt).date()
        except ValueError:
            continue
    return None


def get_material_line_status(line, today=None):
    today = today or date.today()
    ordered = int(line.get("ordered_qty", 0) or 0)
    received = int(line.get("received_qty", 0) or 0)
    outstanding = max(ordered - received, 0)
    backordered = int(line.get("backordered_qty", 0) or 0)
    delivery_date = parse_material_date(line.get("delivery_date"))

    if outstanding == 0:
        return "Received"
    if backordered > 0:
        return "Backordered"
    if delivery_date and delivery_date < today:
        return "Overdue"
    if received > 0:
        return "Partially Received"
    return "Awaiting Receipt"


def get_days_overdue(line, today=None):
    today = today or date.today()
    delivery_date = parse_material_date(line.get("delivery_date"))
    if not delivery_date or delivery_date >= today:
        return 0
    ordered = int(line.get("ordered_qty", 0) or 0)
    received = int(line.get("received_qty", 0) or 0)
    if max(ordered - received, 0) <= 0:
        return 0
    return (today - delivery_date).days


def get_delivery_history(project_slug, po_number=None, part_number=None):
    history = []
    for ticket in DELIVERY_TICKETS.get(project_slug, []):
        if po_number and str(ticket.get("po_number")) != str(po_number):
            continue
        for ticket_line in ticket.get("lines", []):
            if part_number and str(ticket_line.get("part_number")) != str(part_number):
                continue
            history.append({
                "ticket_number": ticket.get("ticket_number"),
                "date": ticket.get("date"),
                "po_number": ticket.get("po_number"),
                "vendor": ticket.get("vendor"),
                "received_by": ticket.get("received_by"),
                "notes": ticket.get("notes", ""),
                "part_number": ticket_line.get("part_number"),
                "qty": int(ticket_line.get("qty", 0) or 0),
            })
    return history


def build_project_po_register(project_slug):
    today = date.today()
    grouped = {}
    for source_line in PURCHASE_ORDERS.get(project_slug, []):
        line = dict(source_line)
        po_number = line.get("po_number")
        if not po_number:
            continue
        ordered = int(line.get("ordered_qty", 0) or 0)
        received = int(line.get("received_qty", 0) or 0)
        outstanding = max(ordered - received, 0)
        line["outstanding_qty"] = outstanding
        line["display_status"] = get_material_line_status(line, today)
        line["days_overdue"] = get_days_overdue(line, today)
        line["delivery_history"] = get_delivery_history(project_slug, po_number, line.get("part_number"))

        po = grouped.setdefault(po_number, {
            "po_number": po_number,
            "vendor": line.get("vendor", "—"),
            "package_name": line.get("package_name") or "—",
            "delivery_date": line.get("delivery_date"),
            "lines": [],
            "line_count": 0,
            "total_ordered": 0,
            "total_received": 0,
            "total_outstanding": 0,
            "backordered_items": 0,
            "overdue_items": 0,
        })
        po["lines"].append(line)
        po["line_count"] += 1
        po["total_ordered"] += ordered
        po["total_received"] += received
        po["total_outstanding"] += outstanding
        if int(line.get("backordered_qty", 0) or 0) > 0:
            po["backordered_items"] += 1
        if line["display_status"] == "Overdue":
            po["overdue_items"] += 1

    result = []
    for po in grouped.values():
        if po["total_outstanding"] == 0:
            po["status"] = "Received"
        elif po["backordered_items"] > 0:
            po["status"] = "Backordered"
        elif po["overdue_items"] > 0:
            po["status"] = "Overdue"
        elif po["total_received"] > 0:
            po["status"] = "Partially Received"
        else:
            po["status"] = "Awaiting Receipt"
        po["tickets"] = sorted({h["ticket_number"] for line in po["lines"] for h in line["delivery_history"]})
        result.append(po)
    return sorted(result, key=lambda po: str(po["po_number"]), reverse=True)


def build_project_material_control_room(project_slug):
    today = date.today()
    materials = []
    metrics = {"total_items": 0, "received": 0, "pending": 0, "delivery_tickets": len(DELIVERY_TICKETS.get(project_slug, []))}
    status_counts = {"Received": 0, "Partially Received": 0, "Awaiting Receipt": 0, "Overdue": 0, "Backordered": 0}

    for source_line in PURCHASE_ORDERS.get(project_slug, []):
        line = dict(source_line)
        ordered = int(line.get("ordered_qty", 0) or 0)
        received = int(line.get("received_qty", 0) or 0)
        outstanding = max(ordered - received, 0)
        status = get_material_line_status(line, today)
        history = get_delivery_history(project_slug, line.get("po_number"), line.get("part_number"))
        line.update({
            "outstanding_qty": outstanding,
            "display_status": status,
            "days_overdue": get_days_overdue(line, today),
            "delivery_history": history,
            "delivery_tickets": [item["ticket_number"] for item in history],
        })
        metrics["total_items"] += ordered
        metrics["received"] += received
        metrics["pending"] += outstanding
        status_counts[status] = status_counts.get(status, 0) + 1
        materials.append(line)

    materials.sort(key=lambda item: (item["display_status"] == "Received", str(item.get("po_number", "")), str(item.get("part_number", ""))))
    return materials, metrics, status_counts


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
    all_pos = []
    overdue_lines = []
    today = date.today()

    metrics = {
        "items_received": 0,
        "items_overdue": 0,
        "active_pos": 0,
        "items_pending": 0,
        "open_lines": 0,
        "total_pos": 0,
    }

    status_counts = {
        "Overdue": 0,
        "Backordered": 0,
        "Partially Received": 0,
        "Awaiting Receipt": 0,
        "Received": 0,
    }

    for project_slug, po_lines in PURCHASE_ORDERS.items():
        project = PROJECTS.get(project_slug)
        if not project:
            continue

        project_name = project.get("short_name", project.get("name", project_slug))
        grouped_pos = {}

        for source_line in po_lines:
            line = dict(source_line)
            po_number = line.get("po_number")
            if not po_number:
                continue

            ordered = int(line.get("ordered_qty", 0) or 0)
            received = int(line.get("received_qty", 0) or 0)
            outstanding = max(ordered - received, 0)
            backordered = int(line.get("backordered_qty", 0) or 0)
            line_status = get_material_line_status(line, today)

            line["outstanding_qty"] = outstanding
            line["remaining_qty"] = outstanding
            line["display_status"] = line_status
            line["days_overdue"] = get_days_overdue(line, today)
            line["project_slug"] = project_slug
            line["project_name"] = project_name

            metrics["items_received"] += received
            metrics["items_pending"] += outstanding
            if outstanding > 0:
                metrics["open_lines"] += 1

            if line_status == "Overdue":
                metrics["items_overdue"] += outstanding
                overdue_lines.append(line)

            if po_number not in grouped_pos:
                grouped_pos[po_number] = {
                    "po_number": po_number,
                    "project_slug": project_slug,
                    "project_name": project_name,
                    "vendor": line.get("vendor", "—"),
                    "package_name": line.get("package_name"),
                    "lines": [],
                    "total_ordered": 0,
                    "total_received": 0,
                    "total_outstanding": 0,
                    "backordered_items": 0,
                    "overdue_items": 0,
                }

            po = grouped_pos[po_number]
            po["lines"].append(line)
            po["total_ordered"] += ordered
            po["total_received"] += received
            po["total_outstanding"] += outstanding
            if backordered > 0:
                po["backordered_items"] += 1
            if line_status == "Overdue":
                po["overdue_items"] += 1

        for po in grouped_pos.values():
            if po["total_outstanding"] == 0:
                po_status = "Received"
            elif po["backordered_items"] > 0:
                po_status = "Backordered"
            elif po["overdue_items"] > 0:
                po_status = "Overdue"
            elif po["total_received"] > 0:
                po_status = "Partially Received"
            else:
                po_status = "Awaiting Receipt"

            po["status"] = po_status
            status_counts[po_status] += 1

            if po["total_outstanding"] > 0:
                metrics["active_pos"] += 1

            searchable_parts = [
                po["po_number"], po["project_name"], po["vendor"],
                po.get("package_name") or "",
            ]
            for line in po["lines"]:
                searchable_parts.extend([
                    line.get("part_number", ""),
                    line.get("description", ""),
                ])
            po["search_text"] = " ".join(str(value) for value in searchable_parts if value)
            all_pos.append(po)

    metrics["total_pos"] = len(all_pos)
    all_pos.sort(key=lambda po: str(po["po_number"]), reverse=True)
    overdue_lines.sort(key=lambda line: (-line["days_overdue"], str(line["po_number"])))

    return render_template(
        "materials_management.html",
        all_pos=all_pos,
        active_pos=all_pos,
        overdue_lines=overdue_lines,
        metrics=metrics,
        status_counts=status_counts,
    )



# ============================================================
# DELIVERY TICKET HISTORY
# ============================================================

@app.route("/materials/delivery-tickets")
def delivery_ticket_history():
    delivery_tickets = []

    for project_slug, tickets in DELIVERY_TICKETS.items():
        project = PROJECTS.get(project_slug)
        if not project:
            continue

        project_name = project.get("short_name", project.get("name", project_slug))

        for source_ticket in tickets:
            ticket = dict(source_ticket)
            ticket["project_slug"] = project_slug
            ticket["project_name"] = project_name
            ticket["total_received"] = sum(
                int(line.get("qty", 0) or 0)
                for line in ticket.get("lines", [])
            )

            search_values = [
                ticket.get("ticket_number", ""),
                ticket.get("date", ""),
                ticket.get("po_number", ""),
                ticket.get("vendor", ""),
                ticket.get("received_by", ""),
                project_name,
            ]
            search_values.extend(
                line.get("part_number", "")
                for line in ticket.get("lines", [])
            )
            ticket["search_text"] = " ".join(
                str(value) for value in search_values if value
            )
            delivery_tickets.append(ticket)

    delivery_tickets.sort(
        key=lambda ticket: (
            parse_material_date(ticket.get("date")) or date.min,
            str(ticket.get("ticket_number", ""))
        ),
        reverse=True,
    )

    return render_template(
        "delivery_ticket_history.html",
        delivery_tickets=delivery_tickets,
    )


# ============================================================
# MATERIAL MANAGEMENT - PO DETAIL
# ============================================================

@app.route("/materials/purchase-orders/<project_slug>/<po_number>")
def materials_purchase_order_detail(project_slug, po_number):
    project = PROJECTS.get(project_slug)
    if not project:
        return ("Project not found", 404)

    project_po_lines = PURCHASE_ORDERS.get(project_slug, [])
    po_lines = [
        line for line in project_po_lines
        if str(line.get("po_number")) == str(po_number)
    ]
    if not po_lines:
        return ("Purchase order not found", 404)

    today = date.today()
    vendor = po_lines[0].get("vendor", "—")
    package_name = po_lines[0].get("package_name")
    order_date = po_lines[0].get("order_date") or po_lines[0].get("po_date")

    total_ordered = sum(int(line.get("ordered_qty", 0) or 0) for line in po_lines)
    total_received = sum(int(line.get("received_qty", 0) or 0) for line in po_lines)
    total_outstanding = max(total_ordered - total_received, 0)

    backordered_lines = []
    overdue_lines = []
    other_lines = []

    for line in po_lines:
        display_line = dict(line)
        ordered = int(line.get("ordered_qty", 0) or 0)
        received = int(line.get("received_qty", 0) or 0)
        outstanding = max(ordered - received, 0)
        backordered_qty = int(line.get("backordered_qty", 0) or 0)
        display_status = get_material_line_status(line, today)

        display_line["outstanding_qty"] = outstanding
        display_line["remaining_qty"] = outstanding
        display_line["backordered_qty"] = backordered_qty
        display_line["display_status"] = display_status
        display_line["days_overdue"] = get_days_overdue(line, today)

        if display_status == "Backordered":
            backordered_lines.append(display_line)
        elif display_status == "Overdue":
            overdue_lines.append(display_line)
        else:
            other_lines.append(display_line)

    if total_outstanding == 0:
        po_status = "Received"
    elif backordered_lines:
        po_status = "Backordered"
    elif overdue_lines:
        po_status = "Overdue"
    elif total_received > 0:
        po_status = "Partially Received"
    else:
        po_status = "Awaiting Receipt"

    return render_template(
        "materials_purchase_order_detail.html",
        project=project,
        project_slug=project_slug,
        po_number=po_number,
        vendor=vendor,
        package_name=package_name,
        order_date=order_date,
        po_status=po_status,
        total_ordered=total_ordered,
        total_received=total_received,
        total_outstanding=total_outstanding,
        backordered_lines=backordered_lines,
        overdue_lines=overdue_lines,
        other_lines=other_lines,
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

@app.route("/projects/<project_slug>/purchase-orders")
def project_purchase_orders(project_slug):
    project = get_project_or_404(project_slug)
    if not project:
        return ("Project not found", 404)

    purchase_orders = build_project_po_register(project_slug)
    po_metrics = {
        "total_pos": len(purchase_orders),
        "open_pos": sum(1 for po in purchase_orders if po["total_outstanding"] > 0),
        "received_pos": sum(1 for po in purchase_orders if po["status"] == "Received"),
        "outstanding_items": sum(po["total_outstanding"] for po in purchase_orders),
    }
    return render_template(
        "project_purchase_orders.html",
        project=project,
        project_slug=project_slug,
        purchase_orders=purchase_orders,
        po_metrics=po_metrics,
        today_iso=date.today().isoformat(),
    )


@app.route(
    "/projects/<project_slug>/purchase-orders/<po_number>/receive",
    methods=["POST"]
)
def record_project_po_delivery(project_slug, po_number):
    project = get_project_or_404(project_slug)
    if not project:
        return ("Project not found", 404)

    project_lines = PURCHASE_ORDERS.get(project_slug, [])
    po_lines = [
        line for line in project_lines
        if str(line.get("po_number")) == str(po_number)
    ]

    if not po_lines:
        return ("Purchase order not found", 404)

    ticket_number = request.form.get("ticket_number", "").strip()
    delivery_date = request.form.get("delivery_date", "").strip()
    received_by = request.form.get("received_by", "").strip()
    notes = request.form.get("notes", "").strip()

    if not ticket_number or not delivery_date or not received_by:
        return redirect(
            url_for(
                "project_purchase_orders",
                project_slug=project_slug,
                receive_error="Ticket number, delivery date, and received by are required.",
                open_po=po_number,
            )
        )

    try:
        datetime.strptime(delivery_date, "%Y-%m-%d")
    except ValueError:
        return redirect(
            url_for(
                "project_purchase_orders",
                project_slug=project_slug,
                receive_error="Enter a valid delivery date.",
                open_po=po_number,
            )
        )

    existing_ticket = any(
        str(ticket.get("ticket_number", "")).lower() == ticket_number.lower()
        for tickets in DELIVERY_TICKETS.values()
        for ticket in tickets
    )
    if existing_ticket:
        return redirect(
            url_for(
                "project_purchase_orders",
                project_slug=project_slug,
                receive_error=f"Delivery ticket {ticket_number} already exists.",
                open_po=po_number,
            )
        )

    received_lines = []

    for index, line in enumerate(po_lines):
        raw_qty = request.form.get(f"qty_{index}", "0").strip() or "0"

        try:
            qty_now = int(raw_qty)
        except ValueError:
            return redirect(
                url_for(
                    "project_purchase_orders",
                    project_slug=project_slug,
                    receive_error="Received quantities must be whole numbers.",
                    open_po=po_number,
                )
            )

        if qty_now < 0:
            return redirect(
                url_for(
                    "project_purchase_orders",
                    project_slug=project_slug,
                    receive_error="Received quantities cannot be negative.",
                    open_po=po_number,
                )
            )

        ordered = int(line.get("ordered_qty", 0) or 0)
        already_received = int(line.get("received_qty", 0) or 0)
        remaining = max(ordered - already_received, 0)

        if qty_now > remaining:
            return redirect(
                url_for(
                    "project_purchase_orders",
                    project_slug=project_slug,
                    receive_error=(
                        f"{line.get('part_number', 'Line item')} only has "
                        f"{remaining} remaining to receive."
                    ),
                    open_po=po_number,
                )
            )

        if qty_now > 0:
            received_lines.append({
                "part_number": line.get("part_number"),
                "qty": qty_now,
            })

    if not received_lines:
        return redirect(
            url_for(
                "project_purchase_orders",
                project_slug=project_slug,
                receive_error="Enter a received quantity for at least one material line.",
                open_po=po_number,
            )
        )

    # Update the mock PO quantities only after every submitted line validates.
    for received_line in received_lines:
        for line in po_lines:
            if str(line.get("part_number")) == str(received_line["part_number"]):
                line["received_qty"] = (
                    int(line.get("received_qty", 0) or 0)
                    + int(received_line["qty"])
                )
                break

    display_date = datetime.strptime(delivery_date, "%Y-%m-%d").strftime("%m/%d/%Y")

    DELIVERY_TICKETS.setdefault(project_slug, []).append({
        "ticket_number": ticket_number,
        "date": display_date,
        "po_number": po_number,
        "vendor": po_lines[0].get("vendor", "—"),
        "received_by": received_by,
        "notes": notes,
        "lines": received_lines,
    })

    return redirect(
        url_for(
            "project_purchase_orders",
            project_slug=project_slug,
            recorded=ticket_number,
            open_po=po_number,
        )
    )


@app.route("/projects/<project_slug>/purchase-orders/<po_number>")
def project_purchase_order_detail(project_slug, po_number):
    project = get_project_or_404(project_slug)
    if not project:
        return ("Project not found", 404)

    purchase_order = next((po for po in build_project_po_register(project_slug) if str(po["po_number"]) == str(po_number)), None)
    if not purchase_order:
        return ("Purchase order not found", 404)

    return render_template(
        "project_purchase_order_detail.html",
        project=project,
        project_slug=project_slug,
        purchase_order=purchase_order,
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

@app.route("/projects/<project_slug>/materials")
def project_materials(project_slug):
    project = get_project_or_404(project_slug)
    if not project:
        return ("Project not found", 404)

    materials, material_metrics, material_status_counts = build_project_material_control_room(project_slug)
    delivery_tickets = DELIVERY_TICKETS.get(project_slug, [])

    return render_template(
        "project_materials.html",
        project=project,
        project_slug=project_slug,
        materials=materials,
        material_metrics=material_metrics,
        material_status_counts=material_status_counts,
        delivery_tickets=delivery_tickets,
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