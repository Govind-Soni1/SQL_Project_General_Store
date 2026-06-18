# ==============================================================
# Excel Export — styled export using openpyxl
# ==============================================================

import os
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from config import REPORTS_DIR


def _ensure_reports_dir():
    os.makedirs(REPORTS_DIR, exist_ok=True)


def export_to_excel(data, columns, filename=None, sheet_name="Report", title=None):
    """Export a list of dicts to a styled Excel file.

    Parameters
    ----------
    data : list[dict]
        Each dict represents a row.
    columns : list[tuple]
        Each tuple: (dict_key, display_header, optional_width).
        e.g. [("product_name", "Product Name", 30), ("stock", "Stock", 12)]
    filename : str or None
        Output filename (without path). If None, auto-generated.
    sheet_name : str
    title : str or None
        Optional title row at the top.

    Returns
    -------
    str : full path to the generated .xlsx file
    """
    _ensure_reports_dir()

    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{sheet_name.replace(' ', '_')}_{timestamp}.xlsx"

    if not filename.endswith(".xlsx"):
        filename += ".xlsx"

    filepath = os.path.join(REPORTS_DIR, filename)

    wb = Workbook()
    ws = wb.active
    ws.title = sheet_name

    # ---- Styles ----
    header_font = Font(name="Calibri", bold=True, size=11, color="FFFFFF")
    header_fill = PatternFill(start_color="0F3460", end_color="0F3460", fill_type="solid")
    header_align = Alignment(horizontal="center", vertical="center", wrap_text=True)

    data_font = Font(name="Calibri", size=10)
    data_align = Alignment(vertical="center", wrap_text=True)
    alt_fill = PatternFill(start_color="F0F4FF", end_color="F0F4FF", fill_type="solid")

    thin_border = Border(
        left=Side(style="thin", color="CCCCCC"),
        right=Side(style="thin", color="CCCCCC"),
        top=Side(style="thin", color="CCCCCC"),
        bottom=Side(style="thin", color="CCCCCC"),
    )

    title_font = Font(name="Calibri", bold=True, size=14, color="1A1A2E")

    current_row = 1

    # ---- Title Row ----
    if title:
        ws.merge_cells(start_row=1, start_column=1,
                       end_row=1, end_column=len(columns))
        cell = ws.cell(row=1, column=1, value=title)
        cell.font = title_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
        current_row = 3  # Leave a blank row

    # ---- Header Row ----
    for col_idx, col_def in enumerate(columns, 1):
        header_text = col_def[1] if len(col_def) > 1 else col_def[0]
        cell = ws.cell(row=current_row, column=col_idx, value=header_text)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_align
        cell.border = thin_border

        # Column width
        width = col_def[2] if len(col_def) > 2 else max(len(header_text) + 4, 12)
        ws.column_dimensions[get_column_letter(col_idx)].width = width

    current_row += 1

    # ---- Data Rows ----
    for row_idx, row_data in enumerate(data):
        for col_idx, col_def in enumerate(columns, 1):
            key = col_def[0]
            value = row_data.get(key, "")
            cell = ws.cell(row=current_row, column=col_idx, value=value)
            cell.font = data_font
            cell.alignment = data_align
            cell.border = thin_border

            if row_idx % 2 == 1:
                cell.fill = alt_fill

        current_row += 1

    # ---- Auto-fit (fallback widths) ----
    ws.auto_filter.ref = ws.dimensions

    wb.save(filepath)
    return filepath
