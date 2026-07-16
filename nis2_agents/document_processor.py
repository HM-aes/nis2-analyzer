"""
Document text extraction using Docling
Handles PDF, DOCX, PPTX, and other formats
"""
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Extract text from various document formats using Docling"""
    
    def __init__(self):
        """Initialize Docling converter"""
        try:
            from docling.document_converter import DocumentConverter
            self.converter = DocumentConverter()
            logger.info("Docling DocumentConverter initialized successfully")
        except ImportError as e:
            logger.error(f"Docling not installed: {e}")
            logger.error("Please run: pip install docling")
            self.converter = None
    
    def extract_text(self, file_path: str) -> Optional[str]:
        """
        Extract text from document using Docling
        
        Args:
            file_path: Path to the document
        
        Returns:
            Extracted text as markdown or None if extraction fails
        """
        if not self.converter:
            logger.error("Docling converter not available - please install docling")
            return None
        
        try:
            # Convert document with Docling
            result = self.converter.convert(file_path)
            
            # Export to markdown (clean, structured text)
            text = result.document.export_to_markdown()
            
            logger.info(f"Successfully extracted {len(text)} characters from {file_path}")
            return text
        
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            return None
    
    def extract_structured(self, file_path: str) -> Optional[Dict]:
        """
        Extract structured data from document
        
        Args:
            file_path: Path to the document
        
        Returns:
            JSON representation with layout, tables, etc.
        """
        if not self.converter:
            logger.error("Docling converter not available")
            return None
        
        try:
            result = self.converter.convert(file_path)
            return result.document.export_to_dict()
        
        except Exception as e:
            logger.error(f"Error extracting structured data: {e}")
            return None
    
    def get_page_count(self, file_path: str) -> int:
        """
        Get number of pages in document
        
        Args:
            file_path: Path to the document
        
        Returns:
            Number of pages or 0 if error
        """
        if not self.converter:
            return 0
        
        try:
            result = self.converter.convert(file_path)
            
            # Docling provides page information
            if hasattr(result.document, 'pages'):
                return len(result.document.pages)
            
            # Fallback: estimate from text length
            text = result.document.export_to_markdown()
            return max(1, len(text) // 3000)  # Rough estimate: 3000 chars per page
        
        except Exception as e:
            logger.error(f"Error getting page count: {e}")
            return 0
    
    def get_file_info(self, file_path: str) -> Dict:
        """
        Get comprehensive file information
        
        Args:
            file_path: Path to the document
        
        Returns:
            Dictionary with file metadata
        """
        info = {
            'text_extracted': False,
            'page_count': 0,
            'char_count': 0,
            'has_tables': False,
            'has_images': False
        }
        
        if not self.converter:
            return info
        
        try:
            result = self.converter.convert(file_path)
            text = result.document.export_to_markdown()
            
            info['text_extracted'] = True
            info['char_count'] = len(text)
            info['page_count'] = self.get_page_count(file_path)
            
            # Check for tables and images in markdown
            info['has_tables'] = '|' in text  # Markdown tables
            info['has_images'] = '![' in text  # Markdown images
            
        except Exception as e:
            logger.error(f"Error getting file info: {e}")
        
        return info
