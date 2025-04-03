import io
from datetime import datetime
from reportlab.pdfgen import canvas

class PDFGenerator:
    def __init__(self):
        pass  # Retirer cette ligne si inutile

    @staticmethod
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
