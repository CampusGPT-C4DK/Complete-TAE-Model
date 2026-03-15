import os
import uuid

from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle,
    Paragraph, Frame, PageTemplate
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


# ⭐ Register Times New Roman Fonts
pdfmetrics.registerFont(TTFont('Times', 'times.ttf'))
pdfmetrics.registerFont(TTFont('Times-Bold', 'timesbd.ttf'))


HEADER_HEIGHT = 120
FOOTER_HEIGHT = 100
PAGE_WIDTH = 540


def generate_assignment_pdf(
        questions,
        assignment_no,
        subject,
        branch,
        semester,
        unit,
        faculty,
        given_date,
        submission_date
):

    os.makedirs("assignments", exist_ok=True)

    filename = f"assignments/assignment_{uuid.uuid4()}.pdf"

    normal = ParagraphStyle(
        'normal',
        fontName='Times',
        fontSize=11,
        leading=14
    )

    bold = ParagraphStyle(
        'bold',
        fontName='Times-Bold',
        fontSize=11
    )

    elements = []

    # ⭐ DETAILS TABLE
    details_data = [
        [Paragraph("Assignment No", bold), assignment_no,
         Paragraph("Subject", bold), subject],

        [Paragraph("Branch", bold), branch,
         Paragraph("Semester", bold), semester],

        [Paragraph("Unit", bold), unit,
         Paragraph("Faculty", bold), faculty],

        [Paragraph("Date Given", bold), given_date,
         Paragraph("Submission Date", bold), submission_date]
    ]

    details_table = Table(
        details_data,
        colWidths=[PAGE_WIDTH*0.2, PAGE_WIDTH*0.3,
                   PAGE_WIDTH*0.2, PAGE_WIDTH*0.3]
    )

    details_table.setStyle(TableStyle([

        ('GRID', (0,0), (-1,-1), 1, colors.black),

        ('BACKGROUND', (0,0), (0,-1), colors.lavender),
        ('BACKGROUND', (2,0), (2,-1), colors.lavender),

        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),

        ('LEFTPADDING',(0,0),(-1,-1),6),
        ('RIGHTPADDING',(0,0),(-1,-1),6),
        ('TOPPADDING',(0,0),(-1,-1),6),
        ('BOTTOMPADDING',(0,0),(-1,-1),6),
    ]))

    elements.append(details_table)

    elements.append(Table([[""]], colWidths=[PAGE_WIDTH], rowHeights=[20]))

    # ⭐ QUESTIONS TABLE
    question_data = [[
        Paragraph("Q.No", bold),
        Paragraph("Questions", bold),
        Paragraph("CO", bold),
        Paragraph("Marks", bold)
    ]]

    for i, q in enumerate(questions, start=1):

        question_data.append([
            Paragraph(f"Q{i}", normal),
            Paragraph(q["question"], normal),
            Paragraph(q["co"], normal),
            Paragraph(str(q["marks"]), normal)
        ])

    question_table = Table(
        question_data,
        colWidths=[
            PAGE_WIDTH*0.08,
            PAGE_WIDTH*0.62,
            PAGE_WIDTH*0.15,
            PAGE_WIDTH*0.15
        ]
    )

    question_table.setStyle(TableStyle([

        ('GRID', (0,0), (-1,-1), 1, colors.black),

        ('BACKGROUND', (0,0), (-1,0), colors.lavender),

        ('VALIGN', (0,0), (-1,-1), 'TOP'),

        ('LEFTPADDING',(0,0),(-1,-1),6),
        ('RIGHTPADDING',(0,0),(-1,-1),6),
        ('TOPPADDING',(0,0),(-1,-1),8),
        ('BOTTOMPADDING',(0,0),(-1,-1),8),

    ]))

    elements.append(question_table)

    # ⭐ Header + Footer + Assignment Title
    def draw_header_footer(canvas, doc):

        page_width, page_height = letter

        header = ImageReader("assets/header.png")
        footer = ImageReader("assets/footer.png")

        canvas.drawImage(
            header,
            0,
            page_height - HEADER_HEIGHT,
            width=page_width,
            height=HEADER_HEIGHT
        )

        canvas.drawImage(
            footer,
            0,
            0,
            width=page_width,
            height=FOOTER_HEIGHT
        )

        y = page_height - HEADER_HEIGHT - 12

        canvas.setLineWidth(1)
        canvas.line(36, y, page_width-36, y)

        canvas.setFont("Times-Bold", 15)
        canvas.drawCentredString(page_width/2, y-18, "Assignment Sheet")

        canvas.setFont("Times-Bold", 11)
        canvas.drawCentredString(page_width/2, y-34, "(Session: 2023-24)")

        canvas.line(36, y-40, page_width-36, y-40)

    frame = Frame(
        36,
        FOOTER_HEIGHT + 20,
        letter[0] - 72,
        letter[1] - HEADER_HEIGHT - FOOTER_HEIGHT - 90,
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0
    )

    template = PageTemplate(
        id='main',
        frames=[frame],
        onPage=draw_header_footer
    )

    pdf = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=0,
        bottomMargin=0
    )

    pdf.addPageTemplates([template])

    pdf.build(elements)

    return filename