import qrcode
import io
import base64
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from datetime import datetime

def generate_qr_code(data):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64 for display
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def generate_pdf_report(data, report_type):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)
    
    # Header
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, 800, f"Rapport - {report_type}")
    p.setFont("Helvetica", 12)
    p.drawString(50, 780, f"Généré le: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    
    # Content
    y_position = 750
    for item in data:
        p.drawString(50, y_position, str(item))
        y_position -= 20
        
    p.save()
    buffer.seek(0)
    return buffer

def format_datetime(dt):
    return dt.strftime("%d/%m/%Y %H:%M")

def validate_email(email):
    import re
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None
