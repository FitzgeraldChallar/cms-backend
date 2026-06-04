import os
import sys
import math
from io import BytesIO
from datetime import datetime, timedelta
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Image
from reportlab.graphics import renderPDF
from reportlab.graphics.shapes import Drawing, Circle, String, Wedge, Rect, Group, Polygon
from reportlab.lib.colors import blue, lightblue, white, navy, HexColor
from django.conf import settings
from django.core.files.base import ContentFile
from django.db.models import Max
from PyPDF2 import PdfReader, PdfWriter
from PIL import Image as PILImage

def generate_certificate(obj):
    """
    Generate a complete certificate PDF from scratch with all elements
    
    Args:
        obj: CertificateApplication object containing the necessary data
        
    Returns:
        None - saves the generated certificate to the object's generated_certificate field
    """
    from .models import CertificateApplication
    
    # === Generate certificate number if missing ===
    if not obj.certificate_number:
        if not obj.id:
            obj.save()  # Ensure the object is saved and has an ID
        obj.certificate_number = f"NWASHC-{obj.id:04d}"
        obj.save()

    # Extract values
    partner_name = obj.partner if obj.partner else "Unknown Partner"
    certificate_number = obj.certificate_number
    tin_number = obj.tin_number or "N/A"
    date_issued = datetime.today().date()
    date_expiry = date_issued + timedelta(days=365)
    
    # Create buffer for the PDF
    buffer = BytesIO()
    
    # Create PDF with landscape orientation
    pagesize = landscape(A4)
    c = canvas.Canvas(buffer, pagesize=pagesize)
    width, height = pagesize
    
    # Set up the background with a white color
    c.setFillColorRGB(1, 1, 1)  # white
    c.rect(0, 0, width, height, fill=1)
    
    # Get paths to logo and seal images
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'wash_logo.png')
    seal_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'lib_seal.png')
    
    
   # === Stylish outer decorative border with layered slope effect ===
    outer_x = 0.6 * inch
    outer_y = 0.6 * inch
    outer_w = width - 1.2 * inch
    outer_h = height - 1.2 * inch

   # Primary border fill
    c.setFillColorRGB(0.12, 0.56, 1.0)  # Dodger Blue
    c.setStrokeColorRGB(0.0, 0.2, 0.4)  # Darker Blue
    c.setLineWidth(2)
    c.roundRect(outer_x, outer_y, outer_w, outer_h, radius=20, fill=1, stroke=1)

   # Secondary inner accent stroke (sloped illusion)
    c.setLineWidth(1)
    c.setStrokeColorRGB(1, 1, 1)  # White accent line for style
    c.roundRect(outer_x + 4, outer_y + 4, outer_w - 8, outer_h - 8, radius=18, fill=0, stroke=1)

   # Optional: add sloped corner notches (decorative style)
    c.setStrokeColorRGB(0.0, 0.2, 0.4)
    notch_len = 20
    c.setLineWidth(1)
   # Top-left notch
    c.line(outer_x, outer_y + outer_h, outer_x + notch_len, outer_y + outer_h)
    c.line(outer_x, outer_y + outer_h, outer_x, outer_y + outer_h - notch_len)
   # Top-right notch
    c.line(outer_x + outer_w, outer_y + outer_h, outer_x + outer_w - notch_len, outer_y + outer_h)
    c.line(outer_x + outer_w, outer_y + outer_h, outer_x + outer_w, outer_y + outer_h - notch_len)
   # Bottom-left notch
    c.line(outer_x, outer_y, outer_x + notch_len, outer_y)
    c.line(outer_x, outer_y, outer_x, outer_y + notch_len)
   # Bottom-right notch
    c.line(outer_x + outer_w, outer_y, outer_x + outer_w - notch_len, outer_y)
    c.line(outer_x + outer_w, outer_y, outer_x + outer_w, outer_y + notch_len)

    
    # Add inner white area for content
    c.setFillColorRGB(0.68, 0.85, 1.0)  # light dodger blue 
    c.rect(1.0*inch, 1.0*inch, width-2.0*inch, height-2.0*inch, fill=1)
    

    c.setFont("Helvetica-Bold", 18)
    c.setFillColorRGB(0.8, 0.1, 0.1)
    c.drawCentredString(width/2, height-1.6*inch, "REPUBLIC OF LIBERIA")
    
    # Add header text
    c.setFont("Helvetica-Bold", 16)
    c.setFillColorRGB(0.12, 0.56, 1.0)  # dodger blue text
    c.drawCentredString(width/2, height-2.2*inch, "NATIONAL WATER, SANITATION & HYGIENE COMMISSION")
    
    # Add certificate title
    c.setFont("Helvetica-Bold", 24)
    c.setFillColorRGB(0.12, 0.56, 1.0)  # dodger blue text
    c.drawCentredString(width/2, height-2.7*inch, "NWASHC")
    
    # Add logo and seal
    try:
        # Add the logo to top right corner if file exists
        if os.path.exists(logo_path):
            logo_width = 1.0*inch
            logo_height = 1.0*inch
            c.drawImage(logo_path, width-1.1*inch-logo_width, height-1.1*inch-logo_height,
                        width=logo_width, height=logo_height, mask='auto')
        else:
            # Fallback if image not found
            c.setFillColorRGB(0.1, 0.2, 0.5)  # Navy blue
            c.circle(width-2*inch, height-1.5*inch, 0.75*inch, fill=0)
            c.setFont("Helvetica", 8)
            c.drawCentredString(width-2*inch, height-1.5*inch, "COMMISSION LOGO")
        
        # Add the seal to top left corner if file exists
        if os.path.exists(seal_path):
            seal_width = 1.0*inch
            seal_height = 1.0*inch
            c.drawImage(seal_path, 1.1*inch, height-1.1*inch-seal_height, 
                        width=seal_width, height=seal_height, mask='auto')
        else:
            # Fallback if image not found
            c.setFillColorRGB(0.1, 0.2, 0.5)  # Navy blue
            c.circle(2*inch, height-1.5*inch, 0.75*inch, fill=0)
            c.setFont("Helvetica", 8)
            c.drawCentredString(2*inch, height-1.5*inch, "LIBERIA SEAL")
    except Exception as e:
        print(f"Error adding images: {e}")
        # Fallback
        c.setFillColorRGB(0.1, 0.2, 0.5)  # Navy blue
        c.circle(2*inch, height-1.5*inch, 0.75*inch, fill=0)
        c.circle(width-2*inch, height-1.5*inch, 0.75*inch, fill=0)
    
    # Certificate Number box - Left side
    cert_box_x = 1.8 * inch
    cert_box_y = height - 3.2 * inch
    cert_box_width = 2.5 * inch
    cert_box_height = 0.4 * inch
    cert_center_x = cert_box_x + cert_box_width / 2
    cert_text_y = cert_box_y + 0.13 * inch

    c.setFillColorRGB(0.95, 0.97, 1.0)  # Light blue background
    c.setStrokeColorRGB(0.1, 0.2, 0.5)  # Navy blue border
    c.roundRect(cert_box_x, cert_box_y, cert_box_width, cert_box_height, 5, fill=1)

    c.setFont("Helvetica", 10)
    c.setFillColorRGB(0.8, 0.1, 0.1)  # red text
    c.drawCentredString(cert_center_x, cert_text_y + 10, "Certificate No.")

    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(cert_center_x, cert_text_y - 2, certificate_number)

    # TIN Number box - Right side
    tin_box_x = width - 4.3 * inch
    tin_box_y = height - 3.2 * inch
    tin_box_width = 2.5 * inch
    tin_box_height = 0.4 * inch
    tin_center_x = tin_box_x + tin_box_width / 2
    tin_text_y = tin_box_y + 0.13 * inch

    c.setFillColorRGB(0.95, 0.97, 1.0)  # Light blue background
    c.setStrokeColorRGB(0.1, 0.2, 0.5)
    c.roundRect(tin_box_x, tin_box_y, tin_box_width, tin_box_height, 5, fill=1)

    c.setFont("Helvetica", 10)
    c.setFillColorRGB(0.8, 0.1, 0.1)  # red text
    c.drawCentredString(tin_center_x, tin_text_y + 10, "TIN:")

    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(tin_center_x, tin_text_y - 2, tin_number)

    
    # Main certificate text
    c.setFont("Helvetica-Oblique", 16)
    c.setFillColorRGB(0, 0, 0)  #black text
    c.drawCentredString(width/2, height/2+1*inch, "This is to certify that")
    
    # Partner name
    partner_font_size = 20 
    if len(partner_name) > 25:
        partner_font_size = 18
    if len(partner_name) > 40:
        partner_font_size = 16
    if len(partner_name) > 60:
        partner_font_size = 14
    c.setFont("Helvetica-Bold", partner_font_size)
    c.drawCentredString(width/2, height/2+0.6*inch, partner_name)
    
    # Compliance text
    c.setFont("Helvetica", 14)
    c.drawCentredString(width/2, height/2+0.2*inch, "Has met all requirements of the National WASH Commission and is hereby granted this")
    # Set text and styling
    text = "WASH COMPLIANCE CERTIFICATE"
    font = "Courier-Bold"
    font_size = 14
    c.setFont(font, font_size)

    # Calculate text dimensions
    text_width = c.stringWidth(text, font, font_size)
    padding_x = 12  # horizontal padding
    padding_y = 6   # vertical padding

    # Position — slightly lowered to create space
    center_x = width / 2
    center_y = height / 2 - 0.25 * inch  # ← shifted from -0.1 to -0.25 inch

    rect_width = text_width + 2 * padding_x
    rect_height = font_size + 2 * padding_y
    rect_x = center_x - rect_width / 2
    rect_y = center_y - rect_height / 2

    # Draw rounded rectangle background
    c.setFillColor(colors.white)
    c.setStrokeColorRGB(0.12, 0.56, 1.0)  # Dodger Blue
    c.setLineWidth(2.5)
    c.roundRect(rect_x, rect_y, rect_width, rect_height, radius=10, fill=1, stroke=1)

    # Draw the text centered inside the rounded rectangle
    c.setFillColor(colors.black)
    c.drawCentredString(center_x, center_y - 0.25 * font_size, text)
    
    # Combine both labels and dates into one line and center it
    c.setFont("Helvetica", 12)

    # Prepare text segments
    label1 = "This certificate is valid until: "
    label2 = "Date of Issue: "
    expiry_text = date_expiry.strftime("%B %d, %Y")
    issued_text = date_issued.strftime("%B %d, %Y")

    # Set font for measurement
    font_name = "Helvetica"
    bold_font = "Helvetica-Bold"
    font_size = 12
    c.setFont(font_name, font_size)

    # Measure total width of line
    total_text = f"{label1} {expiry_text}     {label2} {issued_text}"
    label1_width = c.stringWidth(label1, font_name, font_size)
    expiry_width = c.stringWidth(expiry_text, bold_font, font_size)
    label2_width = c.stringWidth(label2, font_name, font_size)
    issued_width = c.stringWidth(issued_text, bold_font, font_size)
    gap = c.stringWidth("     ", font_name, font_size)
    total_width = label1_width + expiry_width + gap + label2_width + issued_width

    # Starting X to center entire line
    x_start = (width - total_width) / 2
    y_pos = height/2 - 0.9*inch

    # Draw texts
    x = x_start
    c.setFont(font_name, font_size)
    c.drawString(x, y_pos, label1)
    x += label1_width

    c.setFont(bold_font, font_size)
    c.drawString(x, y_pos, expiry_text)
    c.setStrokeColorRGB(0, 0, 0)  # Set underline to black
    c.line(x, y_pos - 1, x + expiry_width, y_pos - 1)
    x += expiry_width + gap

    c.setFont(font_name, font_size)
    c.drawString(x, y_pos, label2)
    x += label2_width

    c.setFont(bold_font, font_size)
    c.drawString(x, y_pos, issued_text)
    c.setStrokeColorRGB(0, 0, 0)  # Set underline to black
    c.line(x, y_pos - 1, x + issued_width, y_pos - 1)

    #add compliance notice text
    c.setFont("Helvetica-Oblique", 11)
    c.setFillColorRGB(0, 0, 0)
    c.drawCentredString(width/2, height/2-1.7*inch, "This certificate is subject to revocation failure to maintain compliance")
    
    # Signature lines
    c.setStrokeColorRGB(0, 0, 0)#black
    c.line(2.5*inch, 2*inch, 4.5*inch, 2*inch)
    c.line(width-4.5*inch, 2*inch, width-2.5*inch, 2*inch)
    
    # Signature titles
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(3.5*inch, 1.8*inch, "Morris G. Gono, Jr.")
    c.drawCentredString(3.5*inch, 1.6*inch, "Executive Director")
    
    c.drawCentredString(width-3.5*inch, 1.8*inch, "George W. K. Yarngo")
    c.drawCentredString(width-3.5*inch, 1.6*inch, "Chief Executive Officer")

    # Watermark: Tiled logos within content area only
    try:
        if logo_path and os.path.exists(logo_path):
           c.saveState()
           c.setFillAlpha(0.09)  # Adjust opacity for watermark visibility

           # Open the logo
           img = PILImage.open(logo_path)
           img_width, img_height = img.size
           aspect = img_height / float(img_width)

          # Content area boundaries (inside the outer border)
           content_x = 1.0 * inch
           content_y = 1.0 * inch
           content_width = width - 2.0 * inch
           content_height = height - 2.0 * inch

          # Watermark size (smaller = more dense)
           wm_width = content_width / 12
           wm_height = wm_width * aspect

          # Adjust step to tile diagonally (slightly overlapped to avoid gaps)
           step_x = wm_width * 0.8
           step_y = wm_height * 0.8

          # Start from the bottom-left corner and go up diagonally
           x = content_x  # Start exactly at the left edge of the content area
           while x < content_x + content_width:
               y = content_y
               while y < content_y + content_height:
                  c.saveState()
                  c.translate(x + wm_width / 2, y + wm_height / 2)
                  c.rotate(45)
                  c.drawImage(logo_path, -wm_width/2, -wm_height/2, width=wm_width, height=wm_height, mask='auto')
                  c.restoreState()
                  y += step_y
               x += step_x
           c.restoreState()
           
        else:
           # fallback watermark
           c.saveState()
           c.setFillColorRGB(0.8, 0.8, 0.9, 0.1)
           c.setFont("Helvetica-Bold", 60)
           c.translate(width/2, height/2)
           c.rotate(45)
           c.drawCentredString(0, 0, "NATIONAL WASH COMMISSION") 
           c.restoreState()
    except Exception as e:
       print(f"Error rendering watermark: {e}")


    # Add decorative background pattern
    c.saveState()
    c.setStrokeColorRGB(0.8, 0.85, 0.95, 0.3)  # light blue
    c.setLineWidth(0.7)

    #Create a subtle grid pattern
    spacing = 25
    for i in range(0, int(width), spacing):
        c.line(i, 0, i, height)
    for i in range(0, int(height), spacing):
        c.line(0, i, width, i)
    c.restoreState()
 
    # Save the PDF
    c.save()
    buffer.seek(0)
    
    # Save to the object's field
    filename = f"certificate_{obj.id}.pdf"
    obj.generated_certificate.save(filename, ContentFile(buffer.read()))
    obj.save()

def debug_certificate_layout(template_path, output_path):
    """
    Helper function to visualize coordinate grid on the certificate template
    
    Args:
        template_path: Path to the certificate template PDF
        output_path: Path where to save the debug output PDF
        
    Returns:
        None - saves a debug PDF with coordinate grid
    """
    packet = BytesIO()
    pagesize = landscape(A4)
    p = canvas.Canvas(packet, pagesize=pagesize)
    width, height = pagesize
    
    # Draw a grid with 50-unit spacing
    p.setStrokeColorRGB(0.7, 0.7, 0.7)  # Light gray
    p.setFont("Helvetica", 8)
    
    # Vertical lines
    for x in range(0, int(width), 50):
        p.line(x, 0, x, height)
        # Label every 100 units
        if x % 100 == 0:
            for y in range(50, int(height), 100):
                p.drawString(x + 5, y, f"x={x}")
    
    # Horizontal lines
    for y in range(0, int(height), 50):
        p.line(0, y, width, y)
        # Label every 100 units
        if y % 100 == 0:
            for x in range(50, int(width), 100):
                p.drawString(x, y - 10, f"y={y}")
    
    # Sample position markers for key elements
    p.setFillColorRGB(1, 0, 0)  # Red
    
    # Certificate Number (adjusted for landscape)
    p.circle(220, height-210, 5)
    p.drawString(230, height-210, "Cert #")
    
    # TIN (adjusted for landscape)
    p.circle(width-350, height-210, 5)
    p.drawString(width-340, height-210, "TIN")
    
    # Partner Name (adjusted for landscape) 
    p.circle(width/2, height/2+40, 5)
    p.drawString(width/2 + 10, height/2+40, "Partner")
    
    # Expiry Date (adjusted for landscape)
    p.circle(width/2+50, height/2-50, 5)
    p.drawString(width/2+60, height/2-50, "Expiry")
    
    # Issue Date (adjusted for landscape)
    p.circle(width/2-100, height/2-80, 5)
    p.drawString(width/2-90, height/2-80, "Issue Date")
    
    p.save()
    packet.seek(0)
    
    # Merge with template
    background = PdfReader(open(template_path, "rb"))
    overlay = PdfReader(packet)
    output = PdfWriter()
    
    base_page = background.pages[0]
    base_page.merge_page(overlay.pages[0])
    output.add_page(base_page)
    
    # Save debug file
    with open(output_path, "wb") as f:
        output.write(f)
    
    print(f"Debug layout saved to {output_path}")