#!/usr/bin/env python
"""Create a sample invoice PDF for testing InvoiceFlow AI"""
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors

def create_sample_invoice():
    doc = SimpleDocTemplate("sample_invoice.pdf", pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    # Title
    elements.append(Paragraph("INVOICE", styles['Title']))
    elements.append(Spacer(1, 12))

    # Header info
    header_data = [
        ["Invoice #: INV-2024-001245", "Date: July 10, 2024"],
        ["", "Due Date: July 25, 2024"],
    ]
    header_table = Table(header_data, colWidths=[3*inch, 3*inch])
    header_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 1), (1, 1), colors.blue),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 24))

    # Bill To
    elements.append(Paragraph("<b>Bill To:</b>", styles['Normal']))
    elements.append(Paragraph("TechVest Corporation<br/>123 Business Park, Suite 500<br/>New York, NY 10001", styles['Normal']))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("<b>Vendor:</b>", styles['Normal']))
    elements.append(Paragraph("Global Tech Solutions<br/>123 Technology Drive<br/>San Francisco, CA 94105", styles['Normal']))
    elements.append(Spacer(1, 24))

    # Items table
    elements.append(Paragraph("<b>ITEMS:</b>", styles['Heading2']))
    elements.append(Spacer(1, 12))

    items_data = [
        ["Item", "Qty", "Unit Price", "Amount"],
        ["Software License", "10", "$1,500.00", "$15,000.00"],
        ["Consulting Hours", "25", "$200.00", "$5,000.00"],
        ["Support Package", "1", "$2,500.00", "$2,500.00"],
    ]
    items_table = Table(items_data, colWidths=[3*inch, 0.8*inch, 1*inch, 1*inch])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 24))

    # Totals
    totals_data = [
        ["", "", "Subtotal:", "$22,500.00"],
        ["", "", "Tax (8.5%):", "$1,912.50"],
        ["", "", "Shipping:", "$150.00"],
        ["", "", "Total Amount:", "$24,562.50"],
    ]
    totals_table = Table(totals_data, colWidths=[3*inch, 0.8*inch, 1*inch, 1*inch])
    totals_table.setStyle(TableStyle([
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica'),
        ('FONTNAME', (3, 0), (3, -1), 'Helvetica-Bold'),
        ('LINEABOVE', (2, -1), (3, -1), 2, colors.black),
        ('ALIGN', (2, 0), (3, -1), 'RIGHT'),
    ]))
    elements.append(totals_table)
    elements.append(Spacer(1, 24))

    # Footer info
    elements.append(Paragraph("<b>Payment Terms:</b> Net 15", styles['Normal']))
    elements.append(Paragraph("<b>GST Number:</b> 27AABCG1234F1Z5", styles['Normal']))
    elements.append(Paragraph("<b>PO Reference:</b> PO-2024-7890", styles['Normal']))
    elements.append(Paragraph("<b>Notes:</b> Annual software subscription renewal with premium support.", styles['Normal']))

    doc.build(elements)
    print("Created sample_invoice.pdf")

if __name__ == "__main__":
    create_sample_invoice()