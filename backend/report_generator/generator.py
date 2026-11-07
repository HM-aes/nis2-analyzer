"""
NIS2 PDF Report Generator
Generates professional 20-30 page reports using ReportLab.
Two report types:
  - Sector Requirements Report (Type 1, no documents needed)
  - Gap Analysis Report (Type 2, post-audit paid product)
"""

import io
import json
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor, white, black
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, Image, PageBreak,
    HRFlowable, KeepTogether,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from django.utils.translation import gettext_lazy as _

import anthropic

from .charts import (
    compliance_gauge_image,
    severity_bar_chart_image,
    category_heatmap_image,
    remediation_timeline_image,
    png_to_reportlab_image,
)
from .claude_prompts import (
    SECTOR_REPORT_SYSTEM,
    SECTOR_REQUIREMENTS_PROMPT,
    EXECUTIVE_SUMMARY_PROMPT,
    REMEDIATION_ROADMAP_PROMPT,
    GAP_NARRATIVE_PROMPT,
    FINE_EXPOSURE_PROMPT,
)

# ── Brand colours (AES AI Solutions) ─────────────────────────────────────────
BRAND_DARK = HexColor('#0f172a')
BRAND_BLUE = HexColor('#1d4ed8')
BRAND_LIGHT = HexColor('#f8fafc')
BRAND_ACCENT = HexColor('#3b82f6')
SEVERITY_CRITICAL = HexColor('#dc2626')
SEVERITY_HIGH = HexColor('#ea580c')
SEVERITY_MEDIUM = HexColor('#ca8a04')
SEVERITY_LOW = HexColor('#16a34a')


class NIS2ReportGenerator:
    """Main PDF report generator for NIS2 compliance reports."""

    def __init__(self):
        self.client = anthropic.Anthropic()
        self.styles = self._build_styles()

    def _build_styles(self):
        """Build custom ReportLab paragraph styles."""
        styles = getSampleStyleSheet()
        custom_styles = [
            ParagraphStyle(
                'ReportTitle',
                fontSize=28,
                textColor=white,
                alignment=TA_CENTER,
                spaceAfter=12,
                fontName='Helvetica-Bold',
            ),
            ParagraphStyle(
                'ReportSubtitle',
                fontSize=14,
                textColor=HexColor('#cbd5e1'),
                alignment=TA_CENTER,
                spaceAfter=8,
                fontName='Helvetica',
            ),
            ParagraphStyle(
                'H1',
                fontSize=20,
                textColor=BRAND_DARK,
                spaceBefore=20,
                spaceAfter=12,
                fontName='Helvetica-Bold',
            ),
            ParagraphStyle(
                'H2',
                fontSize=14,
                textColor=BRAND_BLUE,
                spaceBefore=16,
                spaceAfter=8,
                fontName='Helvetica-Bold',
            ),
            ParagraphStyle(
                'H3',
                fontSize=11,
                textColor=BRAND_DARK,
                spaceBefore=10,
                spaceAfter=6,
                fontName='Helvetica-Bold',
            ),
            ParagraphStyle(
                'Body',
                fontSize=10,
                textColor=BRAND_DARK,
                spaceBefore=4,
                spaceAfter=6,
                leading=16,
                fontName='Helvetica',
                alignment=TA_JUSTIFY,
            ),
            ParagraphStyle(
                'Caption',
                fontSize=8,
                textColor=HexColor('#64748b'),
                alignment=TA_CENTER,
                spaceAfter=12,
                fontName='Helvetica',
            ),
            ParagraphStyle(
                'Footer',
                fontSize=8,
                textColor=HexColor('#94a3b8'),
                alignment=TA_CENTER,
                fontName='Helvetica',
            ),
        ]
        for style in custom_styles:
            styles.add(style)
        return styles

    def _call_claude(self, prompt: str, max_tokens: int = 2000) -> str:
        """Call Claude API and return text response."""
        message = self.client.messages.create(
            model='claude-sonnet-4-20250514',
            max_tokens=max_tokens,
            system=SECTOR_REPORT_SYSTEM,
            messages=[{'role': 'user', 'content': prompt}]
        )
        return message.content[0].text

    def _cover_page(self, elements, report_type: str,
                    company_name: str, sector: str, date_str: str):
        """Build cover page with dark background and branding."""
        # Full-width dark header table
        cover_data = [[
            Paragraph('NIS2 COMPLIANCE REPORT', self.styles['ReportTitle']),
        ]]
        cover_table = Table(cover_data, colWidths=[17 * cm])
        cover_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), BRAND_DARK),
            ('TOPPADDING', (0, 0), (-1, -1), 80),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 30),
            ('LEFTPADDING', (0, 0), (-1, -1), 20),
            ('RIGHTPADDING', (0, 0), (-1, -1), 20),
        ]))
        elements.append(cover_table)

        elements.append(Spacer(1, 1 * cm))
        elements.append(Paragraph(report_type, self.styles['H1']))
        elements.append(Paragraph(company_name, self.styles['H2']))
        elements.append(Spacer(1, 0.3 * cm))
        elements.append(Paragraph(
            _('Sector: %(sector)s | Date: %(date)s') % {'sector': sector, 'date': date_str},
            self.styles['Body']
        ))
        elements.append(Spacer(1, 0.5 * cm))
        elements.append(HRFlowable(width='100%', thickness=2, color=BRAND_BLUE))
        elements.append(Spacer(1, 0.5 * cm))
        elements.append(Paragraph(
            _('Prepared by AES AI Solutions | aes-ai.nl | support@aes-ai.nl'),
            self.styles['Caption']
        ))
        elements.append(PageBreak())

    def _render_content_blocks(self, elements, content: str):
        """Parse Claude text output into ReportLab paragraphs."""
        for paragraph in content.split('\n\n'):
            para = paragraph.strip()
            if not para:
                continue
            # Detect numbered headings (e.g., "1. ENTITY CLASSIFICATION")
            if para and para[0].isdigit() and '. ' in para[:5]:
                elements.append(Paragraph(para, self.styles['H2']))
            elif para.startswith('#'):
                clean = para.lstrip('#').strip()
                elements.append(Paragraph(clean, self.styles['H2']))
            elif para.isupper() and len(para) < 80:
                elements.append(Paragraph(para, self.styles['H3']))
            else:
                # Clean up markdown-like formatting
                clean_para = para.replace('**', '').replace('*', '').replace('__', '')
                elements.append(Paragraph(clean_para, self.styles['Body']))
            elements.append(Spacer(1, 0.2 * cm))

    def generate_sector_report(
            self, company_name: str, sector: str,
            country: str, company_size: str,
            entity_type: str = 'IMPORTANT') -> bytes:
        """
        Generate Type 1: Sector Requirements Report.
        No documents needed. Returns PDF bytes.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=2 * cm,
            rightMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
            title=f'NIS2 Sector Report — {company_name}',
            author='AES AI Solutions',
        )
        elements = []
        date_str = datetime.now().strftime('%B %Y')

        # Cover page
        self._cover_page(
            elements,
            _('Sector Requirements Analysis'),
            company_name, sector, date_str
        )

        # Section header
        elements.append(Paragraph(
            _('NIS2 Requirements for %(company)s') % {'company': company_name},
            self.styles['H1']
        ))
        elements.append(HRFlowable(width='100%', thickness=1, color=BRAND_BLUE))
        elements.append(Spacer(1, 0.5 * cm))

        # Generate main content via Claude
        prompt = SECTOR_REQUIREMENTS_PROMPT.format(
            company_name=company_name,
            sector=sector,
            country=country,
            entity_type=entity_type,
            company_size=company_size,
        )
        content = self._call_claude(prompt, max_tokens=3000)
        self._render_content_blocks(elements, content)

        # Fine exposure section
        elements.append(PageBreak())
        elements.append(Paragraph(_('Regulatory Fine Exposure'), self.styles['H1']))
        elements.append(HRFlowable(width='100%', thickness=1, color=BRAND_BLUE))
        elements.append(Spacer(1, 0.3 * cm))
        fine_prompt = FINE_EXPOSURE_PROMPT.format(
            entity_type=entity_type,
            annual_turnover='Unknown',
            country=country,
            critical_gaps='N/A',
            total_gaps='N/A',
        )
        fine_content = self._call_claude(fine_prompt)
        self._render_content_blocks(elements, fine_content)

        # Call to action page
        elements.append(PageBreak())
        elements.append(Paragraph(_('Next Steps'), self.styles['H1']))
        elements.append(HRFlowable(width='100%', thickness=1, color=BRAND_BLUE))
        elements.append(Spacer(1, 0.3 * cm))
        elements.append(Paragraph(
            _(
                'This report describes your NIS2 requirements based on your sector and entity type. '
                'To understand your current compliance position, upload your existing policy and '
                'procedure documents for a full gap analysis.'
            ),
            self.styles['Body']
        ))
        elements.append(Spacer(1, 0.5 * cm))

        # CTA box
        cta_data = [[
            Paragraph(
                _(
                    '🔍 Full Gap Analysis: €950\n\nUpload your documents via our platform for '
                    'an AI-powered NIS2 gap analysis.\nContact: support@aes-ai.nl'
                ),
                self.styles['Body']
            )
        ]]
        cta_table = Table(cta_data, colWidths=[15 * cm])
        cta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), HexColor('#eff6ff')),
            ('BORDER', (0, 0), (-1, -1), 1, BRAND_BLUE),
            ('BOX', (0, 0), (-1, -1), 1.5, BRAND_BLUE),
            ('TOPPADDING', (0, 0), (-1, -1), 16),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 16),
            ('LEFTPADDING', (0, 0), (-1, -1), 16),
            ('RIGHTPADDING', (0, 0), (-1, -1), 16),
        ]))
        elements.append(cta_table)

        # About AES
        elements.append(PageBreak())
        elements.append(Paragraph(_('About AES AI Solutions'), self.styles['H1']))
        elements.append(Paragraph(
            _(
                'AES AI Solutions is a specialized NIS2 compliance technology company based '
                'in the Netherlands. We combine AI-powered analysis with deep regulatory expertise '
                'to help organizations achieve and maintain NIS2 compliance. '
                'Contact us at support@aes-ai.nl or visit aes-ai.nl.'
            ),
            self.styles['Body']
        ))

        doc.build(elements)
        return buffer.getvalue()

    def generate_gap_report(self, audit, gaps, client) -> bytes:
        """
        Generate Type 2: Gap Analysis Report.
        Full paid report from completed audit. Returns PDF bytes.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=2 * cm,
            rightMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
            title=f'NIS2 Gap Analysis — {client.company_name}',
            author='AES AI Solutions',
        )
        elements = []
        date_str = datetime.now().strftime('%B %Y')

        # Aggregate gap data
        gap_list = list(gaps)
        critical = sum(1 for g in gap_list if g.severity == 'CRITICAL')
        high = sum(1 for g in gap_list if g.severity == 'HIGH')
        medium = sum(1 for g in gap_list if g.severity == 'MEDIUM')
        low = sum(1 for g in gap_list if g.severity == 'LOW')
        total_hours = sum(g.estimated_effort_hours or 0 for g in gap_list)
        total_cost = sum(float(g.estimated_cost_euros or 0) for g in gap_list)

        # Category breakdown
        category_data = {}
        for gap in gap_list:
            cat = gap.category or 'Other'
            category_data[cat] = category_data.get(cat, 0) + 1

        # Severity sort order
        severity_order = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']
        sorted_gaps = sorted(
            gap_list,
            key=lambda g: severity_order.index(g.severity)
            if g.severity in severity_order else 99
        )

        # ── Cover page ─────────────────────────────────────────────────────────
        self._cover_page(
            elements,
            'NIS2 Gap Analysis Report',
            client.company_name,
            client.sector, date_str
        )

        # ── Executive Summary ──────────────────────────────────────────────────
        elements.append(Paragraph('Executive Summary', self.styles['H1']))
        elements.append(HRFlowable(width='100%', thickness=1, color=BRAND_BLUE))
        elements.append(Spacer(1, 0.3 * cm))

        top_gaps = '\n'.join([
            f'- {g.title} ({g.severity})'
            for g in sorted_gaps[:5]
        ])
        exec_summary = self._call_claude(
            EXECUTIVE_SUMMARY_PROMPT.format(
                company_name=client.company_name,
                sector=client.sector,
                compliance_score=audit.compliance_score or 0,
                total_gaps=len(gap_list),
                critical_gaps=critical,
                high_gaps=high,
                medium_gaps=medium,
                low_gaps=low,
                remediation_hours=total_hours,
                remediation_cost=int(total_cost),
                top_gaps_summary=top_gaps,
            ),
            max_tokens=600
        )
        elements.append(Paragraph(exec_summary, self.styles['Body']))

        # ── Score Summary Table ────────────────────────────────────────────────
        elements.append(Spacer(1, 0.5 * cm))
        score_data = [
            ['Metric', 'Value'],
            ['Compliance Score', f'{audit.compliance_score or 0}%'],
            ['Total Gaps Identified', str(len(gap_list))],
            ['Critical Gaps', str(critical)],
            ['High Severity Gaps', str(high)],
            ['Medium Severity Gaps', str(medium)],
            ['Low Severity Gaps', str(low)],
            ['Total Remediation Hours', f'{total_hours} hours'],
            ['Estimated Remediation Cost', f'€{int(total_cost):,}'],
        ]
        score_table = Table(score_data, colWidths=[9 * cm, 8 * cm])
        score_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), BRAND_DARK),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#f8fafc')]),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#e2e8f0')),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ]))
        elements.append(score_table)

        # ── Compliance Score Gauge Chart ───────────────────────────────────────
        elements.append(PageBreak())
        elements.append(Paragraph('Compliance Score', self.styles['H1']))
        elements.append(HRFlowable(width='100%', thickness=1, color=BRAND_BLUE))
        elements.append(Spacer(1, 0.3 * cm))
        try:
            gauge_png = compliance_gauge_image(int(audit.compliance_score or 0))
            gauge_img = png_to_reportlab_image(gauge_png, 12 * cm, 8 * cm)
            elements.append(Image(gauge_img, width=12 * cm, height=8 * cm))
            elements.append(Paragraph(
                _('NIS2 Compliance Score: %(score)s%% — %(label)s') % {
                    'score': audit.compliance_score or 0,
                    'label': (
                        _('Good')
                        if (audit.compliance_score or 0) >= 70
                        else _('Improvement Required')
                        if (audit.compliance_score or 0) >= 40
                        else _('Critical Action Required')
                    ),
                },
                self.styles['Caption']
            ))
        except Exception:
            elements.append(Paragraph(
                f'Compliance Score: {audit.compliance_score or 0}%',
                self.styles['H2']
            ))

        # ── Severity Bar Chart ─────────────────────────────────────────────────
        elements.append(Spacer(1, 0.5 * cm))
        elements.append(Paragraph('Gap Severity Distribution', self.styles['H2']))
        try:
            severity_png = severity_bar_chart_image(critical, high, medium, low)
            severity_img = png_to_reportlab_image(severity_png, 14 * cm, 8 * cm)
            elements.append(Image(severity_img, width=14 * cm, height=8 * cm))
        except Exception:
            pass

        # ── Category Heatmap ───────────────────────────────────────────────────
        elements.append(PageBreak())
        elements.append(Paragraph('Gaps by Category', self.styles['H1']))
        elements.append(HRFlowable(width='100%', thickness=1, color=BRAND_BLUE))
        elements.append(Spacer(1, 0.3 * cm))
        if category_data:
            try:
                heatmap_png = category_heatmap_image(category_data)
                heatmap_img = png_to_reportlab_image(heatmap_png, 15 * cm, 9 * cm)
                elements.append(Image(heatmap_img, width=15 * cm, height=9 * cm))
            except Exception:
                pass

        # ── Gap Summary Table ──────────────────────────────────────────────────
        elements.append(PageBreak())
        elements.append(Paragraph('Identified Compliance Gaps', self.styles['H1']))
        elements.append(HRFlowable(width='100%', thickness=1, color=BRAND_BLUE))
        elements.append(Spacer(1, 0.3 * cm))

        gap_table_data = [['#', 'Gap Title', 'Severity', 'Category', 'Hours']]
        severity_colors = {
            'CRITICAL': SEVERITY_CRITICAL,
            'HIGH': SEVERITY_HIGH,
            'MEDIUM': SEVERITY_MEDIUM,
            'LOW': SEVERITY_LOW,
        }
        for i, gap in enumerate(sorted_gaps, 1):
            gap_table_data.append([
                str(i),
                gap.title[:55],
                gap.severity,
                (gap.category or 'Other').replace('_', ' ').title(),
                str(gap.estimated_effort_hours or 0),
            ])

        gap_table = Table(
            gap_table_data,
            colWidths=[0.8 * cm, 7.5 * cm, 2.5 * cm, 3.5 * cm, 1.7 * cm]
        )
        gap_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), BRAND_DARK),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#f8fafc')]),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#e2e8f0')),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(gap_table)

        # ── Individual Gap Details ─────────────────────────────────────────────
        elements.append(PageBreak())
        elements.append(Paragraph('Gap Analysis Detail', self.styles['H1']))
        elements.append(HRFlowable(width='100%', thickness=1, color=BRAND_BLUE))
        elements.append(Spacer(1, 0.3 * cm))

        for i, gap in enumerate(sorted_gaps, 1):
            sev_color = severity_colors.get(gap.severity, BRAND_DARK)

            gap_block = []
            gap_block.append(Paragraph(f'{i}. {gap.title}', self.styles['H2']))

            # Severity badge row
            badge_data = [[
                Paragraph(f'Severity: {gap.severity}', self.styles['Caption']),
                Paragraph(f'Category: {(gap.category or "Other").replace("_", " ").title()}', self.styles['Caption']),
                Paragraph(f'Est. Hours: {gap.estimated_effort_hours or 0}', self.styles['Caption']),
                Paragraph(f'NIS2: {gap.nis2_article or "—"}', self.styles['Caption']),
            ]]
            badge_table = Table(badge_data, colWidths=[4 * cm, 5 * cm, 3.5 * cm, 3.5 * cm])
            badge_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, 0), sev_color),
                ('TEXTCOLOR', (0, 0), (0, 0), white),
                ('BACKGROUND', (1, 0), (-1, -1), HexColor('#f1f5f9')),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ]))
            gap_block.append(badge_table)
            gap_block.append(Spacer(1, 0.3 * cm))

            # Current vs Required state
            state_data = [
                [
                    Paragraph('Current State', self.styles['H2']),
                    Paragraph('Required State', self.styles['H2']),
                ],
                [
                    Paragraph(gap.current_state or 'Not assessed', self.styles['Body']),
                    Paragraph(gap.required_state or '—', self.styles['Body']),
                ]
            ]
            state_table = Table(state_data, colWidths=[8 * cm, 8 * cm])
            state_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, 0), HexColor('#fee2e2')),
                ('BACKGROUND', (1, 0), (1, 0), HexColor('#dcfce7')),
                ('BACKGROUND', (0, 1), (0, 1), HexColor('#fff5f5')),
                ('BACKGROUND', (1, 1), (1, 1), HexColor('#f0fdf4')),
                ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#e2e8f0')),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ]))
            gap_block.append(state_table)

            if gap.business_impact:
                gap_block.append(Spacer(1, 0.2 * cm))
                gap_block.append(Paragraph(
                    f'Business Impact: {gap.business_impact}',
                    self.styles['Body']
                ))

            if gap.recommendation:
                gap_block.append(Spacer(1, 0.2 * cm))
                gap_block.append(Paragraph(
                    f'Recommendation: {gap.recommendation}',
                    self.styles['Body']
                ))

            gap_block.append(Spacer(1, 0.5 * cm))
            gap_block.append(HRFlowable(width='100%', thickness=0.5, color=HexColor('#e2e8f0')))
            gap_block.append(Spacer(1, 0.3 * cm))

            try:
                elements.append(KeepTogether(gap_block))
            except Exception:
                elements.extend(gap_block)

        # ── Remediation Roadmap ────────────────────────────────────────────────
        elements.append(PageBreak())
        elements.append(Paragraph('Remediation Roadmap', self.styles['H1']))
        elements.append(HRFlowable(width='100%', thickness=1, color=BRAND_BLUE))
        elements.append(Spacer(1, 0.3 * cm))

        gaps_json = json.dumps([{
            'title': g.title,
            'severity': g.severity,
            'category': g.category,
            'estimated_hours': g.estimated_effort_hours,
        } for g in sorted_gaps[:20]], indent=2)

        roadmap = self._call_claude(
            REMEDIATION_ROADMAP_PROMPT.format(
                gaps_json=gaps_json,
                sector=client.sector,
                company_size=client.company_size,
                country=getattr(client, 'country', 'NL'),
            ),
            max_tokens=2000
        )
        self._render_content_blocks(elements, roadmap)

        # Roadmap timeline chart
        phases = [
            {'name': 'Phase 1 (0-30 days)', 'start': 0, 'end': 30, 'tasks': critical},
            {'name': 'Phase 2 (30-90 days)', 'start': 30, 'end': 90, 'tasks': high},
            {'name': 'Phase 3 (90-180 days)', 'start': 90, 'end': 180, 'tasks': medium},
        ]
        try:
            timeline_png = remediation_timeline_image(phases)
            timeline_img = png_to_reportlab_image(timeline_png, 15 * cm, 7 * cm)
            elements.append(Image(timeline_img, width=15 * cm, height=7 * cm))
        except Exception:
            pass

        # ── Fine Exposure ──────────────────────────────────────────────────────
        elements.append(PageBreak())
        elements.append(Paragraph('Regulatory Risk & Fine Exposure', self.styles['H1']))
        elements.append(HRFlowable(width='100%', thickness=1, color=BRAND_BLUE))
        elements.append(Spacer(1, 0.3 * cm))
        fine_content = self._call_claude(
            FINE_EXPOSURE_PROMPT.format(
                entity_type='IMPORTANT',
                annual_turnover='Unknown',
                country=getattr(client, 'country', 'NL'),
                critical_gaps=critical,
                total_gaps=len(gap_list),
            )
        )
        self._render_content_blocks(elements, fine_content)

        # ── About AES AI Solutions ─────────────────────────────────────────────
        elements.append(PageBreak())
        elements.append(Paragraph('About AES AI Solutions', self.styles['H1']))
        elements.append(HRFlowable(width='100%', thickness=1, color=BRAND_BLUE))
        elements.append(Spacer(1, 0.3 * cm))
        elements.append(Paragraph(
            _(
                'AES AI Solutions is a specialized NIS2 compliance technology company based '
                'in the Netherlands. We combine AI-powered analysis with deep regulatory expertise '
                'to help organizations achieve and maintain NIS2 compliance. '
                'Our AI-powered analysis platform processes your existing documents and identifies '
                'compliance gaps based on the official NIS2 Directive (EU) 2022/2555.'
            ),
            self.styles['Body']
        ))
        elements.append(Spacer(1, 0.3 * cm))
        elements.append(Paragraph(
            _('Contact: support@aes-ai.nl | Website: aes-ai.nl'),
            self.styles['Body']
        ))

        doc.build(elements)
        return buffer.getvalue()
