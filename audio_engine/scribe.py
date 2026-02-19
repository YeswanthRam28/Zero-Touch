
import os
import datetime
import logging
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

logger = logging.getLogger(__name__)

class AIScribe:
    def __init__(self, output_dir="operative_notes"):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def generate_report(self, summary_text, event_logs):
        """
        Produce a formatted PDF report of the surgical session.
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"SurgicalNote_{timestamp}.pdf"
        filepath = os.path.join(self.output_dir, filename)

        try:
            doc = SimpleDocTemplate(filepath, pagesize=letter)
            styles = getSampleStyleSheet()
            elements = []

            # Title
            elements.append(Paragraph("Zero-Touch: Surgical Procedure Note", styles['Title']))
            elements.append(Spacer(1, 12))

            # Metadata
            elements.append(Paragraph(f"<b>Session Date:</b> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
            elements.append(Paragraph(f"<b>Assistant Version:</b> 2.0 (Smart Assistant)", styles['Normal']))
            elements.append(Spacer(1, 24))

            # AI Summary
            elements.append(Paragraph("Clinical Summary", styles['Heading2']))
            elements.append(Paragraph(summary_text, styles['Normal']))
            elements.append(Spacer(1, 24))

            # Event Logs Table
            elements.append(Paragraph("Detailed Event Log", styles['Heading2']))
            data = [["Timestamp", "Event Type", "Details"]]
            for event in event_logs:
                # Truncate details if too long for table
                details = str(event.get('details', ''))
                if len(details) > 50:
                    details = details[:47] + "..."
                data.append([event.get('timestamp', ''), event.get('type', ''), details])

            table = Table(data, colWidths=[120, 100, 250])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(table)

            # Build PDF
            doc.build(elements)
            logger.info(f"Surgical report generated: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Failed to generate PDF: {e}")
            return None

if __name__ == "__main__":
    # Test
    scribe = AIScribe()
    scribe.generate_report("The surgeon performed a routine gallbladder removal. Navigation was used to zoom in on the cystic duct.", 
                           [{"timestamp": "12:00", "type": "ZOOM_IN", "details": {"factor": 1.4}}])
