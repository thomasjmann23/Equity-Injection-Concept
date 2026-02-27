#!/usr/bin/env python3
"""Generates example invoice and bank statement PNG documents for the demo."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

W, H = 850, 1100  # Letter-ish portrait

# ── FONTS ─────────────────────────────────────────────────────────────────────
def get_fonts():
    sizes = {"title": 26, "heading": 17, "body": 13, "small": 11}
    candidates = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            try:
                return {k: ImageFont.truetype(path, v) for k, v in sizes.items()}
            except Exception:
                continue
    # Pillow 10+ supports size=
    try:
        return {k: ImageFont.load_default(size=v) for k, v in sizes.items()}
    except TypeError:
        d = ImageFont.load_default()
        return {k: d for k in sizes}

FONTS = get_fonts()

# ── DRAWING HELPERS ───────────────────────────────────────────────────────────
def new_doc():
    img = Image.new("RGB", (W, H), "#FFFFFF")
    return img, ImageDraw.Draw(img)

def draw_header(draw, color, title, subtitle=""):
    draw.rectangle([(0, 0), (W, 88)], fill=color)
    draw.text((30, 14), title,    fill="white",   font=FONTS["title"])
    draw.text((30, 52), subtitle, fill="#cccccc", font=FONTS["small"])

def divider(draw, y, color="#dddddd"):
    draw.line([(30, y), (W - 30, y)], fill=color, width=1)

def labeled(draw, x, y, label, value):
    draw.text((x, y),      label.upper(), fill="#999999", font=FONTS["small"])
    draw.text((x, y + 17), value,         fill="#222222", font=FONTS["body"])

# ══════════════════════════════════════════════════════════════════════════════
# INVOICES
# ══════════════════════════════════════════════════════════════════════════════
INVOICES = [
    {
        "filename": "INV-2025-001_ABC-Industrial-Supply.png",
        "inv_num":  "INV-2025-001",
        "vendor":   "ABC Industrial Supply",
        "addr":     "4400 Commerce Blvd, Chicago, IL 60601",
        "date":     "November 15, 2025",
        "terms":    "Due Upon Receipt",
        "bill_to":  "Moving Company LLC\n123 Business Park, Chicago, IL 60601",
        "items": [
            ("Industrial Conveyor Belt System (x2)", 2,  6000.00, 12000.00),
            ("Hydraulic Lift Platform",              1,  8500.00,  8500.00),
            ("Electric Pallet Jacks (x2)",           2,  2000.00,  4000.00),
        ],
        "total": 24500.00,
        "color": "#154360",
    },
    {
        "filename": "INV-2025-002_Premier-Contractors.png",
        "inv_num":  "INV-2025-002",
        "vendor":   "Premier Contractors LLC",
        "addr":     "8821 Build Ave, Chicago, IL 60602",
        "date":     "November 22, 2025",
        "terms":    "Net 30",
        "bill_to":  "Moving Company LLC\n123 Business Park, Chicago, IL 60601",
        "items": [
            ("Warehouse Floor Renovation (3,200 sq ft)", 1, 32000.00, 32000.00),
            ("Office Buildout (1,200 sq ft)",             1, 18000.00, 18000.00),
            ("Loading Dock Construction (2 bays)",        1, 17000.00, 17000.00),
        ],
        "total": 67000.00,
        "color": "#1e8449",
    },
    {
        "filename": "INV-2025-003_Office-Outfitters.png",
        "inv_num":  "INV-2025-003",
        "vendor":   "Office Outfitters Inc",
        "addr":     "220 Workspace Dr, Chicago, IL 60603",
        "date":     "December 3, 2025",
        "terms":    "Due Upon Receipt",
        "bill_to":  "Moving Company LLC\n123 Business Park, Chicago, IL 60601",
        "items": [
            ("Executive Desk Sets (x5)",    5,  700.00,  3500.00),
            ("Ergonomic Task Chairs (x10)", 10, 225.00,  2250.00),
            ("Filing Cabinets (x8)",         8, 200.00,  1600.00),
            ("Reception Furniture Set",      1, 1400.00,  1400.00),
        ],
        "total": 8750.00,
        "color": "#7d3c98",
    },
    {
        "filename": "INV-2025-005_TechStack-Solutions.png",
        "inv_num":  "INV-2025-005",
        "vendor":   "TechStack Solutions",
        "addr":     "555 Tech Park Way, Chicago, IL 60604",
        "date":     "December 18, 2025",
        "terms":    "Due Upon Receipt",
        "bill_to":  "Moving Company LLC\n123 Business Park, Chicago, IL 60601",
        "items": [
            ("Fleet Management Software (Annual)",   1, 1800.00, 1800.00),
            ("Dispatch & Routing Platform (Annual)", 1,  900.00,  900.00),
            ("Employee Scheduling Suite (Annual)",   1,  500.00,  500.00),
        ],
        "total": 3200.00,
        "color": "#1a5276",
    },
    {
        "filename": "INV-2025-006_SignPro-Design.png",
        "inv_num":  "INV-2025-006",
        "vendor":   "SignPro Design Group",
        "addr":     "900 Marquee Blvd, Chicago, IL 60605",
        "date":     "January 7, 2026",
        "terms":    "Net 15",
        "bill_to":  "Moving Company LLC\n123 Business Park, Chicago, IL 60601",
        "items": [
            ("Exterior Building Sign (illuminated)", 1, 2400.00, 2400.00),
            ("Vehicle Wrap — Box Trucks (x2)",       2,  800.00, 1600.00),
            ("Interior Lobby Signage",               1,  800.00,  800.00),
        ],
        "total": 4800.00,
        "color": "#c0392b",
    },
]

def generate_invoice(inv, out_dir):
    img, draw = new_doc()
    draw_header(draw, inv["color"], inv["vendor"], inv["addr"])
    draw.text((W - 170, 28), "INVOICE", fill="white", font=FONTS["title"])

    labeled(draw,  30, 102, "Invoice #", inv["inv_num"])
    labeled(draw, 215, 102, "Date",      inv["date"])
    labeled(draw, 430, 102, "Terms",     inv["terms"])
    divider(draw, 160)

    draw.text((30, 172), "BILL TO", fill="#999", font=FONTS["small"])
    y = 190
    for line in inv["bill_to"].split("\n"):
        draw.text((30, y), line, fill="#222", font=FONTS["body"])
        y += 18

    # Table header
    draw.rectangle([(30, 242), (W - 30, 268)], fill="#f2f4f6")
    draw.text(( 40, 250), "Description", fill="#555", font=FONTS["small"])
    draw.text((565, 250), "Qty",         fill="#555", font=FONTS["small"])
    draw.text((625, 250), "Unit Price",  fill="#555", font=FONTS["small"])
    draw.text((755, 250), "Amount",      fill="#555", font=FONTS["small"])

    y = 280
    for desc, qty, unit, amount in inv["items"]:
        draw.text(( 40, y), desc,               fill="#222", font=FONTS["body"])
        draw.text((570, y), str(qty),            fill="#222", font=FONTS["body"])
        draw.text((625, y), f"${unit:,.2f}",     fill="#222", font=FONTS["body"])
        draw.text((750, y), f"${amount:,.2f}",   fill="#222", font=FONTS["body"])
        y += 36
        divider(draw, y - 10, "#eeeeee")

    y += 12
    divider(draw, y)
    y += 14
    draw.text((610, y), "Subtotal:", fill="#555", font=FONTS["body"])
    draw.text((740, y), f"${inv['total']:,.2f}", fill="#222", font=FONTS["body"])
    y += 26
    draw.text((610, y), "Tax (0%):", fill="#555", font=FONTS["body"])
    draw.text((740, y), "$0.00",     fill="#222", font=FONTS["body"])
    y += 14
    divider(draw, y + 6)
    y += 18
    draw.rectangle([(595, y), (W - 30, y + 44)], fill=inv["color"])
    draw.text((606, y + 12), "TOTAL DUE", fill="white", font=FONTS["heading"])
    draw.text((730, y + 12), f"${inv['total']:,.2f}", fill="white", font=FONTS["heading"])

    divider(draw, H - 70)
    draw.text((30, H - 55), "Thank you for your business!", fill="#888", font=FONTS["small"])
    draw.text((30, H - 38), f"Questions? Contact {inv['vendor']}  |  {inv['addr']}", fill="#aaa", font=FONTS["small"])
    draw.text((30, H - 20), "SAMPLE DOCUMENT — FOR DEMONSTRATION PURPOSES ONLY", fill="#ccc", font=FONTS["small"])

    img.save(out_dir / inv["filename"])
    print(f"  ✓ invoices/{inv['filename']}")

# ══════════════════════════════════════════════════════════════════════════════
# BANK STATEMENTS
# ══════════════════════════════════════════════════════════════════════════════
ACCOUNTS = [
    {
        "id":         "account_4821",
        "bank":       "First National Bank",
        "short":      "First-National-Bank",
        "acct_name":  "Moving Company LLC — Business Checking",
        "acct_num":   "****4821",
        "routing":    "071000013",
        "color":      "#154360",
        "months": [
            ("2025-07","July 2025",     "07/01/25","07/31/25",  48200.00,[
                ("07/02","Opening deposit — owner equity",          50000.00),
                ("07/08","Office supplies — Staples",                -320.00),
                ("07/15","Payroll — bimonthly",                    -12000.00),
                ("07/22","Fuel expense",                              -850.00),
                ("07/28","Client payment — Riverside Corp",         12500.00),
            ]),
            ("2025-08","August 2025",   "08/01/25","08/31/25",  47530.00,[
                ("08/05","Truck maintenance — Chicago Fleet Svc",   -1200.00),
                ("08/10","Insurance premium — Allied Insurance",    -2400.00),
                ("08/15","Payroll — bimonthly",                    -12000.00),
                ("08/20","Client payment — Lakeview Properties",    18000.00),
                ("08/28","Utilities",                                -560.00),
            ]),
            ("2025-09","September 2025","09/01/25","09/30/25",  49370.00,[
                ("09/03","Marketing — Google Ads",                    -900.00),
                ("09/12","Payroll — bimonthly",                    -12000.00),
                ("09/18","Client payment — Northside Realty",       22000.00),
                ("09/24","Fuel expense",                              -740.00),
                ("09/29","Office lease deposit",                    -5000.00),
            ]),
            ("2025-10","October 2025",  "10/01/25","10/31/25",  52730.00,[
                ("10/05","Client payment — Downtown Storage",       15000.00),
                ("10/10","Payroll — bimonthly",                    -12000.00),
                ("10/16","Truck maintenance",                         -850.00),
                ("10/22","Insurance renewal",                       -2400.00),
                ("10/30","Fuel expense",                              -920.00),
            ]),
            # Nov: 51560 + 19000 + 75000 - 12000 - 24500 - 67000 - 640 = 41420
            ("2025-11","November 2025", "11/01/25","11/30/25",  51560.00,[
                ("11/04","Client payment — Westwood LLC",           19000.00),
                ("11/10","Transfer from savings ****3309",          75000.00),
                ("11/12","Payroll — bimonthly",                    -12000.00),
                ("11/15","ABC Industrial Supply — INV-2025-001",   -24500.00),
                ("11/22","Premier Contractors LLC — INV-2025-002", -67000.00),
                ("11/28","Utilities",                                -640.00),
            ]),
            # Dec: 41420 - 12000 + 28000 - 3200 - 780 = 53440
            ("2025-12","December 2025", "12/01/25","12/31/25",  41420.00,[
                ("12/10","Payroll — bimonthly",                    -12000.00),
                ("12/15","Client payment — Harbor Industrial",      28000.00),
                ("12/18","TechStack Solutions — INV-2025-005",      -3200.00),
                ("12/28","Fuel expense",                              -780.00),
            ]),
        ],
    },
    {
        "id":         "account_3309",
        "bank":       "Chase Business Banking",
        "short":      "Chase-Business-Banking",
        "acct_name":  "Moving Company LLC — Business Savings",
        "acct_num":   "****3309",
        "routing":    "021000021",
        "color":      "#1a3a5c",
        "months": [
            ("2025-08","August 2025",   "08/01/25","08/31/25",  80000.00,[
                ("08/01","Initial equity deposit",                  80000.00),
                ("08/15","Interest earned",                             65.00),
                ("08/30","Transfer to checking ****4821",           -5000.00),
            ]),
            ("2025-09","September 2025","09/01/25","09/30/25",  75065.00,[
                ("09/15","Interest earned",                             61.00),
                ("09/20","Transfer to checking ****4821",          -10000.00),
            ]),
            ("2025-10","October 2025",  "10/01/25","10/31/25",  65126.00,[
                ("10/05","Equity injection — additional deposit",  100000.00),
                ("10/15","Interest earned",                            135.00),
                ("10/25","Transfer to checking ****4821",          -20000.00),
            ]),
            # Nov: 145261 + 118 - 75000 - 5000 = 65379
            ("2025-11","November 2025", "11/01/25","11/30/25", 145261.00,[
                ("11/10","Transfer to checking ****4821",          -75000.00),
                ("11/15","Interest earned",                            118.00),
                ("11/28","Transfer to checking ****4821",           -5000.00),
            ]),
            # Dec: 65379 - 8750 - 15000 + 102 - 10000 = 31731
            ("2025-12","December 2025", "12/01/25","12/31/25",  65379.00,[
                ("12/03","Office Outfitters Inc — INV-2025-003",    -8750.00),
                ("12/10","Payroll Services Co — Working Capital",   -15000.00),
                ("12/15","Interest earned",                            102.00),
                ("12/20","Transfer to checking ****4821",          -10000.00),
            ]),
            # Jan: 31731 - 4800 + 94 - 8000 = 19025
            ("2026-01","January 2026",  "01/01/26","01/31/26",  31731.00,[
                ("01/07","SignPro Design Group — INV-2025-006",     -4800.00),
                ("01/15","Interest earned",                             94.00),
                ("01/28","Transfer to checking ****4821",           -8000.00),
            ]),
        ],
    },
    {
        # Line of credit: balance shown as available credit remaining (always >= 0)
        # Draws reduce available credit; payments restore it.
        "id":         "account_7756",
        "bank":       "Wells Fargo Business",
        "short":      "Wells-Fargo-Business",
        "acct_name":  "Moving Company LLC — Business Line of Credit",
        "acct_num":   "****7756",
        "routing":    "121042882",
        "color":      "#7b0d1e",
        "months": [
            # Sep: 50000 (full available credit, no activity)
            ("2025-09","September 2025","09/01/25","09/30/25",  50000.00,[
                ("09/01","Credit line established — $50,000 limit",    0.00),
                ("09/15","No transactions this period",                0.00),
            ]),
            ("2025-10","October 2025",  "10/01/25","10/31/25",  50000.00,[
                ("10/10","No activity this period",                    0.00),
            ]),
            # Nov: 50000 - 15000 + 500 = 35500
            ("2025-11","November 2025", "11/01/25","11/30/25",  50000.00,[
                ("11/18","Draw — equipment purchase working capital", -15000.00),
                ("11/30","Payment received",                             500.00),
            ]),
            # Dec: 35500 - 8000 + 750 - 183 = 28067
            ("2025-12","December 2025", "12/01/25","12/31/25",  35500.00,[
                ("12/10","Draw — working capital",                   -8000.00),
                ("12/31","Payment received",                            750.00),
                ("12/31","Interest charge",                            -183.00),
            ]),
            # Jan: 28067 + 5000 - 176 = 32891
            ("2026-01","January 2026",  "01/01/26","01/31/26",  28067.00,[
                ("01/15","Payment received",                           5000.00),
                ("01/31","Interest charge",                            -176.00),
            ]),
            # Feb: 32891 - 3000 + 750 - 162 = 30479
            ("2026-02","February 2026", "02/01/26","02/28/26",  32891.00,[
                ("02/10","Draw — operational expenses",              -3000.00),
                ("02/28","Payment received",                            750.00),
                ("02/28","Interest charge",                            -162.00),
            ]),
        ],
    },
]

def generate_statement(acct, month_data, out_dir):
    month_id, month_label, start_dt, end_dt, opening, txns = month_data
    img, draw = new_doc()

    draw_header(draw, acct["color"], acct["bank"], acct["acct_name"])

    labeled(draw,  30, 102, "Account Number", acct["acct_num"])
    labeled(draw, 230, 102, "Routing",        acct["routing"])
    labeled(draw, 430, 102, "Period",         f"{start_dt} – {end_dt}")
    divider(draw, 160)

    total_credits = sum(a for _, _, a in txns if a > 0)
    total_debits  = sum(a for _, _, a in txns if a < 0)
    closing       = opening + total_credits + total_debits
    net           = total_credits + total_debits

    bw = (W - 90) // 3
    for i, (lbl, val, col) in enumerate([
        ("Opening Balance", f"${opening:,.2f}", "#333"),
        ("Net Activity",    (f"+${net:,.2f}" if net >= 0 else f"-${abs(net):,.2f}"),
                            "#196f3d" if net >= 0 else "#922b21"),
        ("Closing Balance", f"${closing:,.2f}", acct["color"]),
    ]):
        bx = 30 + i * (bw + 15)
        draw.rectangle([(bx, 174), (bx + bw, 220)], fill="#f8f9fa", outline="#dee2e6")
        draw.text((bx + 10, 182), lbl, fill="#888", font=FONTS["small"])
        draw.text((bx + 10, 200), val, fill=col,   font=FONTS["heading"])

    draw.rectangle([(30, 234), (W - 30, 258)], fill="#f2f4f6")
    draw.text(( 40, 242), "Date",        fill="#555", font=FONTS["small"])
    draw.text((110, 242), "Description", fill="#555", font=FONTS["small"])
    draw.text((648, 242), "Amount",      fill="#555", font=FONTS["small"])
    draw.text((758, 242), "Balance",     fill="#555", font=FONTS["small"])

    y = 270
    running = opening
    for dt, desc, amount in txns:
        if y > H - 130:
            break
        running += amount
        col    = "#196f3d" if amount >= 0 else "#922b21"
        amt_s  = f"+${amount:,.2f}" if amount >= 0 else f"-${abs(amount):,.2f}"
        draw.text(( 40, y), dt,               fill="#333", font=FONTS["body"])
        draw.text((110, y), desc[:54],        fill="#333", font=FONTS["body"])
        draw.text((643, y), amt_s,            fill=col,    font=FONTS["body"])
        draw.text((753, y), f"${running:,.2f}", fill="#333", font=FONTS["body"])
        y += 32
        divider(draw, y - 9, "#eeeeee")

    divider(draw, H - 70)
    draw.text((30, H - 55), f"Statement Period: {month_label}", fill="#888", font=FONTS["small"])
    draw.text((30, H - 38), f"{acct['bank']}  |  {acct['acct_num']}  |  Routing: {acct['routing']}", fill="#aaa", font=FONTS["small"])
    draw.text((30, H - 20), "SAMPLE DOCUMENT — FOR DEMONSTRATION PURPOSES ONLY", fill="#ccc", font=FONTS["small"])

    fname = f"{month_id}_{acct['short']}.png"
    img.save(out_dir / fname)
    print(f"  ✓ {acct['id']}/{fname}")

# ── MAIN ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    base = Path(__file__).parent

    inv_dir = base / "invoices"
    inv_dir.mkdir(exist_ok=True)
    print(f"\nGenerating invoices → {inv_dir}/")
    for inv in INVOICES:
        generate_invoice(inv, inv_dir)

    stmt_base = base / "statements"
    stmt_base.mkdir(exist_ok=True)
    print(f"\nGenerating bank statements → {stmt_base}/")
    for acct in ACCOUNTS:
        acct_dir = stmt_base / acct["id"]
        acct_dir.mkdir(exist_ok=True)
        for month_data in acct["months"]:
            generate_statement(acct, month_data, acct_dir)

    print("\n✅ Done! All example documents generated.")
