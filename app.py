import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import date, datetime
import base64, io

st.set_page_config(page_title="Closing Equity Injection", layout="wide")

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Loan info - plain text, no card */
    .loan-label {
        font-size: 0.72rem;
        color: #6c757d;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 3px;
    }
    .loan-value {
        font-size: 1.1rem;
        font-weight: 700;
        color: #212529;
    }
    /* Ledger */
    .ledger-header {
        font-size: 0.75rem;
        font-weight: 700;
        color: #6c757d;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        padding: 6px 0;
        border-bottom: 2px solid #dee2e6;
    }
    .ledger-row {
        padding: 7px 0;
        border-bottom: 1px solid #f0f0f0;
        font-size: 0.88rem;
    }
    .sourced-yes { color: #198754; font-weight: 600; }
    .sourced-no  { color: #dc3545; font-weight: 600; }
    .total-row {
        font-weight: 700;
        font-size: 0.92rem;
        padding: 8px 0;
        border-top: 2px solid #dee2e6;
    }
    /* Document cards */
    .doc-card {
        width: 100%;
        height: 230px;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        background: #f8f9fa;
        overflow: hidden;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: flex-start;
        padding: 8px 6px 6px 6px;
        box-sizing: border-box;
    }
    .doc-card-empty {
        width: 100%;
        height: 230px;
        border: 2px dashed #dee2e6;
        border-radius: 8px;
        background: #ffffff;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        color: #adb5bd;
        font-size: 0.8rem;
        text-align: center;
        box-sizing: border-box;
    }
    .doc-card-add {
        width: 100%;
        height: 230px;
        border: 2px dashed #0d6efd;
        border-radius: 8px;
        background: #f0f6ff;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        color: #0d6efd;
        font-size: 0.92rem;
        font-weight: 600;
        text-align: center;
        box-sizing: border-box;
    }
    /* File type badge (replaces emoji) */
    .file-ext-badge {
        width: 42px;
        height: 54px;
        border: 2px solid #ced4da;
        border-radius: 3px;
        background: #f0f0f0;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.6rem;
        color: #6c757d;
        font-weight: 700;
        margin-bottom: 6px;
        letter-spacing: 0.03em;
    }
    /* Request card */
    .req-card {
        border-left: 4px solid #ffc107;
        border-top: 1px solid #dee2e6;
        border-right: 1px solid #dee2e6;
        border-bottom: 1px solid #dee2e6;
        border-radius: 0 8px 8px 0;
        padding: 10px 14px;
        background: #fffdf0;
        margin-bottom: 8px;
    }
    /* Add Statement upload zone - styled to look like the add card */
    div[data-testid="stExpander"] [data-testid="stFileUploaderDropzone"] {
        min-height: 160px;
        border: 2px dashed #0d6efd !important;
        border-radius: 8px !important;
        background: #f0f6ff !important;
    }
    div[data-testid="stExpander"] [data-testid="stFileUploaderDropzoneInstructions"] span,
    div[data-testid="stExpander"] [data-testid="stFileUploaderDropzoneInstructions"] small {
        color: #0d6efd !important;
        font-weight: 600 !important;
    }
    /* Green expander for sourced items - targets expander containing the marker */
    div[data-testid="stExpander"]:has(.sourced-item-marker) details {
        background-color: #f0fff4 !important;
        border-color: #198754 !important;
    }
    div[data-testid="stExpander"]:has(.sourced-item-marker) summary p,
    div[data-testid="stExpander"]:has(.sourced-item-marker) summary span {
        color: #198754 !important;
        font-weight: 600 !important;
    }
    /* Yellow expander for items with outstanding document requests */
    div[data-testid="stExpander"]:has(.request-outstanding-marker) details {
        background-color: #fffdf0 !important;
        border-color: #ffc107 !important;
    }
    div[data-testid="stExpander"]:has(.request-outstanding-marker) summary p,
    div[data-testid="stExpander"]:has(.request-outstanding-marker) summary span {
        color: #856404 !important;
        font-weight: 600 !important;
    }
</style>
""", unsafe_allow_html=True)

# ── CONSTANTS ─────────────────────────────────────────────────────────────────
LOAN_NAME       = "Moving Company LLC"
LOAN_AMOUNT     = 1_000_000.00
EQUITY_REQUIRED = 100_000.00

STATUS_OPTIONS = ["Pending", "Approved", "Rejected"]
MAX_DOC_COLS   = 5
UOP_ITEMS      = ["Working Capital", "Leasehold Improvements", "FF&E", "M&E", "Closing Costs"]

# ── FILE HELPERS ──────────────────────────────────────────────────────────────
def parse_month(fname: str) -> str:
    stem  = fname.rsplit(".", 1)[0]
    parts = stem.split("_", 1)
    try:
        return datetime.strptime(parts[0], "%Y-%m").strftime("%b %Y")
    except ValueError:
        return parts[0]

def bank_name_from_file(fname: str) -> str:
    stem  = fname.rsplit(".", 1)[0]
    parts = stem.split("_", 1)
    return parts[1].replace("-", " ") if len(parts) > 1 else fname

def acct_num_from_folder(folder: str) -> str:
    parts = folder.split("_")
    return f"****{parts[-1]}" if len(parts) >= 2 else folder

def make_thumbnail(data: bytes, max_w: int = 150, max_h: int = 165):
    try:
        from PIL import Image
        img = Image.open(io.BytesIO(data))
        img.thumbnail((max_w, max_h), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode()
        return f"data:image/png;base64,{b64}"
    except Exception:
        return None

def get_thumbnail(fname: str, data: bytes):
    if fname not in st.session_state.thumbnails:
        st.session_state.thumbnails[fname] = make_thumbnail(data)
    return st.session_state.thumbnails[fname]

def find_file(file_list: list, name: str):
    for f in file_list:
        if f["name"] == name:
            return f
    return None

def file_ext_badge(fname: str) -> str:
    ext = fname.rsplit(".", 1)[-1].upper() if "." in fname else "FILE"
    return f'<div class="file-ext-badge">{ext}</div>'

def doc_card_html(fname: str, data=None, card_class: str = "doc-card") -> str:
    if data:
        thumb = get_thumbnail(fname, data)
        inner = (
            f'<img src="{thumb}" style="max-width:100%;max-height:158px;'
            f'object-fit:contain;border-radius:3px;margin-bottom:4px">'
            if thumb else file_ext_badge(fname)
        )
    else:
        inner = file_ext_badge(fname)
    short = fname if len(fname) <= 32 else fname[:29] + "..."
    return (
        f'<div class="{card_class}">'
        f'  {inner}'
        f'  <div style="font-size:0.68rem;color:#495057;word-break:break-all;'
        f'              text-align:center;line-height:1.3;padding:0 2px">{short}</div>'
        f'</div>'
    )

def col_label(text: str) -> str:
    return (
        f"<div style='font-size:0.78rem;font-weight:700;color:#6c757d;"
        f"text-transform:uppercase;letter-spacing:.04em;margin-bottom:4px'>"
        f"{text}</div>"
    )

# ── PDF PACKAGE EXPORT ────────────────────────────────────────────────────────
def _load_pkg_fonts():
    from PIL import ImageFont
    candidates = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    def _try(size):
        for fp in candidates:
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                continue
        try:
            return ImageFont.load_default(size=size)
        except Exception:
            return ImageFont.load_default()
    return {
        "title": _try(30),
        "lg":    _try(24),
        "md":    _try(19),
        "sm":    _try(15),
        "xs":    _try(12),
    }

def apply_watermark(img, text: str = "DRAFT - FOR REVIEW ONLY") -> "Image":
    from PIL import Image, ImageDraw, ImageFont
    import math

    F = _load_pkg_fonts()
    PAGE_W, PAGE_H = img.size

    # Create transparent RGBA overlay the same size as the page
    overlay = Image.new("RGBA", (PAGE_W, PAGE_H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)

    # Render watermark text onto a temporary wide canvas, then rotate
    wm_font = F["title"]
    try:
        bbox = od.textbbox((0, 0), text, font=wm_font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
    except Exception:
        tw, th = 700, 40

    # Build a temp canvas sized to the text, draw text, rotate 45°
    tmp = Image.new("RGBA", (tw + 40, th + 20), (0, 0, 0, 0))
    td  = ImageDraw.Draw(tmp)
    td.text((20, 10), text, font=wm_font, fill=(180, 0, 0, 90))
    rotated = tmp.rotate(45, expand=True)

    # Tile the rotated stamp across the page with spacing
    rw, rh = rotated.size
    x_step = int(rw * 1.1)
    y_step = int(rh * 1.1)
    x_start = -rw
    y_start = -rh
    x = x_start
    while x < PAGE_W + rw:
        y = y_start
        while y < PAGE_H + rh:
            overlay.paste(rotated, (x, y), rotated)
            y += y_step
        x += x_step

    # Composite overlay onto a copy of the original page
    base = img.convert("RGBA")
    combined = Image.alpha_composite(base, overlay)
    return combined.convert("RGB")


def build_package_pdf(watermark: bool = False) -> bytes:
    from PIL import Image, ImageDraw
    import io as _io

    PAGE_W, PAGE_H = 1200, 1650
    MARGIN  = 60
    BANNER_H = 130          # slightly taller to fit closer notes line
    BG           = (255, 255, 255)
    BANNER_BG    = (13, 110, 253)
    BANNER_FG    = (255, 255, 255)
    NOTES_FG     = (180, 210, 255)   # lighter blue for closer notes in banner
    TEXT_C       = (33, 37, 41)
    MUTED_C      = (108, 117, 125)
    GREEN_C      = (25, 135, 84)
    RED_C        = (220, 53, 69)
    DIVIDER_C    = (222, 226, 230)

    F = _load_pkg_fonts()
    pages = []

    # ── PAGE 1: LEDGER ────────────────────────────────────────────────────────
    img  = Image.new("RGB", (PAGE_W, PAGE_H), BG)
    draw = ImageDraw.Draw(img)
    y = MARGIN

    draw.text((MARGIN, y), "Closing Equity Injection", font=F["title"], fill=TEXT_C)
    y += 42
    draw.text(
        (MARGIN, y),
        f"Loan: {LOAN_NAME}   |   Loan Amount: ${LOAN_AMOUNT:,.0f}"
        f"   |   Equity Required: ${EQUITY_REQUIRED:,.0f}",
        font=F["xs"], fill=MUTED_C,
    )
    y += 28
    draw.line([(MARGIN, y), (PAGE_W - MARGIN, y)], fill=DIVIDER_C, width=2)
    y += 18

    # Table column widths and headers
    CW    = [50, 220, 105, 195, 115, 120, 120, 75]
    HEADS = ["#", "Funds Used For", "Date", "Vendor Name", "Amount", "Account#", "Invoice#", "Sourced"]
    x = MARGIN
    for h, w in zip(HEADS, CW):
        draw.text((x, y), h.upper(), font=F["xs"], fill=MUTED_C)
        x += w
    y += 20
    draw.line([(MARGIN, y), (PAGE_W - MARGIN, y)], fill=DIVIDER_C, width=1)
    y += 10

    df = st.session_state.ledger
    total_amount, sourced_amount, _, _ = compute_totals()

    for row_num, (_, row) in enumerate(df.iterrows(), 1):
        x     = MARGIN
        cells = [
            str(row_num),
            str(row["Funds Used For"])[:30],
            str(row["Date"]),
            str(row["Vendor Name"])[:26],
            f"${float(row['Amount']):,.2f}",
            str(row["Bank Account#"]),
            str(row["Invoice#"]),
            "Yes" if row["Sourced"] else "No",
        ]
        colors = [MUTED_C] + [TEXT_C] * 6 + [GREEN_C if row["Sourced"] else RED_C]
        for cell, w, color in zip(cells, CW, colors):
            draw.text((x, y), cell, font=F["sm"], fill=color)
            x += w
        y += 26
        draw.line([(MARGIN, y - 5), (PAGE_W - MARGIN, y - 5)], fill=(240, 240, 240), width=1)

    y += 8
    draw.line([(MARGIN, y), (PAGE_W - MARGIN, y)], fill=DIVIDER_C, width=2)
    y += 14

    # Totals - shift right by the new "#" column width
    tx = MARGIN + CW[0] + CW[1] + CW[2]
    draw.text((tx, y),        "Total Amount",  font=F["md"], fill=TEXT_C)
    draw.text((tx + CW[3], y), f"${total_amount:,.2f}", font=F["md"], fill=TEXT_C)
    y += 30
    draw.text((tx, y),        "Total Sourced", font=F["md"], fill=TEXT_C)
    draw.text((tx + CW[3], y), f"${sourced_amount:,.2f}", font=F["md"], fill=GREEN_C)

    pages.append(apply_watermark(img) if watermark else img)

    # ── PAGE 2: UOP ROLL-UP ───────────────────────────────────────────────────
    img2  = Image.new("RGB", (PAGE_W, PAGE_H), BG)
    draw2 = ImageDraw.Draw(img2)
    y2 = MARGIN

    draw2.text((MARGIN, y2), "Use of Proceeds Roll-up", font=F["title"], fill=TEXT_C)
    y2 += 42
    draw2.text((MARGIN, y2), f"Loan: {LOAN_NAME}   |   Equity Required: ${EQUITY_REQUIRED:,.0f}",
               font=F["xs"], fill=MUTED_C)
    y2 += 28
    draw2.line([(MARGIN, y2), (PAGE_W - MARGIN, y2)], fill=DIVIDER_C, width=2)
    y2 += 18

    RCW2   = [50, 240, 160, 160, 200, 130]
    RHEAD2 = ["#", "UOP Item", "Total Sourced", "EI Outstanding", "Total EI Available", "Fully Sourced"]
    rx = MARGIN
    for h, w in zip(RHEAD2, RCW2):
        draw2.text((rx, y2), h.upper(), font=F["xs"], fill=MUTED_C)
        rx += w
    y2 += 20
    draw2.line([(MARGIN, y2), (PAGE_W - MARGIN, y2)], fill=DIVIDER_C, width=1)
    y2 += 10

    uop_df = st.session_state.ledger
    assigned2 = uop_df[uop_df.get("UOP Item", pd.Series(dtype=str)).isin(UOP_ITEMS)] if "UOP Item" in uop_df.columns else pd.DataFrame()
    rollup2 = []
    for uop_item in UOP_ITEMS:
        grp = assigned2[assigned2["UOP Item"] == uop_item] if not assigned2.empty else pd.DataFrame()
        if grp.empty:
            continue
        ts = grp.loc[grp["Sourced"], "Amount"].sum()
        ta = grp["Amount"].sum()
        ei_out = ta - ts
        rollup2.append((uop_item, ts, ei_out, ta, "Yes" if ei_out <= 0 else "No"))

    for r_num, (uop_item, ts, ei_out, ei_avail, fs) in enumerate(rollup2, 1):
        rx = MARGIN
        cells2 = [str(r_num), uop_item, f"${ts:,.2f}", f"${ei_out:,.2f}", f"${ei_avail:,.2f}", fs]
        colors2 = [MUTED_C, TEXT_C, GREEN_C, RED_C if ei_out > 0 else GREEN_C, TEXT_C,
                   GREEN_C if fs == "Yes" else RED_C]
        for cell, w, color in zip(cells2, RCW2, colors2):
            draw2.text((rx, y2), cell, font=F["sm"], fill=color)
            rx += w
        y2 += 26
        draw2.line([(MARGIN, y2 - 5), (PAGE_W - MARGIN, y2 - 5)], fill=(240, 240, 240), width=1)

    y2 += 8
    draw2.line([(MARGIN, y2), (PAGE_W - MARGIN, y2)], fill=DIVIDER_C, width=2)
    y2 += 14
    # Totals
    tx2 = MARGIN + RCW2[0]
    draw2.text((tx2, y2), "Totals", font=F["md"], fill=TEXT_C)
    draw2.text((tx2 + RCW2[1], y2), f"${sum(r[1] for r in rollup2):,.2f}", font=F["md"], fill=GREEN_C)
    ei_tot2 = sum(r[2] for r in rollup2)
    draw2.text((tx2 + RCW2[1] + RCW2[2], y2), f"${ei_tot2:,.2f}",
               font=F["md"], fill=GREEN_C if ei_tot2 <= 0 else RED_C)
    draw2.text((tx2 + RCW2[1] + RCW2[2] + RCW2[3], y2), f"${sum(r[3] for r in rollup2):,.2f}",
               font=F["md"], fill=TEXT_C)

    pages.append(apply_watermark(img2) if watermark else img2)
    for row_num, (idx, row) in enumerate(df.iterrows(), 1):
        sourcing   = get_sourcing(idx)
        item_label = (
            f"{row_num}. {row['Vendor Name']}  -  {row['Funds Used For']}"
            f"   |   ${float(row['Amount']):,.2f}   |   {row['Date']}"
        )

        docs = []
        inv_name = sourcing.get("invoice_file_name")
        if inv_name:
            inv_f = find_file(all_invoices, inv_name)
            inv_notes = sourcing.get("invoice_notes", "").strip()
            docs.append(("Invoice", inv_f["data"] if inv_f else None, inv_notes))
        for j, sname in enumerate(sourcing.get("statements", []), 1):
            sf = find_file(all_statements, sname)
            stmt_notes = (sourcing.get("statement_notes") or [""])[j-1] if j-1 < len(sourcing.get("statement_notes") or []) else ""
            stmt_notes = stmt_notes.strip()
            docs.append((f"Statement {j}", sf["data"] if sf else None, stmt_notes))

        if not docs:
            docs = [("No Documents Attached", None, "")]

        for doc_type, doc_data, closer_notes in docs:
            pg   = Image.new("RGB", (PAGE_W, PAGE_H), BG)
            draw = ImageDraw.Draw(pg)

            # Banner
            draw.rectangle([(0, 0), (PAGE_W, BANNER_H)], fill=BANNER_BG)
            draw.text((MARGIN, 14),  item_label[:95], font=F["sm"], fill=BANNER_FG)
            draw.text((MARGIN, 44),  doc_type,        font=F["lg"], fill=BANNER_FG)
            # Closer notes beneath doc_type title
            if closer_notes:
                draw.text((MARGIN, 82), closer_notes[:120], font=F["sm"], fill=NOTES_FG)

            # Document body
            if doc_data:
                try:
                    doc_img  = Image.open(_io.BytesIO(doc_data)).convert("RGB")
                    avail_w  = PAGE_W - 2 * MARGIN
                    avail_h  = PAGE_H - BANNER_H - 2 * MARGIN
                    doc_img.thumbnail((avail_w, avail_h), Image.LANCZOS)
                    x_off    = MARGIN + (avail_w - doc_img.width) // 2
                    pg.paste(doc_img, (x_off, BANNER_H + MARGIN))
                except Exception:
                    draw.text((MARGIN, BANNER_H + MARGIN + 40),
                              "[Could not load document image]", font=F["md"], fill=MUTED_C)
            else:
                msg_y = (PAGE_H + BANNER_H) // 2 - 20
                draw.text((MARGIN, msg_y),
                          "No document file available for this item.",
                          font=F["md"], fill=MUTED_C)

            pages.append(apply_watermark(pg) if watermark else pg)

    buf = _io.BytesIO()
    pages[0].save(buf, format="PDF", save_all=True, append_images=pages[1:])
    return buf.getvalue()

# ── LOAD LOCAL DEMO FILES ─────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_local_files():
    inv_files, stmt_files, stmt_by_acct = [], [], {}
    inv_dir = Path("invoices")
    if inv_dir.exists():
        for f in sorted(inv_dir.glob("*.png")):
            inv_files.append({"name": f.name, "data": f.read_bytes(),
                               "type": "image/png", "account": None})
    stmt_dir = Path("statements")
    if stmt_dir.exists():
        for acct_dir in sorted(stmt_dir.iterdir()):
            if not acct_dir.is_dir():
                continue
            acct_files = []
            for f in sorted(acct_dir.glob("*.png")):
                fd = {"name": f.name, "data": f.read_bytes(),
                      "type": "image/png", "account": acct_dir.name}
                stmt_files.append(fd)
                acct_files.append(fd)
            if acct_files:
                stmt_by_acct[acct_dir.name] = acct_files
    return inv_files, stmt_files, stmt_by_acct

# ── SESSION STATE INIT ────────────────────────────────────────────────────────
@st.cache_data
def load_ledger():
    try:
        df = pd.read_csv("demo_data.csv")
        df["Sourced"]       = df["Sourced"].astype(bool)
        df["Amount"]        = df["Amount"].astype(float)
        df["Date"]          = df["Date"].astype(str)
        df["Bank Account#"] = df["Bank Account#"].astype(str)
        df["Invoice#"]      = df["Invoice#"].fillna("").astype(str)
        if "UOP Item" not in df.columns:
            df["UOP Item"] = ""
        return df
    except FileNotFoundError:
        return pd.DataFrame(columns=["Funds Used For", "Date", "Vendor Name",
                                     "Amount", "Bank Account#", "Invoice#", "Sourced", "UOP Item"])

for _k, _v in [
    ("ledger",            None),
    ("auto_invoices",     None),
    ("auto_statements",   None),
    ("stmts_by_acct",     None),
    ("user_invoices",     []),
    ("user_statements",   []),
    ("sourcing",          {}),
    ("thumbnails",        {}),
    ("show_add_form",     False),
    ("initial_state_set", False),
    ("package_approved",  False),
]:
    if _k not in st.session_state:
        st.session_state[_k] = _v

if st.session_state.ledger is None:
    st.session_state.ledger = load_ledger()

if st.session_state.auto_invoices is None:
    _inv, _stmts, _by_acct = load_local_files()
    st.session_state.auto_invoices   = _inv
    st.session_state.auto_statements = _stmts
    st.session_state.stmts_by_acct  = _by_acct

all_invoices   = st.session_state.auto_invoices   + st.session_state.user_invoices
all_statements = st.session_state.auto_statements + st.session_state.user_statements

combined_by_acct = dict(st.session_state.stmts_by_acct)
_uploaded_stmts = [f for f in st.session_state.user_statements if f["account"] == "uploaded"]
_other_docs     = [f for f in st.session_state.user_statements if f["account"] == "other_docs"]
if _uploaded_stmts:
    combined_by_acct["uploaded"]   = _uploaded_stmts
# Always present so the option appears in the sourcing dropdown
combined_by_acct["other_docs"] = _other_docs

# ── SOURCING HELPERS ──────────────────────────────────────────────────────────
def get_sourcing(idx: int) -> dict:
    if idx not in st.session_state.sourcing:
        st.session_state.sourcing[idx] = {
            "invoice_file_name": None,
            "invoice_notes":     "",
            "statements":        [],
            "statement_notes":   [],   # list of notes, one per statement
            "requests":          [],
        }
    # Back-fill keys for older session state entries
    s = st.session_state.sourcing[idx]
    s.setdefault("invoice_notes", "")
    s.setdefault("statement_notes", [])
    return s

def acct_label(acct: str) -> str:
    if acct == "uploaded":
        return "Uploaded Files"
    if acct == "other_docs":
        return "Other Documents"
    files = combined_by_acct.get(acct, [])
    bank  = bank_name_from_file(files[0]["name"]) if files else ""
    num   = acct_num_from_folder(acct)
    return f"{bank}  ({num})"

if not st.session_state.initial_state_set and all_invoices:
    _s = get_sourcing(0)
    _first = all_invoices[0]["name"]
    _s["invoice_file_name"]       = _first
    st.session_state["inv_sel_0"] = _first
    st.session_state.initial_state_set = True

# ── COMPUTED TOTALS ───────────────────────────────────────────────────────────
def compute_totals():
    df = st.session_state.ledger
    if df.empty:
        return 0.0, 0.0, 0.0, EQUITY_REQUIRED
    total     = df["Amount"].sum()
    sourced   = df.loc[df["Sourced"],  "Amount"].sum()
    unsourced = df.loc[~df["Sourced"], "Amount"].sum()
    return total, sourced, unsourced, EQUITY_REQUIRED - sourced

# ══════════════════════════════════════════════════════════════════════════════
# PAGE TITLE
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("# Closing Equity Injection")
st.markdown("---")

tab1, tab2, tab3 = st.tabs(["Equity Injection", "Statements", "Other Documents"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 - EQUITY INJECTION
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    total_amount, sourced_amount, unsourced_amount, equity_remaining = compute_totals()

    # ── LOAN INFO - plain text, same column layout ────────────────────────────
    c1, c2, c3, c4, c5, c6 = st.columns([2, 1.5, 1.5, 1.5, 1.5, 1.5])

    c1.markdown(f"""<div>
        <div class="loan-label">Loan Name</div>
        <div class="loan-value">{LOAN_NAME}</div>
    </div>""", unsafe_allow_html=True)

    c2.markdown(f"""<div>
        <div class="loan-label">Loan Amount</div>
        <div class="loan-value">${LOAN_AMOUNT:,.0f}</div>
    </div>""", unsafe_allow_html=True)

    c3.markdown(f"""<div>
        <div class="loan-label">Equity Injection Required</div>
        <div class="loan-value">${EQUITY_REQUIRED:,.0f}</div>
    </div>""", unsafe_allow_html=True)

    c4.markdown(f"""<div>
        <div class="loan-label">Equity Injection Total</div>
        <div class="loan-value">${total_amount:,.2f}</div>
    </div>""", unsafe_allow_html=True)

    rem_color = "#198754" if equity_remaining <= 0 else "#dc3545"
    c5.markdown(f"""<div>
        <div class="loan-label">Equity Injection Remaining</div>
        <div class="loan-value" style="color:{rem_color}">${equity_remaining:,.2f}</div>
    </div>""", unsafe_allow_html=True)

    uns_color = "#dc3545" if unsourced_amount > 0 else "#198754"
    c6.markdown(f"""<div>
        <div class="loan-label">Equity Injection Unsourced</div>
        <div class="loan-value" style="color:{uns_color}">${unsourced_amount:,.2f}</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── DOCUMENT UPLOAD ───────────────────────────────────────────────────────
    col_inv, col_stmt = st.columns(2)

    with col_inv:
        st.markdown("**Invoices / Receipts**")
        up_inv = st.file_uploader(
            "invoices", type=["pdf", "png", "jpg", "jpeg"],
            accept_multiple_files=True, key="inv_uploader",
            label_visibility="collapsed"
        )
        if up_inv:
            existing = {f["name"] for f in st.session_state.user_invoices}
            for f in up_inv:
                if f.name not in existing:
                    st.session_state.user_invoices.append(
                        {"name": f.name, "data": f.read(), "type": f.type, "account": None}
                    )
        if all_invoices:
            st.caption(f"{len(all_invoices)} invoice(s) available")

    with col_stmt:
        st.markdown("**Bank / Credit Card Statements**")
        up_stmt = st.file_uploader(
            "statements", type=["pdf", "png", "jpg", "jpeg"],
            accept_multiple_files=True, key="stmt_uploader",
            label_visibility="collapsed"
        )
        if up_stmt:
            existing = {f["name"] for f in st.session_state.user_statements}
            for f in up_stmt:
                if f.name not in existing:
                    st.session_state.user_statements.append(
                        {"name": f.name, "data": f.read(), "type": f.type, "account": "uploaded"}
                    )
            combined_by_acct["uploaded"] = [
                f for f in st.session_state.user_statements if f["account"] == "uploaded"
            ]
        if all_statements:
            st.caption(f"{len(all_statements)} statement(s) available")

    st.markdown("---")

    # ── LEDGER ────────────────────────────────────────────────────────────────
    st.markdown("### Ledger")

    ledger = st.session_state.ledger
    # Added "#" column at the start, UOP Item at end
    CW    = [0.3, 2.0, 1.3, 1.8, 1.1, 1.3, 1.3, 0.8, 1.5, 0.4]
    HEADS = ["#", "Funds Used For", "Date", "Vendor Name", "Amount ($)",
             "Bank Account#", "Invoice#", "Fully Sourced", "UOP Item", ""]

    hcols = st.columns(CW)
    for col, lbl in zip(hcols, HEADS):
        col.markdown(f'<div class="ledger-header">{lbl}</div>', unsafe_allow_html=True)

    to_del = []
    if ledger.empty:
        st.markdown("*No entries yet.*")
    else:
        for row_num, (idx, row) in enumerate(ledger.iterrows(), 1):
            rc = st.columns(CW)
            rc[0].markdown(f'<div class="ledger-row" style="color:#6c757d">{row_num}</div>', unsafe_allow_html=True)
            rc[1].markdown(f'<div class="ledger-row">{row["Funds Used For"]}</div>', unsafe_allow_html=True)
            rc[2].markdown(f'<div class="ledger-row">{row["Date"]}</div>', unsafe_allow_html=True)
            rc[3].markdown(f'<div class="ledger-row">{row["Vendor Name"]}</div>', unsafe_allow_html=True)
            rc[4].markdown(f'<div class="ledger-row">${float(row["Amount"]):,.2f}</div>', unsafe_allow_html=True)
            rc[5].markdown(f'<div class="ledger-row">{row["Bank Account#"]}</div>', unsafe_allow_html=True)
            rc[6].markdown(f'<div class="ledger-row">{row["Invoice#"]}</div>', unsafe_allow_html=True)
            sc = "sourced-yes" if row["Sourced"] else "sourced-no"
            sl = "Yes" if row["Sourced"] else "No"
            rc[7].markdown(f'<div class="ledger-row {sc}">{sl}</div>', unsafe_allow_html=True)
            # UOP Item dropdown inline in ledger
            cur_uop = row.get("UOP Item", "") if "UOP Item" in row.index else ""
            uop_opts = ["- Select -"] + UOP_ITEMS
            uop_default = uop_opts.index(cur_uop) if cur_uop in uop_opts else 0
            new_uop = rc[8].selectbox(
                "uop", uop_opts, index=uop_default,
                key=f"uop_{idx}", label_visibility="collapsed"
            )
            if new_uop != "- Select -":
                st.session_state.ledger.at[idx, "UOP Item"] = new_uop
            elif "UOP Item" not in st.session_state.ledger.columns or st.session_state.ledger.at[idx, "UOP Item"] not in UOP_ITEMS:
                st.session_state.ledger.at[idx, "UOP Item"] = ""
            if rc[9].button("x", key=f"del_{idx}", help="Delete entry"):
                to_del.append(idx)

    if to_del:
        st.session_state.ledger = ledger.drop(to_del).reset_index(drop=True)
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    tc = st.columns(CW)
    tc[3].markdown('<div class="total-row">Total Amount</div>', unsafe_allow_html=True)
    tc[4].markdown(f'<div class="total-row">${total_amount:,.2f}</div>', unsafe_allow_html=True)
    sc2 = st.columns(CW)
    sc2[3].markdown('<div class="total-row">Total Sourced</div>', unsafe_allow_html=True)
    sc2[4].markdown(f'<div class="total-row" style="color:#198754">${sourced_amount:,.2f}</div>',
                    unsafe_allow_html=True)
    ei_closing = max(0.0, EQUITY_REQUIRED - sourced_amount)
    ei_closing_color = "#dc3545" if ei_closing > 0 else "#198754"
    ec = st.columns(CW)
    ec[3].markdown('<div class="total-row">Additional EI Required to Close</div>', unsafe_allow_html=True)
    ec[4].markdown(f'<div class="total-row" style="color:{ei_closing_color}">${ei_closing:,.2f}</div>',
                   unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("+ Add Entry", type="secondary"):
        st.session_state.show_add_form = not st.session_state.show_add_form

    if st.session_state.show_add_form:
        with st.form("add_entry_form", clear_on_submit=True):
            st.markdown("**New Ledger Entry**")
            c1, c2, c3, c4, c5, c6, c7, c8 = st.columns([2.5, 1.4, 2, 1.2, 1.4, 1.4, 0.8, 1.5])
            nf = c1.text_input("Funds Used For*")
            nd = c2.date_input("Date", value=date.today())
            nv = c3.text_input("Vendor Name*")
            na = c4.number_input("Amount ($)*", min_value=0.0, value=0.0, format="%.2f")
            nb = c5.text_input("Bank Account#")
            ni = c6.text_input("Invoice#")
            ns = c7.checkbox("Sourced")
            nu = c8.selectbox("UOP Item", ["- Select -"] + UOP_ITEMS)
            if st.form_submit_button("Add Entry", type="primary"):
                if not nf or not nv:
                    st.error("Funds Used For and Vendor Name are required.")
                else:
                    st.session_state.ledger = pd.concat([
                        st.session_state.ledger,
                        pd.DataFrame([{"Funds Used For": nf, "Date": str(nd),
                                       "Vendor Name": nv, "Amount": na,
                                       "Bank Account#": nb, "Invoice#": ni, "Sourced": ns,
                                       "UOP Item": nu if nu != "- Select -" else ""}])
                    ], ignore_index=True)
                    st.session_state.show_add_form = False
                    st.rerun()

    st.markdown("---")

    # ── UOP ROLL-UP ───────────────────────────────────────────────────────────
    st.markdown("### Use of Proceeds Roll-up")

    df_uop = st.session_state.ledger
    if df_uop.empty or "UOP Item" not in df_uop.columns:
        st.markdown("*Assign UOP Items in the ledger above to see the roll-up.*")
    else:
        assigned = df_uop[df_uop["UOP Item"].isin(UOP_ITEMS)]
        if assigned.empty:
            st.markdown("*Assign UOP Items in the ledger above to see the roll-up.*")
        else:
            # Build roll-up grouped by UOP Item (preserve order of UOP_ITEMS)
            rollup_rows = []
            for uop_item in UOP_ITEMS:
                grp = assigned[assigned["UOP Item"] == uop_item]
                if grp.empty:
                    continue
                total_sourced = grp.loc[grp["Sourced"], "Amount"].sum()
                total_amount  = grp["Amount"].sum()
                ei_outstanding = total_amount - total_sourced
                total_ei_avail = EQUITY_REQUIRED  # same pool for all items
                fully_sourced  = "Yes" if ei_outstanding <= 0 else "No"
                rollup_rows.append({
                    "UOP Item":           uop_item,
                    "Total Sourced":      total_sourced,
                    "EI Outstanding":     ei_outstanding,
                    "Total EI Available": total_amount,
                    "Fully Sourced":      fully_sourced,
                })

            RCW   = [0.3, 2.0, 1.5, 1.5, 1.8, 1.2]
            RHEADS = ["#", "UOP Item", "Total Sourced", "EI Outstanding",
                      "Total EI Available", "Fully Sourced"]
            rhcols = st.columns(RCW)
            for col, lbl in zip(rhcols, RHEADS):
                col.markdown(f'<div class="ledger-header">{lbl}</div>', unsafe_allow_html=True)

            for r_num, rrow in enumerate(rollup_rows, 1):
                rrc = st.columns(RCW)
                rrc[0].markdown(f'<div class="ledger-row" style="color:#6c757d">{r_num}</div>', unsafe_allow_html=True)
                rrc[1].markdown(f'<div class="ledger-row">{rrow["UOP Item"]}</div>', unsafe_allow_html=True)
                rrc[2].markdown(f'<div class="ledger-row" style="color:#198754">${rrow["Total Sourced"]:,.2f}</div>', unsafe_allow_html=True)
                ei_color = "#dc3545" if rrow["EI Outstanding"] > 0 else "#198754"
                rrc[3].markdown(f'<div class="ledger-row" style="color:{ei_color}">${rrow["EI Outstanding"]:,.2f}</div>', unsafe_allow_html=True)
                rrc[4].markdown(f'<div class="ledger-row">${rrow["Total EI Available"]:,.2f}</div>', unsafe_allow_html=True)
                fs_c = "sourced-yes" if rrow["Fully Sourced"] == "Yes" else "sourced-no"
                rrc[5].markdown(f'<div class="ledger-row {fs_c}">{rrow["Fully Sourced"]}</div>', unsafe_allow_html=True)

            # Totals row
            st.markdown("<br>", unsafe_allow_html=True)
            rtc = st.columns(RCW)
            rtc[1].markdown('<div class="total-row">Totals</div>', unsafe_allow_html=True)
            rtc[2].markdown(f'<div class="total-row" style="color:#198754">${sum(r["Total Sourced"] for r in rollup_rows):,.2f}</div>', unsafe_allow_html=True)
            ei_tot = sum(r["EI Outstanding"] for r in rollup_rows)
            ei_tot_color = "#dc3545" if ei_tot > 0 else "#198754"
            rtc[3].markdown(f'<div class="total-row" style="color:{ei_tot_color}">${ei_tot:,.2f}</div>', unsafe_allow_html=True)
            rtc[4].markdown(f'<div class="total-row">${sum(r["Total EI Available"] for r in rollup_rows):,.2f}</div>', unsafe_allow_html=True)
            uop_sourced_total = sum(r["Total Sourced"] for r in rollup_rows)
            uop_ei_closing = max(0.0, EQUITY_REQUIRED - uop_sourced_total)
            uop_ei_closing_color = "#dc3545" if uop_ei_closing > 0 else "#198754"
            rec = st.columns(RCW)
            rec[1].markdown('<div class="total-row">Additional EI Required to Close</div>', unsafe_allow_html=True)
            rec[2].markdown(f'<div class="total-row" style="color:{uop_ei_closing_color}">${uop_ei_closing:,.2f}</div>', unsafe_allow_html=True)

    st.markdown("---")

    # ── DOCUMENT SOURCING ─────────────────────────────────────────────────────
    st.markdown("### Document Sourcing")

    inv_names = [f["name"] for f in all_invoices]

    if st.session_state.ledger.empty:
        st.markdown("*No ledger entries to source.*")
    else:
        for row_num, (idx, row) in enumerate(st.session_state.ledger.iterrows(), 1):
            sourcing = get_sourcing(idx)
            # Number prefix in the expander label
            label    = f"{row_num}. {row['Vendor Name']}  -  {row['Funds Used For']}  |  ${float(row['Amount']):,.2f}"

            with st.expander(label, expanded=(idx == 0)):

                # Inject hidden marker so CSS :has() can make this expander green
                if row["Sourced"]:
                    st.markdown(
                        '<div class="sourced-item-marker" style="display:none"></div>',
                        unsafe_allow_html=True
                    )
                # Inject hidden marker for yellow highlight when requests are outstanding
                if sourcing.get("requests"):
                    st.markdown(
                        '<div class="request-outstanding-marker" style="display:none"></div>',
                        unsafe_allow_html=True
                    )

                # ── DOCUMENT CARD ROW ─────────────────────────────────────────
                n_stmts  = len(sourcing["statements"])
                doc_cols = st.columns(MAX_DOC_COLS)

                # Invoice card - col 0
                with doc_cols[0]:
                    st.markdown(col_label("Invoice / Receipt"), unsafe_allow_html=True)
                    inv_opts = ["- Select invoice -"] + inv_names
                    sel_inv  = st.selectbox(
                        "inv", inv_opts, key=f"inv_sel_{idx}",
                        label_visibility="collapsed"
                    )
                    if sel_inv != "- Select invoice -":
                        sourcing["invoice_file_name"] = sel_inv
                        inv_f = find_file(all_invoices, sel_inv)
                        st.markdown(
                            doc_card_html(sel_inv, inv_f["data"] if inv_f else None),
                            unsafe_allow_html=True
                        )
                        if inv_f:
                            with st.expander("View", expanded=False):
                                st.image(inv_f["data"], use_container_width=True)
                    else:
                        sourcing["invoice_file_name"] = None
                        st.markdown(
                            '<div class="doc-card-empty">No invoice<br>assigned</div>',
                            unsafe_allow_html=True
                        )
                    st.selectbox(
                        "inv_status", STATUS_OPTIONS,
                        key=f"inv_status_{idx}", label_visibility="collapsed"
                    )
                    # Closer notes text box for invoice
                    inv_notes_val = st.text_area(
                        "Closer Notes",
                        value=sourcing.get("invoice_notes", ""),
                        key=f"inv_notes_{idx}",
                        placeholder="Add closer notes for this invoice...",
                        height=80,
                    )
                    sourcing["invoice_notes"] = inv_notes_val

                # Statement cards - cols 1..n_stmts
                stmts_to_remove = []
                # Ensure statement_notes list is long enough
                while len(sourcing["statement_notes"]) < len(sourcing["statements"]):
                    sourcing["statement_notes"].append("")

                for j, sname in enumerate(sourcing["statements"]):
                    if j + 1 >= MAX_DOC_COLS:
                        break
                    with doc_cols[j + 1]:
                        st.markdown(col_label(f"Statement {j + 1}"), unsafe_allow_html=True)
                        sf = find_file(all_statements, sname)
                        st.markdown(
                            doc_card_html(sname, sf["data"] if sf else None),
                            unsafe_allow_html=True
                        )
                        if sf:
                            with st.expander("View", expanded=False):
                                st.image(sf["data"], use_container_width=True)
                        st.selectbox(
                            f"stmt_status_{j}", STATUS_OPTIONS,
                            key=f"stmt_status_{idx}_{j}", label_visibility="collapsed"
                        )
                        # Closer notes text box for this statement
                        stmt_notes_val = st.text_area(
                            "Closer Notes",
                            value=sourcing["statement_notes"][j],
                            key=f"stmt_notes_{idx}_{j}",
                            placeholder=f"Add closer notes for Statement {j+1}...",
                            height=80,
                        )
                        sourcing["statement_notes"][j] = stmt_notes_val

                        if st.button("Remove", key=f"rm_{idx}_{j}"):
                            stmts_to_remove.append(j)

                if stmts_to_remove:
                    sourcing["statements"] = [
                        s for i, s in enumerate(sourcing["statements"])
                        if i not in stmts_to_remove
                    ]
                    sourcing["statement_notes"] = [
                        n for i, n in enumerate(sourcing["statement_notes"])
                        if i not in stmts_to_remove
                    ]
                    st.rerun()

                # Add Statement card - next available col
                add_col_idx = n_stmts + 1
                if add_col_idx < MAX_DOC_COLS:
                    with doc_cols[add_col_idx]:
                        st.markdown(col_label("Add Statement"), unsafe_allow_html=True)
                        avail_accts = {
                            acct: [f for f in files if f["name"] not in sourcing["statements"]]
                            for acct, files in combined_by_acct.items()
                        }
                        # Keep non-empty accounts + always keep other_docs
                        avail_accts = {
                            k: v for k, v in avail_accts.items()
                            if v or k == "other_docs"
                        }

                        # Upload zone - styled via CSS to look like doc-card-add
                        up_new_stmt = st.file_uploader(
                            "upload_stmt", type=["pdf", "png", "jpg", "jpeg"],
                            key=f"stmt_upload_{idx}", label_visibility="collapsed"
                        )
                        if up_new_stmt is not None:
                            existing_names = {
                                f["name"] for f in st.session_state.user_statements
                            }
                            if up_new_stmt.name not in existing_names:
                                new_fd = {
                                    "name":    up_new_stmt.name,
                                    "data":    up_new_stmt.read(),
                                    "type":    up_new_stmt.type,
                                    "account": "other_docs",
                                }
                                st.session_state.user_statements.append(new_fd)
                                sourcing["statements"].append(up_new_stmt.name)
                                sourcing["statement_notes"].append("")
                                st.rerun()

                        # Select from existing loaded statements / other docs
                        if avail_accts:
                            acct_opts = ["- Select Account -"] + list(avail_accts.keys())
                            sel_acct  = st.selectbox(
                                "acct_sel", acct_opts,
                                key=f"acct_sel_{idx}",
                                label_visibility="collapsed",
                                format_func=lambda x: acct_label(x) if x != "- Select Account -" else x
                            )
                            if sel_acct != "- Select Account -":
                                avail_stmts = [f["name"] for f in avail_accts[sel_acct]]
                                if not avail_stmts:
                                    st.caption("No other documents yet. Upload one above.")
                                else:
                                    sel_stmt = st.selectbox(
                                        "stmt_sel", ["- Select Statement -"] + avail_stmts,
                                        key=f"stmt_sel_{idx}",
                                        label_visibility="collapsed",
                                        format_func=lambda x: parse_month(x)
                                        if x != "- Select Statement -" else x
                                    )
                                    if sel_stmt != "- Select Statement -":
                                        if st.button("Add", key=f"add_stmt_{idx}", type="primary"):
                                            sourcing["statements"].append(sel_stmt)
                                            sourcing["statement_notes"].append("")
                                            for _k in [f"acct_sel_{idx}", f"stmt_sel_{idx}"]:
                                                st.session_state.pop(_k, None)
                                            st.rerun()

                st.markdown("<br>", unsafe_allow_html=True)

                # ── RIGHT-SIDE ACTIONS: sourced dropdown + request button ─────
                show_key = f"show_req_{idx}"
                _, right_col = st.columns([3, 1])

                with right_col:
                    # Sourced status dropdown
                    sourced_choice = st.selectbox(
                        "Sourced Status",
                        ["Unsourced", "Sourced"],
                        index=1 if bool(row["Sourced"]) else 0,
                        key=f"sourced_sel_{idx}",
                    )
                    new_sourced = (sourced_choice == "Sourced")
                    if new_sourced != bool(row["Sourced"]):
                        st.session_state.ledger.at[idx, "Sourced"] = new_sourced
                        st.rerun()

                    # Request Missing Document
                    if st.button("Request Missing Document", key=f"req_btn_{idx}",
                                 use_container_width=True):
                        st.session_state[show_key] = not st.session_state.get(show_key, False)

                # Request form - full width below
                if st.session_state.get(show_key, False):
                    with st.form(f"req_form_{idx}", clear_on_submit=True):
                        desc = st.text_area(
                            "Describe the missing document",
                            placeholder="e.g. Bank statement for ****4821, November 2025",
                            height=70
                        )
                        if st.form_submit_button("Add Request"):
                            if desc.strip():
                                sourcing["requests"].append({
                                    "item":        f"{row['Vendor Name']} - {row['Funds Used For']}",
                                    "description": desc.strip(),
                                })
                                st.session_state[show_key] = False
                                st.rerun()

                if sourcing["requests"]:
                    st.markdown("**Outstanding requests for this item:**")
                    req_to_remove = None
                    for r_idx, r in enumerate(sourcing["requests"]):
                        r_col, del_col = st.columns([10, 1])
                        r_col.markdown(f"&nbsp;&nbsp;• {r['description']}")
                        if del_col.button("x", key=f"del_req_{idx}_{r_idx}", help="Remove request"):
                            req_to_remove = r_idx
                    if req_to_remove is not None:
                        sourcing["requests"].pop(req_to_remove)
                        st.rerun()

    st.markdown("---")

    # ── PENDING REQUESTS ──────────────────────────────────────────────────────
    st.markdown("### Pending Requests")

    all_reqs = [
        r for idx in st.session_state.sourcing
        for r in st.session_state.sourcing[idx].get("requests", [])
    ]

    if not all_reqs:
        st.markdown("*No outstanding requests.*")
    else:
        st.caption(f"{len(all_reqs)} outstanding request(s)")
        for r in all_reqs:
            st.markdown(f"""<div class="req-card">
                <div style="font-size:0.78rem;color:#6c757d;font-weight:600;margin-bottom:3px">
                    {r['item']}</div>
                <div style="font-size:0.9rem;color:#212529">{r['description']}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ── EXPORT PACKAGE ────────────────────────────────────────────────────────
    st.markdown("### Export Package")

    df_check    = st.session_state.ledger
    all_sourced = (not df_check.empty) and bool(df_check["Sourced"].all())

    # ── DRAFT / REVIEW COPY (always available) + approval checkbox ────────────
    st.markdown("#### Draft - Review Copy")
    st.caption("Watermarked PDF for internal review.")

    draft_col, approval_col = st.columns([3, 2])

    with draft_col:
        if st.button("Generate Draft PDF", type="secondary"):
            with st.spinner("Building draft PDF..."):
                try:
                    st.session_state["draft_pdf"] = build_package_pdf(watermark=True)
                except Exception as e:
                    st.error(f"Error generating draft PDF: {e}")
                    st.session_state.pop("draft_pdf", None)

        if st.session_state.get("draft_pdf"):
            fname_draft = f"DRAFT_closing_package_{LOAN_NAME.replace(' ', '_')}.pdf"
            st.download_button(
                label="Download Draft PDF",
                data=st.session_state["draft_pdf"],
                file_name=fname_draft,
                mime="application/pdf",
            )

    with approval_col:
        is_approved = st.checkbox(
            "Approved",
            value=st.session_state.get("package_approved", False),
            key="approval_checkbox",
        )
        if is_approved != st.session_state.get("package_approved", False):
            st.session_state["package_approved"] = is_approved
            st.session_state.pop("final_pdf", None)
            st.rerun()
        if is_approved:
            st.caption("Package approved - final PDF unlocked.")
        else:
            st.caption("Check to approve and unlock the final PDF.")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── FINAL / APPROVED COPY (requires approval checkbox + all sourced) ───────
    st.markdown("#### Final - Approved Package")

    if not is_approved:
        st.caption("Approve the package above to unlock the final PDF.")
    elif not all_sourced:
        st.warning("All ledger items must be marked **Sourced** before the final package can be generated.")
    else:
        st.success("All items sourced and package approved - final PDF available.")
        if st.button("Generate Final PDF", type="primary"):
            with st.spinner("Building final PDF..."):
                try:
                    st.session_state["final_pdf"] = build_package_pdf(watermark=False)
                except Exception as e:
                    st.error(f"Error generating final PDF: {e}")
                    st.session_state.pop("final_pdf", None)

        if st.session_state.get("final_pdf"):
            fname_final = f"FINAL_closing_package_{LOAN_NAME.replace(' ', '_')}.pdf"
            st.download_button(
                label="Download Final PDF",
                data=st.session_state["final_pdf"],
                file_name=fname_final,
                mime="application/pdf",
            )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 - STATEMENTS
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("### Bank / Credit Card Statements")

    stmt_accts = {k: v for k, v in combined_by_acct.items() if k != "other_docs"}

    if not stmt_accts:
        st.info("No statements loaded. Run generate_examples.py to create demo documents.")
    else:
        for acct_folder, files in stmt_accts.items():
            bank_name = bank_name_from_file(files[0]["name"]) if files else "Uploaded"
            acct_num  = acct_num_from_folder(acct_folder)
            header    = (f"{bank_name}  ({acct_num})"
                         if acct_folder != "uploaded" else "Uploaded Statements")

            with st.expander(header, expanded=True):
                st.caption(f"{len(files)} statement(s)")
                for row_start in range(0, len(files), MAX_DOC_COLS):
                    row_files = files[row_start: row_start + MAX_DOC_COLS]
                    cols      = st.columns(MAX_DOC_COLS)
                    for col, fd in zip(cols, row_files):
                        with col:
                            month_label = parse_month(fd["name"])
                            thumb       = get_thumbnail(fd["name"], fd["data"])
                            if thumb:
                                card_html = (
                                    f'<div class="doc-card">'
                                    f'<img src="{thumb}" style="max-width:100%;max-height:168px;'
                                    f'object-fit:contain;border-radius:3px;margin-bottom:4px">'
                                    f'<div style="font-size:0.72rem;color:#495057;font-weight:600;'
                                    f'text-align:center">{month_label}</div>'
                                    f'</div>'
                                )
                            else:
                                card_html = (
                                    f'<div class="doc-card">'
                                    f'{file_ext_badge(fd["name"])}'
                                    f'<div style="font-size:0.72rem;color:#495057;font-weight:600;'
                                    f'text-align:center">{month_label}</div>'
                                    f'</div>'
                                )
                            st.markdown(card_html, unsafe_allow_html=True)
                            with st.expander("View", expanded=False):
                                st.image(fd["data"], use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 - OTHER DOCUMENTS
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("### Other Documents")

    other_docs = combined_by_acct.get("other_docs", [])

    if not other_docs:
        st.info("No other documents uploaded yet. Use the upload zone in Document Sourcing to add files here.")
    else:
        st.caption(f"{len(other_docs)} document(s)")
        for row_start in range(0, len(other_docs), MAX_DOC_COLS):
            row_files = other_docs[row_start: row_start + MAX_DOC_COLS]
            cols      = st.columns(MAX_DOC_COLS)
            for col, fd in zip(cols, row_files):
                with col:
                    thumb = get_thumbnail(fd["name"], fd["data"])
                    if thumb:
                        card_html = (
                            f'<div class="doc-card">'
                            f'<img src="{thumb}" style="max-width:100%;max-height:168px;'
                            f'object-fit:contain;border-radius:3px;margin-bottom:4px">'
                            f'<div style="font-size:0.72rem;color:#495057;word-break:break-all;'
                            f'text-align:center;line-height:1.3">{fd["name"]}</div>'
                            f'</div>'
                        )
                    else:
                        card_html = (
                            f'<div class="doc-card">'
                            f'{file_ext_badge(fd["name"])}'
                            f'<div style="font-size:0.72rem;color:#495057;word-break:break-all;'
                            f'text-align:center;line-height:1.3">{fd["name"]}</div>'
                            f'</div>'
                        )
                    st.markdown(card_html, unsafe_allow_html=True)
                    with st.expander("View", expanded=False):
                        st.image(fd["data"], use_container_width=True)