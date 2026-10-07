import os
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.pdfgen import canvas

def generate_certificate_pdf(
    file_path: str,
    recipient_name: str,
    event_name: str,
    issue_date: str,
    issuer_name: str,
    issuer_title: str = "Authorized Signatory",
    custom_message: str = None,
    certificate_code: str = ""
):
    """
    Renders an elegant, professional landscape PDF certificate using ReportLab canvas.
    Dimensions: 11 x 8.5 inches (792 x 612 pt).
    """
    width, height = landscape(letter)  # 792 x 612
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    c = canvas.Canvas(file_path, pagesize=landscape(letter))
    
    # 1. Background fill (soft warm off-white / parchment feel)
    c.setFillColor(colors.HexColor("#FDFCF7"))
    c.rect(0, 0, width, height, fill=1, stroke=0)

    # 2. Decorative Double Outer Border
    # Outer navy border
    c.setStrokeColor(colors.HexColor("#1A365D"))  # Deep Classic Navy
    c.setLineWidth(4)
    c.rect(24, 24, width - 48, height - 48)

    # Inner warm gold border
    c.setStrokeColor(colors.HexColor("#C5A059"))  # Elegant Antique Gold
    c.setLineWidth(1.5)
    c.rect(32, 32, width - 64, height - 64)

    # Corner accents (subtle gold bracket accents)
    gold_color = colors.HexColor("#C5A059")
    c.setStrokeColor(gold_color)
    c.setLineWidth(2)
    # Top-left corner
    c.line(40, height - 40, 65, height - 40)
    c.line(40, height - 40, 40, height - 65)
    # Top-right corner
    c.line(width - 40, height - 40, width - 65, height - 40)
    c.line(width - 40, height - 40, width - 40, height - 65)
    # Bottom-left corner
    c.line(40, 40, 65, 40)
    c.line(40, 40, 40, 65)
    # Bottom-right corner
    c.line(width - 40, 40, width - 65, 40)
    c.line(width - 40, 40, width - 40, 65)

    # 3. Header / Organization title watermark / badge style
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(colors.HexColor("#C5A059"))
    c.drawCentredString(width / 2.0, height - 85, "★ ★ ★   OFFICIAL CERTIFICATION OF ACHIEVEMENT   ★ ★ ★")

    # 4. Main Certificate Heading
    c.setFont("Helvetica-Bold", 32)
    c.setFillColor(colors.HexColor("#1A365D"))
    c.drawCentredString(width / 2.0, height - 130, "CERTIFICATE OF COMPLETION")

    # Decorative divider under title
    c.setStrokeColor(colors.HexColor("#C5A059"))
    c.setLineWidth(1)
    c.line(width / 2.0 - 150, height - 145, width / 2.0 + 150, height - 145)

    # 5. "This is proudly presented to"
    c.setFont("Helvetica-Oblique", 14)
    c.setFillColor(colors.HexColor("#4A5568"))
    c.drawCentredString(width / 2.0, height - 185, "This is proudly presented to")

    # 6. Recipient Name
    c.setFont("Helvetica-Bold", 28)
    c.setFillColor(colors.HexColor("#0F172A"))
    c.drawCentredString(width / 2.0, height - 230, recipient_name)

    # Underline under recipient name
    name_width = min(c.stringWidth(recipient_name, "Helvetica-Bold", 28) + 40, 450)
    c.setStrokeColor(colors.HexColor("#CBD5E1"))
    c.setLineWidth(1)
    c.line(width / 2.0 - (name_width / 2.0), height - 240, width / 2.0 + (name_width / 2.0), height - 240)

    # 7. Achievement statement
    default_msg = f"for outstanding participation and successful completion of"
    msg = custom_message if custom_message else default_msg
    c.setFont("Helvetica", 13)
    c.setFillColor(colors.HexColor("#4A5568"))
    c.drawCentredString(width / 2.0, height - 275, msg)

    # 8. Event / Course Name
    c.setFont("Helvetica-Bold", 22)
    c.setFillColor(colors.HexColor("#1A365D"))
    c.drawCentredString(width / 2.0, height - 315, event_name)

    # 9. Signatures and Date Section
    bottom_y = 120

    # Date Block (Left)
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(colors.HexColor("#1E293B"))
    c.drawCentredString(180, bottom_y + 35, issue_date)
    c.setStrokeColor(colors.HexColor("#94A3B8"))
    c.setLineWidth(1)
    c.line(100, bottom_y + 25, 260, bottom_y + 25)
    c.setFont("Helvetica", 11)
    c.setFillColor(colors.HexColor("#64748B"))
    c.drawCentredString(180, bottom_y + 10, "Date of Issue")

    # Issuer / Signature Block (Right)
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(colors.HexColor("#1E293B"))
    c.drawCentredString(width - 180, bottom_y + 35, issuer_name)
    c.setStrokeColor(colors.HexColor("#94A3B8"))
    c.setLineWidth(1)
    c.line(width - 260, bottom_y + 25, width - 100, bottom_y + 25)
    c.setFont("Helvetica", 11)
    c.setFillColor(colors.HexColor("#64748B"))
    c.drawCentredString(width - 180, bottom_y + 10, issuer_title or "Authorized Signatory")

    # 10. Verification Code & Footer (Center Bottom)
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.HexColor("#94A3B8"))
    if certificate_code:
        c.drawCentredString(width / 2.0, 52, f"Verification ID: {certificate_code}")
    c.drawCentredString(width / 2.0, 40, "Verified Digital Certificate • Issued via Bulk Certificate Generator")

    c.showPage()
    c.save()
    return file_path
