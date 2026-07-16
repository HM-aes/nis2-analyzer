#!/usr/bin/env python
"""
Ingest NIS2 EU documents into Qdrant using Docling
Processes PDFs from sample_docs/NIS2-EU-documents/
"""
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nis2_analyzer.settings')
import django
django.setup()

from rag_engine.qdrant_client import NIS2QdrantClient
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> list:
    """
    Split text into overlapping chunks
    
    Args:
        text: Text to chunk
        chunk_size: Target size of each chunk
        overlap: Number of characters to overlap between chunks
    
    Returns:
        List of text chunks
    """
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        
        # Try to break at sentence boundary
        if end < len(text):
            last_period = chunk.rfind('.')
            if last_period > chunk_size * 0.7:  # At least 70% of chunk
                end = start + last_period + 1
                chunk = text[start:end]
        
        if chunk.strip():
            chunks.append(chunk.strip())
        
        start = end - overlap
    
    return chunks


def ingest_nis2_documents():
    """Ingest all NIS2 documents from sample_docs/NIS2-EU-documents/"""
    
    docs_dir = Path(__file__).parent.parent / 'sample_docs' / 'NIS2-EU-documents'
    
    if not docs_dir.exists():
        logger.error(f"Directory not found: {docs_dir}")
        return
    
    # Initialize Docling and Qdrant
    try:
        from docling.document_converter import DocumentConverter
        converter = DocumentConverter()
        logger.info("Docling converter initialized")
    except ImportError as e:
        logger.error(f"Docling not installed: {e}")
        logger.error("Please run: pip install docling")
        return
    
    qdrant = NIS2QdrantClient()
    
    # Get all PDF files
    pdf_files = list(docs_dir.glob('*.pdf'))
    logger.info(f"Found {len(pdf_files)} PDF files to process")
    
    if not pdf_files:
        logger.warning("No PDF files found in sample_docs/NIS2-EU-documents/")
        return
    
    total_chunks = 0
    
    for pdf_file in pdf_files:
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing: {pdf_file.name}")
        logger.info(f"{'='*60}")
        
        try:
            # Extract text with Docling
            logger.info("Extracting text with Docling...")
            result = converter.convert(str(pdf_file))
            text = result.document.export_to_markdown()
            
            logger.info(f"✓ Extracted {len(text):,} characters from {pdf_file.name}")
            
            # Chunk the text
            chunks = chunk_text(text, chunk_size=800, overlap=100)
            logger.info(f"✓ Created {len(chunks)} chunks")
            
            # Upload to Qdrant
            logger.info("Uploading to Qdrant...")
            for i, chunk in enumerate(chunks):
                metadata = {
                    'source': pdf_file.name,
                    'chunk_index': i,
                    'total_chunks': len(chunks),
                    'language': 'en',  # NIS2 directive is in English
                    'document_type': 'regulation',
                    'category': 'nis2_directive'
                }
                
                point_id = qdrant.add_document(chunk, metadata)
                total_chunks += 1
                
                if (i + 1) % 50 == 0:
                    logger.info(f"  Uploaded {i + 1}/{len(chunks)} chunks")
            
            logger.info(f"✅ Completed {pdf_file.name} - {len(chunks)} chunks uploaded")
        
        except Exception as e:
            logger.error(f"❌ Error processing {pdf_file.name}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    logger.info(f"\n{'='*60}")
    logger.info(f"🎉 Ingestion complete!")
    logger.info(f"{'='*60}")
    logger.info(f"Total chunks uploaded: {total_chunks}")
    
    # Verify
    info = qdrant.get_collection_info()
    if info:
        logger.info(f"Collection '{qdrant.collection_name}' now has {info.points_count} points")
    
    logger.info("\n✓ NIS2 knowledge base is ready for RAG queries!")


if __name__ == '__main__':
    logger.info("NIS2 Document Ingestion Script")
    logger.info("=" * 60)
    ingest_nis2_documents()
