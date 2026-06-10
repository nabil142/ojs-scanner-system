from datetime import datetime
from io import BytesIO


def _clean_text(value):
    text = str(value or "-")
    return text.replace("\r", " ").replace("\n", " ").strip()


def _severity_counts(vulnerabilities):
    counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    for item in vulnerabilities:
        level = str(item.get("level", "Low")).capitalize()
        if level not in counts:
            counts[level] = 0
        counts[level] += 1
    return counts


def generate_scan_pdf(scan_record, vulnerabilities):
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import (
            SimpleDocTemplate,
            Paragraph,
            Spacer,
            Table,
            TableStyle,
            PageBreak,
        )
    except ImportError as exc:
        raise RuntimeError(
            "Library reportlab belum terinstall. Jalankan: pip install reportlab"
        ) from exc

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        title=f"OJS Security Report - {scan_record.id}",
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="SectionTitle",
        parent=styles["Heading2"],
        textColor=colors.HexColor("#1f2937"),
        spaceBefore=12,
        spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        name="SmallText",
        parent=styles["BodyText"],
        fontSize=8,
        leading=10,
    ))

    generated_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    counts = _severity_counts(vulnerabilities)
    total = len(vulnerabilities)

    story = [
        Paragraph("OJS Repository Security Scan Report", styles["Title"]),
        Spacer(1, 10),
        Paragraph("Ringkasan Scan", styles["SectionTitle"]),
        Table(
            [
                ["Target", _clean_text(scan_record.target)],
                ["Tanggal Scan", _clean_text(scan_record.timestamp)],
                ["Sumber Scanner", _clean_text(scan_record.source)],
                ["Report Dibuat", generated_at],
                ["Total Kerentanan", str(total)],
            ],
            colWidths=[4 * cm, 13 * cm],
            style=[
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#e5e7eb")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("PADDING", (0, 0), (-1, -1), 6),
            ],
        ),
        Spacer(1, 10),
        Paragraph("Distribusi Severity", styles["SectionTitle"]),
        Table(
            [
                ["Critical", "High", "Medium", "Low"],
                [
                    str(counts.get("Critical", 0)),
                    str(counts.get("High", 0)),
                    str(counts.get("Medium", 0)),
                    str(counts.get("Low", 0)),
                ],
            ],
            colWidths=[4.25 * cm, 4.25 * cm, 4.25 * cm, 4.25 * cm],
            style=[
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111827")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("PADDING", (0, 0), (-1, -1), 6),
            ],
        ),
    ]

    if not vulnerabilities:
        story.extend([
            Spacer(1, 14),
            Paragraph("Detail Kerentanan", styles["SectionTitle"]),
            Paragraph(
                "Tidak ada kerentanan yang ditemukan pada hasil scan ini.",
                styles["BodyText"],
            ),
        ])
    else:
        story.extend([
            Spacer(1, 14),
            Paragraph("Detail Kerentanan dan Rekomendasi", styles["SectionTitle"]),
        ])

        for index, item in enumerate(vulnerabilities, start=1):
            story.extend([
                Paragraph(f"{index}. {_clean_text(item.get('type'))}", styles["Heading3"]),
                Table(
                    [
                        ["Severity", _clean_text(item.get("level"))],
                        ["Score", _clean_text(item.get("score"))],
                        ["Critical Area", _clean_text(item.get("critical_area"))],
                        ["Priority", _clean_text(item.get("priority"))],
                        ["OWASP", _clean_text(item.get("owasp"))],
                        ["Location", _clean_text(item.get("location") or item.get("file_path"))],
                        ["Line", _clean_text(item.get("line_number") or "-")],
                        ["Source", _clean_text(item.get("source"))],
                    ],
                    colWidths=[4 * cm, 13 * cm],
                    style=[
                        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f3f4f6")),
                        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d1d5db")),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                        ("PADDING", (0, 0), (-1, -1), 5),
                    ],
                ),
                Spacer(1, 5),
                Paragraph("<b>Alasan Risiko:</b>", styles["BodyText"]),
                Paragraph(_clean_text(item.get("severity_reason") or item.get("description")), styles["SmallText"]),
                Spacer(1, 5),
                Paragraph("<b>Kode/Indikator:</b>", styles["BodyText"]),
                Paragraph(_clean_text(item.get("code_snippet") or item.get("vulnerable_code") or "-"), styles["SmallText"]),
                Spacer(1, 5),
                Paragraph("<b>Rekomendasi Perbaikan:</b>", styles["BodyText"]),
                Paragraph(_clean_text(item.get("repair_steps") or item.get("recommendation")), styles["SmallText"]),
                Spacer(1, 12),
            ])

            if index % 4 == 0 and index != len(vulnerabilities):
                story.append(PageBreak())

    doc.build(story)
    buffer.seek(0)
    return buffer
