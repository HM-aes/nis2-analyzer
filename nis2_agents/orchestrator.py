"""
NIS2 Orchestrator - Coordinates the entire audit workflow
Manages all 5 agents and produces the final report
"""

from compliance_engine.models import ComplianceAudit, ComplianceGap, ClientDocument
from rag_engine.qdrant_client import NIS2QdrantClient
from .auditor import NIS2Auditor
from .document_processor import DocumentProcessor
from .report_generator import NIS2ReportGenerator
import logging
from django.utils import timezone
from django.conf import settings
from pathlib import Path

logger = logging.getLogger(__name__)


class NIS2Orchestrator:
    """
    Coordinates the entire NIS2 compliance audit process
    """
    
    def __init__(self):
        self.qdrant = NIS2QdrantClient()
        self.auditor = NIS2Auditor()
        self.doc_processor = DocumentProcessor()
        self.report_generator = NIS2ReportGenerator()
    
    def process_audit(self, audit_id: str) -> dict:
        """
        Process a complete NIS2 audit
        
        Workflow:
        1. Load client documents
        2. Extract text from documents
        3. Query Qdrant for relevant NIS2 requirements
        4. Run AI gap analysis (Claude via Pydantic AI)
        5. Save gaps to database
        6. Generate PDF report
        7. Update audit status
        
        Args:
            audit_id: UUID of the ComplianceAudit
        
        Returns:
            dict with status and results
        """
        try:
            # Load audit
            audit = ComplianceAudit.objects.get(id=audit_id)
            audit.status = 'PROCESSING'
            audit.started_at = timezone.now()
            audit.save()
            
            logger.info(f"Starting audit processing for {audit.client.company_name}")
            
            # Step 1: Gather client documents
            documents = ClientDocument.objects.filter(audit=audit, processed=True)
            if not documents.exists():
                return {'status': 'error', 'message': 'No processed documents found'}
            
            # Step 2: Extract text from all documents
            client_docs_text = "\n\n".join([
                f"Document: {doc.original_filename}\n{self._extract_text(doc)}"
                for doc in documents
            ])
            
            # Step 3: Query Qdrant for relevant NIS2 requirements
            # Use client's industry/sector for filtering
            search_query = f"NIS2 requirements for {audit.client.get_sector_display()}"
            nis2_context = self.qdrant.search(
                query=search_query,
                top_k=20,
                filters={'language': 'nl'}  # Dutch requirements
            )
            
            nis2_requirements = [result['text'] for result in nis2_context]
            
            # Step 4: Run AI gap analysis
            audit.status = 'ANALYSIS'
            audit.save()
            
            gap_analysis = self.auditor.analyze_compliance_sync(
                client_documents=client_docs_text,
                nis2_requirements=nis2_requirements
            )
            
            # Step 5: Save gaps to database
            for gap_data in gap_analysis.gaps:
                ComplianceGap.objects.create(
                    audit=audit,
                    category=gap_data.category,
                    severity=gap_data.severity,
                    title=gap_data.title,
                    nis2_article=gap_data.nis2_article,
                    current_state=gap_data.current_state,
                    required_state=gap_data.required_state,
                    recommendation=gap_data.recommendation,
                    risk_score=gap_data.risk_score,
                    estimated_effort_hours=gap_data.estimated_effort_hours,
                    nis2_requirement=f"See {gap_data.nis2_article}",
                    description=gap_data.title,
                    business_impact=f"Risk score: {gap_data.risk_score}/10"
                )
            
            # Update audit with results
            audit.gaps_identified = len(gap_analysis.gaps)
            audit.compliance_score = gap_analysis.overall_compliance_score
            audit.status = 'COMPLETE'
            audit.completed_at = timezone.now()
            audit.save()
            
            logger.info(f"Audit complete: {audit.gaps_identified} gaps, {audit.compliance_score}% compliant")
            
            # Step 6: Generate PDF report
            try:
                report_filename = f"NIS2_Report_{audit.client.company_name.replace(' ', '_')}_{audit.id}.pdf"
                
                # Ensure reports directory exists
                reports_dir = Path(settings.MEDIA_ROOT) / 'reports'
                reports_dir.mkdir(parents=True, exist_ok=True)
                
                report_path = reports_dir / report_filename
                
                if self.report_generator.generate_report(audit, str(report_path)):
                    audit.report_file = f"reports/{report_filename}"
                    audit.report_generated = True
                    audit.report_generated_at = timezone.now()
                    audit.save()
                    logger.info(f"PDF report generated: {report_filename}")
                else:
                    logger.warning("PDF report generation failed")
            
            except Exception as e:
                logger.error(f"Error generating PDF report: {e}")
            
            return {
                'status': 'success',
                'audit_id': str(audit.id),
                'gaps_found': audit.gaps_identified,
                'compliance_score': float(audit.compliance_score),
                'summary': gap_analysis.summary
            }
        
        except Exception as e:
            logger.error(f"Error processing audit: {e}")
            audit.status = 'REVIEW'  # Mark for manual review
            audit.save()
            return {'status': 'error', 'message': str(e)}
    
    def _extract_text(self, document: ClientDocument) -> str:
        """
        Extract text from a document using Docling
        """
        try:
            text = self.doc_processor.extract_text(document.file.path)
            
            if text:
                # Update document metadata
                document.text_extracted = True
                document.pages_count = self.doc_processor.get_page_count(document.file.path)
                document.processed = True
                document.processed_at = timezone.now()
                document.save()
                
                logger.info(f"Extracted {len(text)} chars from {document.original_filename}")
                return text
            else:
                logger.warning(f"Failed to extract text from {document.original_filename}")
                return f"[Failed to extract text from {document.original_filename}]"
        
        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            return f"[Error extracting text from {document.original_filename}]"
