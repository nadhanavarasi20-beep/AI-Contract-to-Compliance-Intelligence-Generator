import json
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from backend.config import settings
from backend.models.schemas import ComplianceReport

class ReportGenerator:
    """Exports compliance reports into JSON and executive PDF formats."""

    @staticmethod
    def save_json_report(report: ComplianceReport) -> Path:
        """Saves compliance report as JSON."""
        file_path = settings.REPORTS_DIR / f"{report.report_id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(report.model_dump_json(indent=2))
        return file_path

    @staticmethod
    def generate_pdf_report(report: ComplianceReport) -> Path:
        """Generates an executive legal compliance audit PDF."""
        pdf_path = settings.REPORTS_DIR / f"{report.report_id}.pdf"
        doc = SimpleDocTemplate(
            str(pdf_path),
            pagesize=letter,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontSize=18,
            leading=22,
            textColor=colors.HexColor('#1E293B'),
            alignment=TA_LEFT,
            fontName='Helvetica-Bold'
        )

        subtitle_style = ParagraphStyle(
            'ReportSubtitle',
            parent=styles['Normal'],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#64748B'),
            alignment=TA_LEFT
        )

        section_heading = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading2'],
            fontSize=13,
            leading=16,
            textColor=colors.HexColor('#0F172A'),
            spaceBefore=12,
            spaceAfter=6,
            fontName='Helvetica-Bold'
        )

        body_style = ParagraphStyle(
            'ReportBody',
            parent=styles['Normal'],
            fontSize=9,
            leading=13,
            textColor=colors.HexColor('#334155')
        )

        badge_style = ParagraphStyle(
            'BadgeStyle',
            parent=styles['Normal'],
            fontSize=11,
            leading=14,
            fontName='Helvetica-Bold',
            alignment=TA_CENTER
        )

        story = []

        # Header Title
        story.append(Paragraph("AI Contract-to-Compliance Intelligence Report", title_style))
        story.append(Spacer(1, 4))
        story.append(Paragraph(f"<b>Engine:</b> {report.engine_name}", subtitle_style))
        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#CBD5E1'), spaceAfter=12))

        # Executive Metadata & Scorecard Table
        score_color = colors.HexColor('#16A34A') if report.compliance_score >= 80 else (
            colors.HexColor('#D97706') if report.compliance_score >= 65 else colors.HexColor('#DC2626')
        )

        meta_data = [
            [
                Paragraph(f"<b>Contract:</b> {report.contract_name}", body_style),
                Paragraph(f"<b>Audit Score:</b> <font color='{score_color.hexval()}'><b>{report.compliance_score}% (Grade {report.grade})</b></font>", badge_style)
            ],
            [
                Paragraph(f"<b>Compliance Policy:</b> {report.policy_name}", body_style),
                Paragraph(f"<b>Engine Mode:</b> {'Resilient Fallback' if report.is_fallback_active else 'Live Gemini'}", body_style)
            ],
            [
                Paragraph(f"<b>Risks Flagged:</b> {len(report.risks)} (High: {report.risk_breakdown.get('high', 0)}, Med: {report.risk_breakdown.get('medium', 0)})", body_style),
                Paragraph(f"<b>Missing Clauses:</b> {len(report.missing_clauses)}", body_style)
            ]
        ]
        meta_table = Table(meta_data, colWidths=[3.8 * inch, 3.2 * inch])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#E2E8F0')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 14))

        # Executive Summary
        story.append(Paragraph("1. Executive Summary", section_heading))
        story.append(Paragraph(report.executive_summary, body_style))
        story.append(Spacer(1, 12))

        # Identified Legal & Compliance Risks
        story.append(Paragraph("2. Identified Legal & Operational Risks", section_heading))
        risk_table_data = [
            [
                Paragraph("<b>Sev</b>", body_style),
                Paragraph("<b>Category</b>", body_style),
                Paragraph("<b>Risk & Rationale</b>", body_style),
                Paragraph("<b>Citation / Clause</b>", body_style)
            ]
        ]
        for r in report.risks[:6]:
            sev_color = "#DC2626" if r.severity == "High" else "#D97706"
            risk_table_data.append([
                Paragraph(f"<font color='{sev_color}'><b>{r.severity}</b></font>", body_style),
                Paragraph(f"<b>{r.category}</b>", body_style),
                Paragraph(f"<b>{r.risk_title}</b><br/>{r.rationale}", body_style),
                Paragraph(f"<b>{r.citation.section_number} ({r.citation.section_title})</b><br/>P. {r.citation.page_number}", body_style)
            ])

        risk_table = Table(risk_table_data, colWidths=[0.7 * inch, 1.2 * inch, 3.3 * inch, 1.8 * inch])
        risk_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E2E8F0')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(risk_table)
        story.append(Spacer(1, 14))

        # Missing Policy Clauses & Suggested Redlines
        story.append(Paragraph("3. Missing Policy Clauses & Recommended Redlines", section_heading))
        missing_data = [
            [
                Paragraph("<b>Required Clause</b>", body_style),
                Paragraph("<b>Policy Source</b>", body_style),
                Paragraph("<b>Suggested Redline Text</b>", body_style)
            ]
        ]
        for m in report.missing_clauses[:4]:
            missing_data.append([
                Paragraph(f"<b>{m.required_clause_name}</b>", body_style),
                Paragraph(f"<b>{m.policy_source_section}</b>", body_style),
                Paragraph(f"<i>\"{m.suggested_redline_text}\"</i>", body_style)
            ])
        missing_table = Table(missing_data, colWidths=[2.2 * inch, 1.3 * inch, 3.5 * inch])
        missing_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E2E8F0')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(missing_table)
        story.append(Spacer(1, 14))

        # Key Deadlines & Timelines
        story.append(Paragraph("4. Key Contract Deadlines & Notice Windows", section_heading))
        deadline_data = [
            [
                Paragraph("<b>Timeframe</b>", body_style),
                Paragraph("<b>Type</b>", body_style),
                Paragraph("<b>Trigger Event / Context</b>", body_style),
                Paragraph("<b>Source</b>", body_style)
            ]
        ]
        for d in report.deadlines[:5]:
            deadline_data.append([
                Paragraph(f"<b>{d.date_or_period}</b>", body_style),
                Paragraph(d.deadline_type, body_style),
                Paragraph(d.description, body_style),
                Paragraph(f"{d.citation.section_number} (P. {d.citation.page_number})", body_style)
            ])
        deadline_table = Table(deadline_data, colWidths=[1.4 * inch, 1.3 * inch, 3.1 * inch, 1.2 * inch])
        deadline_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E2E8F0')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(deadline_table)

        # Build PDF Document
        doc.build(story)
        return pdf_path
