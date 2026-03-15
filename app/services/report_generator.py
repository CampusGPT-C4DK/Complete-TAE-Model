from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import uuid

def generate_report(student_name, score, feedback):

    filename = f"reports/report_{uuid.uuid4()}.pdf"

    c = canvas.Canvas(filename, pagesize=letter)

    c.drawString(100, 700, "Assignment Evaluation Report")
    c.drawString(100, 650, f"Student: {student_name}")
    c.drawString(100, 620, f"Score: {score}/10")
    c.drawString(100, 590, f"Feedback: {feedback}")

    c.save()

    return filename