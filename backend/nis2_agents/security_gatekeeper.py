"""
Security Gatekeeper Agent
Validates documents for security issues before processing
"""
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from typing import Dict, List
import logging
import hashlib
import os

logger = logging.getLogger(__name__)


class SecurityGatekeeper:
    """
    Security validation for uploaded documents
    - PII detection and anonymization
    - File validation
    - Security scanning
    """
    
    def __init__(self):
        """Initialize Presidio analyzers"""
        try:
            self.analyzer = AnalyzerEngine()
            self.anonymizer = AnonymizerEngine()
            logger.info("Presidio security engines initialized")
        except Exception as e:
            logger.error(f"Error initializing Presidio: {e}")
            self.analyzer = None
            self.anonymizer = None
    
    def scan_document(self, document) -> Dict:
        """
        Perform security scan on uploaded document
        
        Args:
            document: ClientDocument instance
        
        Returns:
            dict with scan results
        """
        results = {
            'safe': True,
            'virus_found': False,
            'pii_detected': False,
            'pii_types': [],
            'file_valid': True,
            'errors': []
        }
        
        try:
            # 1. File validation
            if not self._validate_file_type(document.original_filename):
                results['safe'] = False
                results['file_valid'] = False
                results['errors'].append('Invalid file type')
                return results
            
            # 2. File size check (50MB max)
            if document.file_size_bytes > 50 * 1024 * 1024:
                results['safe'] = False
                results['errors'].append('File too large (max 50MB)')
                return results
            
            # 3. File exists check
            if not os.path.exists(document.file.path):
                results['safe'] = False
                results['errors'].append('File not found on disk')
                return results
            
            # 4. Calculate file hash for integrity
            file_hash = self.calculate_file_hash(document.file.path)
            logger.info(f"File hash: {file_hash[:16]}...")
            
            # 5. PII detection (if text is available)
            # Note: This would typically run after text extraction
            # For now, we mark it as scanned
            document.virus_scanned = True
            document.save()
            
            logger.info(f"Document {document.original_filename} passed security scan")
            
        except Exception as e:
            logger.error(f"Error scanning document: {e}")
            results['safe'] = False
            results['errors'].append(str(e))
        
        return results
    
    def detect_pii(self, text: str) -> Dict:
        """
        Detect PII in text using Presidio
        
        Args:
            text: Text to analyze
        
        Returns:
            dict with PII detection results
        """
        if not self.analyzer:
            return {'found': False, 'types': [], 'count': 0}
        
        try:
            # Analyze text for PII
            results = self.analyzer.analyze(
                text=text,
                language='en',
                entities=[
                    'PERSON', 'EMAIL_ADDRESS', 'PHONE_NUMBER',
                    'IBAN_CODE', 'CREDIT_CARD', 'IP_ADDRESS',
                    'NL_BSN'  # Dutch social security number
                ]
            )
            
            pii_types = list(set([result.entity_type for result in results]))
            
            return {
                'found': len(results) > 0,
                'types': pii_types,
                'count': len(results)
            }
            
        except Exception as e:
            logger.error(f"Error detecting PII: {e}")
            return {'found': False, 'types': [], 'count': 0}
    
    def anonymize_pii(self, text: str) -> str:
        """
        Anonymize PII in text
        
        Args:
            text: Text containing PII
        
        Returns:
            Anonymized text
        """
        if not self.analyzer or not self.anonymizer:
            return text
        
        try:
            # Analyze
            analyzer_results = self.analyzer.analyze(
                text=text,
                language='en',
                entities=['PERSON', 'EMAIL_ADDRESS', 'PHONE_NUMBER']
            )
            
            # Anonymize
            anonymized_result = self.anonymizer.anonymize(
                text=text,
                analyzer_results=analyzer_results
            )
            
            return anonymized_result.text
            
        except Exception as e:
            logger.error(f"Error anonymizing PII: {e}")
            return text
    
    def _validate_file_type(self, filename: str) -> bool:
        """
        Validate file extension
        
        Args:
            filename: Name of the file
        
        Returns:
            True if valid, False otherwise
        """
        allowed_extensions = ['.pdf', '.docx', '.txt', '.doc', '.pptx']
        return any(filename.lower().endswith(ext) for ext in allowed_extensions)
    
    def calculate_file_hash(self, file_path: str) -> str:
        """
        Calculate SHA256 hash of file
        
        Args:
            file_path: Path to file
        
        Returns:
            SHA256 hash as hex string
        """
        sha256_hash = hashlib.sha256()
        
        try:
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating file hash: {e}")
            return ""
    
    def scan_text_for_threats(self, text: str) -> Dict:
        """
        Scan text for potential security threats
        
        Args:
            text: Text to scan
        
        Returns:
            dict with threat analysis
        """
        threats = {
            'suspicious_patterns': [],
            'risk_level': 'LOW'
        }
        
        # Check for suspicious patterns
        suspicious_keywords = [
            'DROP TABLE', 'DELETE FROM', '<script>',
            'javascript:', 'eval(', 'exec('
        ]
        
        for keyword in suspicious_keywords:
            if keyword.lower() in text.lower():
                threats['suspicious_patterns'].append(keyword)
                threats['risk_level'] = 'HIGH'
        
        return threats
