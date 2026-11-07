"""
PDF Report Generation for NIS2 Compliance Audits
Uses ReportLab to create professional audit reports
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class NIS2ReportGenerator:
    """Generate professional PDF reports for compliance audits"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Create custom paragraph styles"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#2c5aa0'),
            spaceAfter=12,
            spaceBefore=12
        ))
    
    def generate_report(self, audit, output_path: str) -> bool:
        """
        Generate complete NIS2 compliance report
        
        Args:
            audit: ComplianceAudit instance
            output_path: Path to save PDF
        
        Returns:
            True if successful, False otherwise
        """
        try:
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2*cm,
                bottomMargin=2*cm
            )
            
            story = []
            
            # Cover Page
            story.extend(self._create_cover_page(audit))
            story.append(PageBreak())
            
            # Executive Summary
            story.extend(self._create_executive_summary(audit))
            story.append(PageBreak())
            
            # Compliance Score Overview
            story.extend(self._create_compliance_overview(audit))
            story.append(PageBreak())
            
            # Gap Analysis Details
            story.extend(self._create_gap_analysis(audit))
            story.append(PageBreak())
            
            # Recommendations
            story.extend(self._create_recommendations(audit))
            story.append(PageBreak())
            
            # Implementation Roadmap
            story.extend(self._create_implementation_roadmap(audit))
            
            # Build PDF
            doc.build(story)
            
            logger.info(f"Report generated successfully: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return False
    
    def _create_cover_page(self, audit):
        """Create report cover page"""
        elements = []
        
        # Title
        title = Paragraph(
            "NIS2 Compliance Audit Report",
            self.styles['CustomTitle']
        )
        elements.append(title)
        elements.append(Spacer(1, 2*cm))
        
        # Client Info
        client_info = f"""
        <b>Client:</b> {audit.client.company_name}<br/>
        <b>KVK Number:</b> {audit.client.kvk_number}<br/>
        <b>Sector:</b> {audit.client.get_sector_display()}<br/>
        <b>Company Size:</b> {audit.client.get_company_size_display()}<br/>
        <br/>
        <b>Audit Date:</b> {audit.created_at.strftime('%d %B %Y')}<br/>
        <b>Report Generated:</b> {datetime.now().strftime('%d %B %Y')}<br/>
        <b>Tier:</b> {audit.get_tier_display()}
        """
        
        elements.append(Paragraph(client_info, self.styles['Normal']))
        elements.append(Spacer(1, 3*cm))
        
        # Compliance Score (Large)
        score_text = f"""
        <para align="center">
            <font size="48" color="#2c5aa0"><b>{audit.compliance_score}%</b></font><br/>
            <font size="16">Overall Compliance Score</font>
        </para>
        """
        elements.append(Paragraph(score_text, self.styles['Normal']))
        
        return elements
    
    def _create_executive_summary(self, audit):
        """Create executive summary section"""
        elements = []
        
        elements.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
        
        # Get gaps by severity
        critical_gaps = audit.gaps.filter(severity='CRITICAL').count()
        high_gaps = audit.gaps.filter(severity='HIGH').count()
        medium_gaps = audit.gaps.filter(severity='MEDIUM').count()
        low_gaps = audit.gaps.filter(severity='LOW').count()
        
        summary_text = f"""
        This report presents the findings of a comprehensive NIS2 Directive compliance 
        assessment for {audit.client.company_name}. The audit was conducted on 
        {audit.created_at.strftime('%d %B %Y')} and evaluated the organization's 
        current security posture against the requirements of the NIS2 Directive.
        <br/><br/>
        <b>Key Findings:</b><br/>
        • Overall Compliance Score: <b>{audit.compliance_score}%</b><br/>
        • Total Gaps Identified: <b>{audit.gaps_identified}</b><br/>
        • Critical Issues: <b>{critical_gaps}</b><br/>
        • High Priority Issues: <b>{high_gaps}</b><br/>
        • Medium Priority Issues: <b>{medium_gaps}</b><br/>
        • Low Priority Issues: <b>{low_gaps}</b><br/>
        <br/>
        The following sections provide detailed analysis of each compliance gap, 
        along with specific recommendations for remediation.
        """
        
        elements.append(Paragraph(summary_text, self.styles['Normal']))
        
        return elements
    
    def _create_compliance_overview(self, audit):
        """Create compliance score overview with charts"""
        elements = []
        
        elements.append(Paragraph("Compliance Overview", self.styles['SectionHeader']))
        
        # Category breakdown table
        categories = {}
        for gap in audit.gaps.all():
            if gap.category not in categories:
                categories[gap.category] = {'count': 0, 'avg_risk': 0}
            categories[gap.category]['count'] += 1
            categories[gap.category]['avg_risk'] += gap.risk_score
        
        # Calculate averages
        for cat in categories:
            if categories[cat]['count'] > 0:
                categories[cat]['avg_risk'] /= categories[cat]['count']
        
        # Create table
        table_data = [['Category', 'Gaps Found', 'Avg Risk Score']]
        for cat, data in sorted(categories.items(), key=lambda x: x[1]['count'], reverse=True):
            table_data.append([
                cat.replace('_', ' ').title(),
                str(data['count']),
                f"{data['avg_risk']:.1f}/10"
            ])
        
        if len(table_data) > 1:
            table = Table(table_data, colWidths=[8*cm, 3*cm, 3*cm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5aa0')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(table)
        
        return elements
    
    def _create_gap_analysis(self, audit):
        """Create detailed gap analysis section"""
        elements = []
        
        elements.append(Paragraph("Detailed Gap Analysis", self.styles['SectionHeader']))
        
        # Group gaps by severity
        for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            gaps = audit.gaps.filter(severity=severity).order_by('-risk_score')
            
            if gaps.exists():
                severity_header = Paragraph(
                    f"{severity} Priority Gaps ({gaps.count()})",
                    self.styles['Heading3']
                )
                elements.append(severity_header)
                elements.append(Spacer(1, 0.5*cm))
                
                for gap in gaps:
                    gap_text = f"""
                    <b>{gap.title}</b><br/>
                    <i>NIS2 Reference: {gap.nis2_article}</i><br/>
                    <br/>
                    <b>Current State:</b> {gap.current_state}<br/>
                    <b>Required State:</b> {gap.required_state}<br/>
                    <br/>
                    <b>Recommendation:</b> {gap.recommendation}<br/>
                    <br/>
                    <b>Estimated Effort:</b> {gap.estimated_effort_hours} hours<br/>
                    <b>Risk Score:</b> {gap.risk_score}/10<br/>
                    """
                    
                    elements.append(Paragraph(gap_text, self.styles['Normal']))
                    elements.append(Spacer(1, 0.5*cm))
        
        return elements
    
    def _create_recommendations(self, audit):
        """Create recommendations section"""
        elements = []
        
        elements.append(Paragraph("Priority Recommendations", self.styles['SectionHeader']))
        
        # Get top 5 critical gaps
        critical_gaps = audit.gaps.filter(severity='CRITICAL').order_by('-risk_score')[:5]
        
        if critical_gaps.exists():
            rec_text = """
            Based on the compliance assessment, we recommend addressing the following 
            critical issues immediately:<br/><br/>
            """
            
            for i, gap in enumerate(critical_gaps, 1):
                rec_text += f"""
                <b>{i}. {gap.title}</b><br/>
                {gap.recommendation}<br/>
                <i>Estimated effort: {gap.estimated_effort_hours} hours</i><br/><br/>
                """
            
            elements.append(Paragraph(rec_text, self.styles['Normal']))
        else:
            elements.append(Paragraph(
                "No critical gaps identified. Focus on high and medium priority items.",
                self.styles['Normal']
            ))
        
        return elements
    
    def _create_implementation_roadmap(self, audit):
        """Create implementation roadmap"""
        elements = []
        
        elements.append(Paragraph("Implementation Roadmap", self.styles['SectionHeader']))
        
        total_hours = sum(gap.estimated_effort_hours for gap in audit.gaps.all())
        
        roadmap_text = f"""
        We recommend implementing the identified improvements in the following phases:<br/><br/>
        
        <b>Phase 1 (Weeks 1-4): Critical Issues</b><br/>
        Address all CRITICAL severity gaps to mitigate immediate risks.<br/><br/>
        
        <b>Phase 2 (Weeks 5-12): High Priority</b><br/>
        Implement HIGH severity recommendations to achieve baseline compliance.<br/><br/>
        
        <b>Phase 3 (Weeks 13-24): Medium Priority</b><br/>
        Address MEDIUM severity gaps to strengthen security posture.<br/><br/>
        
        <b>Phase 4 (Ongoing): Continuous Improvement</b><br/>
        Implement LOW severity recommendations and maintain compliance.<br/><br/>
        
        <b>Total Estimated Effort:</b> {total_hours} hours<br/>
        <b>Recommended Timeline:</b> 6 months
        """
        
        elements.append(Paragraph(roadmap_text, self.styles['Normal']))
        
        return elements
