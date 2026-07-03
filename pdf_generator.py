
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime


def generate_pdf(filename, ats, similarity, matched, missing, suggestions):
    pdf_name = "resume_report.pdf"

    doc = SimpleDocTemplate(pdf_name)
    styles = getSampleStyleSheet()
    elements = []

    title = Paragraph("AI Resume Analyzer Report", styles["Title"])
    elements.append(title)
    elements.append(Spacer(1, 20))

    elements.append(Paragraph(f"Resume File: {filename}", styles["Normal"]))
    elements.append(Paragraph(f"Generated On: {datetime.now().strftime('%d %b %Y, %I:%M %p')}", styles["Normal"]))
    elements.append(Spacer(1, 20))

    elements.append(Paragraph(f"ATS Score: {ats}%", styles["Heading2"]))
    elements.append(Paragraph(f"Similarity Score: {similarity}%", styles["Heading2"]))
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("Matched Skills:", styles["Heading2"]))
    for skill in matched:
        elements.append(Paragraph(f"• {skill}", styles["Normal"]))
    elements.append(Spacer(1, 15))

    elements.append(Paragraph("Missing Skills:", styles["Heading2"]))
    for skill in missing:
        elements.append(Paragraph(f"• {skill}", styles["Normal"]))
    elements.append(Spacer(1, 15))

    elements.append(Paragraph("Suggestions:", styles["Heading2"]))
    for suggestion in suggestions:
        elements.append(Paragraph(f"• {suggestion}", styles["Normal"]))

    doc.build(elements)

    return pdf_name

