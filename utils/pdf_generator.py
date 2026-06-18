# ==============================================================
# PDF Invoice Generator — professional invoice using reportlab
# ==============================================================

import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

from config import STORE_NAME, STORE_ADDRESS, STORE_PHONE, STORE_GSTIN, REPORTS_DIR


def _ensure_reports_dir():
    os.makedirs(REPORTS_DIR, exist_ok=True)


def generate_sale_invoice(sale_data, items, customer):
    """Generate a professional PDF invoice for a sale.

    Parameters
    ----------
    sale_data : dict   (from sales_service.get_sale or save_sale return)
    items : list[dict] (product_name, quantity, selling_price, amount, unit)
    customer : dict    (customer_name, phone, address)

    Returns
    -------
    str : path to the generated PDF file
    """
    _ensure_reports_dir()
    bill_number = sale_data.get("bill_number", "BILL-0000")
    filename = os.path.join(REPORTS_DIR, f"{bill_number}.pdf")

    doc = SimpleDocTemplate(
        filename, pagesize=A4,
        rightMargin=15 * mm, leftMargin=15 * mm,
        topMargin=15 * mm, bottomMargin=15 * mm,
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        "StoreTitle", parent=styles["Title"],
        fontSize=18, textColor=colors.HexColor("#1a1a2e"),
        spaceAfter=2,
    ))
    styles.add(ParagraphStyle(
        "StoreSubtitle", parent=styles["Normal"],
        fontSize=9, textColor=colors.HexColor("#555555"),
        alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        "SectionHeader", parent=styles["Heading3"],
        fontSize=11, textColor=colors.HexColor("#0f3460"),
        spaceBefore=10, spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        "RightAlign", parent=styles["Normal"],
        alignment=TA_RIGHT, fontSize=9,
    ))
    styles.add(ParagraphStyle(
        "SmallText", parent=styles["Normal"],
        fontSize=9, textColor=colors.HexColor("#333333"),
    ))

    elements = []

    # ---- Store Header ----
    elements.append(Paragraph(STORE_NAME, styles["StoreTitle"]))
    elements.append(Paragraph(STORE_ADDRESS, styles["StoreSubtitle"]))
    elements.append(Paragraph(
        f"Phone: {STORE_PHONE} | GSTIN: {STORE_GSTIN}", styles["StoreSubtitle"]
    ))
    elements.append(Spacer(1, 3 * mm))
    elements.append(HRFlowable(
        width="100%", thickness=1, color=colors.HexColor("#0f3460"),
    ))
    elements.append(Spacer(1, 3 * mm))

    # ---- Bill Info ----
    sale_date = sale_data.get("sale_date", datetime.now())
    if isinstance(sale_date, str):
        sale_date = datetime.strptime(sale_date, "%Y-%m-%d %H:%M:%S")

    bill_info_data = [
        [
            Paragraph(f"<b>Bill No:</b> {bill_number}", styles["SmallText"]),
            Paragraph(
                f"<b>Date:</b> {sale_date.strftime('%d-%b-%Y %I:%M %p') if isinstance(sale_date, datetime) else str(sale_date)}",
                styles["RightAlign"],
            ),
        ]
    ]
    bill_info_table = Table(bill_info_data, colWidths=["50%", "50%"])
    bill_info_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    elements.append(bill_info_table)
    elements.append(Spacer(1, 3 * mm))

    # ---- Customer Info ----
    elements.append(Paragraph("Bill To:", styles["SectionHeader"]))
    cust_name = customer.get("customer_name", "N/A")
    cust_phone = customer.get("phone", "")
    cust_addr = customer.get("address", "")
    elements.append(Paragraph(f"<b>{cust_name}</b>", styles["SmallText"]))
    if cust_phone:
        elements.append(Paragraph(f"Phone: {cust_phone}", styles["SmallText"]))
    if cust_addr:
        elements.append(Paragraph(f"Address: {cust_addr}", styles["SmallText"]))
    elements.append(Spacer(1, 4 * mm))

    # ---- Items Table ----
    table_data = [["S.No", "Product", "Qty", "Unit", "Rate (₹)", "Amount (₹)"]]
    for i, item in enumerate(items, 1):
        table_data.append([
            str(i),
            str(item.get("product_name", "")),
            str(item.get("quantity", 0)),
            str(item.get("unit", "Pcs")),
            f"{float(item.get('selling_price', 0)):,.2f}",
            f"{float(item.get('amount', 0)):,.2f}",
        ])

    item_table = Table(
        table_data,
        colWidths=[30, 180, 45, 40, 75, 85],
        repeatRows=1,
    )
    item_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f3460")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (2, 0), (-1, -1), "CENTER"),
        ("ALIGN", (-2, 1), (-1, -1), "RIGHT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
            colors.HexColor("#f8f8ff"), colors.white
        ]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(item_table)
    elements.append(Spacer(1, 4 * mm))

    # ---- Totals ----
    subtotal = float(sale_data.get("subtotal", 0))
    discount_amount = float(sale_data.get("discount_amount", 0))
    discount_pct = float(sale_data.get("discount_pct", 0))
    gst_amount = float(sale_data.get("gst_amount", 0))
    grand_total = float(sale_data.get("grand_total", 0))
    paid_amount = float(sale_data.get("paid_amount", 0))
    due_amount = float(sale_data.get("due_amount", 0))

    totals_data = [
        ["", "Subtotal:", f"₹ {subtotal:,.2f}"],
    ]
    if discount_amount > 0:
        totals_data.append(
            ["", f"Discount ({discount_pct}%):", f"- ₹ {discount_amount:,.2f}"]
        )
    if gst_amount > 0:
        totals_data.append(["", "GST:", f"₹ {gst_amount:,.2f}"])

    totals_data.append(["", "Grand Total:", f"₹ {grand_total:,.2f}"])
    totals_data.append(["", "Paid:", f"₹ {paid_amount:,.2f}"])
    if due_amount > 0:
        totals_data.append(["", "Due:", f"₹ {due_amount:,.2f}"])

    totals_table = Table(totals_data, colWidths=[255, 100, 100])
    totals_table.setStyle(TableStyle([
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("ALIGN", (2, 0), (2, -1), "RIGHT"),
        ("FONTNAME", (1, -1 if due_amount <= 0 else -2),
         (2, -1 if due_amount <= 0 else -2), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("LINEABOVE", (1, -1 if due_amount <= 0 else -2),
         (2, -1 if due_amount <= 0 else -2), 1, colors.HexColor("#0f3460")),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    elements.append(totals_table)
    elements.append(Spacer(1, 4 * mm))

    # ---- Payment Mode ----
    payment_mode = sale_data.get("payment_mode", "Cash")
    status = sale_data.get("status", "Completed")
    elements.append(Paragraph(
        f"<b>Payment Mode:</b> {payment_mode} | <b>Status:</b> {status}",
        styles["SmallText"],
    ))
    elements.append(Spacer(1, 8 * mm))

    # ---- Footer ----
    elements.append(HRFlowable(
        width="100%", thickness=0.5, color=colors.HexColor("#cccccc"),
    ))
    elements.append(Spacer(1, 2 * mm))
    elements.append(Paragraph(
        "Thank you for your purchase! Visit again.",
        ParagraphStyle("Footer", parent=styles["Normal"],
                       alignment=TA_CENTER, fontSize=10,
                       textColor=colors.HexColor("#0f3460")),
    ))
    elements.append(Paragraph(
        "This is a computer-generated invoice.",
        ParagraphStyle("FooterSmall", parent=styles["Normal"],
                       alignment=TA_CENTER, fontSize=7,
                       textColor=colors.HexColor("#999999")),
    ))

    doc.build(elements)
    return filename


def generate_purchase_receipt(purchase_data, items, supplier):
    """Generate a PDF receipt for a purchase order.

    Parameters
    ----------
    purchase_data : dict
    items : list[dict]
    supplier : dict

    Returns
    -------
    str : path to the generated PDF file
    """
    _ensure_reports_dir()
    purchase_number = purchase_data.get("purchase_number", "PUR-0000")
    filename = os.path.join(REPORTS_DIR, f"{purchase_number}.pdf")

    doc = SimpleDocTemplate(
        filename, pagesize=A4,
        rightMargin=15 * mm, leftMargin=15 * mm,
        topMargin=15 * mm, bottomMargin=15 * mm,
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        "PTitle", parent=styles["Title"],
        fontSize=18, textColor=colors.HexColor("#1a1a2e"),
        spaceAfter=2,
    ))
    styles.add(ParagraphStyle(
        "PSubtitle", parent=styles["Normal"],
        fontSize=9, textColor=colors.HexColor("#555555"),
        alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        "PSection", parent=styles["Heading3"],
        fontSize=11, textColor=colors.HexColor("#0f3460"),
        spaceBefore=10, spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        "PRight", parent=styles["Normal"],
        alignment=TA_RIGHT, fontSize=9,
    ))
    styles.add(ParagraphStyle(
        "PSmall", parent=styles["Normal"],
        fontSize=9, textColor=colors.HexColor("#333333"),
    ))

    elements = []

    # Header
    elements.append(Paragraph(STORE_NAME, styles["PTitle"]))
    elements.append(Paragraph(STORE_ADDRESS, styles["PSubtitle"]))
    elements.append(Paragraph(
        f"Phone: {STORE_PHONE} | GSTIN: {STORE_GSTIN}", styles["PSubtitle"]
    ))
    elements.append(Spacer(1, 3 * mm))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#0f3460")))
    elements.append(Spacer(1, 3 * mm))
    elements.append(Paragraph("PURCHASE RECEIPT", ParagraphStyle(
        "PReceiptTitle", parent=styles["Title"],
        fontSize=14, textColor=colors.HexColor("#e94560"),
        alignment=TA_CENTER,
    )))
    elements.append(Spacer(1, 3 * mm))

    # Purchase info
    purchase_date = purchase_data.get("purchase_date", datetime.now())
    if isinstance(purchase_date, str):
        purchase_date = datetime.strptime(purchase_date, "%Y-%m-%d %H:%M:%S")

    info_data = [[
        Paragraph(f"<b>Purchase No:</b> {purchase_number}", styles["PSmall"]),
        Paragraph(
            f"<b>Date:</b> {purchase_date.strftime('%d-%b-%Y') if isinstance(purchase_date, datetime) else str(purchase_date)}",
            styles["PRight"],
        ),
    ]]
    info_table = Table(info_data, colWidths=["50%", "50%"])
    info_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    elements.append(info_table)
    elements.append(Spacer(1, 3 * mm))

    # Supplier info
    elements.append(Paragraph("Supplier:", styles["PSection"]))
    elements.append(Paragraph(f"<b>{supplier.get('supplier_name', 'N/A')}</b>", styles["PSmall"]))
    if supplier.get("phone"):
        elements.append(Paragraph(f"Phone: {supplier['phone']}", styles["PSmall"]))
    if supplier.get("gst_number"):
        elements.append(Paragraph(f"GSTIN: {supplier['gst_number']}", styles["PSmall"]))
    elements.append(Spacer(1, 4 * mm))

    # Items table
    table_data = [["S.No", "Product", "Qty", "Unit", "Rate (₹)", "Amount (₹)"]]
    for i, item in enumerate(items, 1):
        table_data.append([
            str(i),
            str(item.get("product_name", "")),
            str(item.get("quantity", 0)),
            str(item.get("unit", "Pcs")),
            f"{float(item.get('purchase_price', 0)):,.2f}",
            f"{float(item.get('amount', 0)):,.2f}",
        ])

    item_table = Table(table_data, colWidths=[30, 180, 45, 40, 75, 85], repeatRows=1)
    item_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f3460")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (2, 0), (-1, -1), "CENTER"),
        ("ALIGN", (-2, 1), (-1, -1), "RIGHT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8f8ff"), colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(item_table)
    elements.append(Spacer(1, 4 * mm))

    # Totals
    subtotal = float(purchase_data.get("subtotal", 0))
    discount = float(purchase_data.get("discount", 0))
    grand_total = float(purchase_data.get("grand_total", 0))

    totals_data = [["", "Subtotal:", f"₹ {subtotal:,.2f}"]]
    if discount > 0:
        totals_data.append(["", "Discount:", f"- ₹ {discount:,.2f}"])
    totals_data.append(["", "Grand Total:", f"₹ {grand_total:,.2f}"])

    totals_table = Table(totals_data, colWidths=[255, 100, 100])
    totals_table.setStyle(TableStyle([
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("FONTNAME", (1, -1), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("LINEABOVE", (1, -1), (2, -1), 1, colors.HexColor("#0f3460")),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    elements.append(totals_table)
    elements.append(Spacer(1, 8 * mm))

    # Footer
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc")))
    elements.append(Spacer(1, 2 * mm))
    elements.append(Paragraph(
        "This is a computer-generated purchase receipt.",
        ParagraphStyle("PFooter", parent=styles["Normal"],
                       alignment=TA_CENTER, fontSize=7,
                       textColor=colors.HexColor("#999999")),
    ))

    doc.build(elements)
    return filename
