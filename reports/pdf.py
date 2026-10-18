from io import BytesIO

from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def build_offering_pdf(offering, rows, threshold=None):
    """Return the bytes of a PDF attendance report for one offering."""
    if threshold is None:
        threshold = getattr(settings, "ATTENDANCE_THRESHOLD", 60)

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )
    styles = getSampleStyleSheet()

    title = f"{offering.subject.code} - {offering.subject.name}"
    subtitle = (
        f"{offering.session.name} · Semester {offering.semester} · "
        f"Section {offering.section or '-'} · Threshold {threshold}%"
    )

    elements = [
        Paragraph(title, styles["Title"]),
        Paragraph(subtitle, styles["Normal"]),
        Spacer(1, 0.5 * cm),
    ]

    data = [["Roll", "Name", "Present", "Late", "Absent", "Excused", "Attended", "Total", "%"]]
    for row in rows:
        name = row["student"].user.get_full_name() or row["student"].user.username
        data.append(
            [
                row["student"].roll_no,
                name,
                row["present"],
                row["late"],
                row["absent"],
                row["excused"],
                row["attended"],
                row["total"],
                "—" if row["percentage"] is None else f'{row["percentage"]}%',
            ]
        )

    table = Table(data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4338ca")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f9")]),
                ("ALIGN", (2, 1), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )

    for index, row in enumerate(rows, start=1):
        if row["below_threshold"]:
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, index), (-1, index), colors.HexColor("#fee2e2")),
                        ("TEXTCOLOR", (0, index), (-1, index), colors.HexColor("#991b1b")),
                    ]
                )
            )

    elements.append(table)
    doc.build(elements)
    return buffer.getvalue()
