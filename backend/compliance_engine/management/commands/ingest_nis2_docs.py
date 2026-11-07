"""
Ingest NIS2 EU documents into the Qdrant knowledge base.

    python manage.py ingest_nis2_docs
    python manage.py ingest_nis2_docs --docs-dir NIS2-EU-documents --language en --clear

Text extraction uses Docling when installed, otherwise falls back to
pdfplumber (which is always in requirements.txt). Without a populated
knowledge base the RAG step returns nothing and gap analysis has no
NIS2 context to compare against.
"""

import re
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from rag_engine.qdrant_client import NIS2QdrantClient


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> list[str]:
    """Split text into overlapping chunks, preferring sentence boundaries."""
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if end < len(text):
            last_period = chunk.rfind(". ")
            if last_period > chunk_size * 0.7:
                end = start + last_period + 1
                chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk.strip())
        start = max(end - overlap, start + 1)
    return chunks


def _detect_article(text: str) -> str | None:
    for pattern in (
        r"Article\s+(\d+(?:\.\d+)?)",
        r"Art\.\s+(\d+(?:\.\d+)?)",
        r"Artikel\s+(\d+(?:\.\d+)?)",
    ):
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return f"Article {match.group(1)}"
    return None


def _extract_pdf_text(pdf_path: Path) -> str:
    """Extract text with Docling if available, else pdfplumber."""
    try:
        from docling.document_converter import DocumentConverter

        result = DocumentConverter().convert(str(pdf_path))
        return result.document.export_to_markdown()
    except ImportError:
        import pdfplumber

        with pdfplumber.open(str(pdf_path)) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)


class Command(BaseCommand):
    help = "Ingest NIS2 PDF documents into the Qdrant vector database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--docs-dir",
            default=str(settings.BASE_DIR / "NIS2-EU-documents"),
            help="Directory containing NIS2 PDF files",
        )
        parser.add_argument("--chunk-size", type=int, default=800)
        parser.add_argument("--overlap", type=int, default=100)
        parser.add_argument("--language", default="en")
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete the existing collection before ingesting",
        )

    def handle(self, *args, **options):
        docs_dir = Path(options["docs_dir"])
        if not docs_dir.exists():
            raise CommandError(f"Directory not found: {docs_dir}")

        pdf_files = sorted(
            p for p in docs_dir.glob("*.pdf") if "(1)" not in p.name
        )
        if not pdf_files:
            raise CommandError(f"No PDF files found in {docs_dir}")

        self.stdout.write(f"Found {len(pdf_files)} PDF file(s)")

        qdrant = NIS2QdrantClient()
        if options["clear"]:
            self.stdout.write("Clearing existing collection...")
            qdrant.delete_collection()
            qdrant._ensure_collection()

        total_chunks = 0
        for pdf_file in pdf_files:
            self.stdout.write(f"Processing: {pdf_file.name}")
            try:
                full_text = _extract_pdf_text(pdf_file)
            except Exception as exc:  # noqa: BLE001
                self.stderr.write(self.style.ERROR(f"  extract failed: {exc}"))
                continue

            chunks = chunk_text(
                full_text, options["chunk_size"], options["overlap"]
            )
            self.stdout.write(f"  {len(chunks)} chunks")

            for i, chunk in enumerate(chunks):
                if len(chunk.strip()) < 50:
                    continue
                qdrant.add_document(
                    text=chunk,
                    metadata={
                        "source": "NIS2_DIRECTIVE",
                        "file": pdf_file.name,
                        "language": options["language"],
                        "chunk_index": i,
                        "article": _detect_article(chunk) or f"chunk_{i}",
                    },
                )
                total_chunks += 1

        info = qdrant.get_collection_info()
        points = getattr(info, "points_count", "?") if info else "?"
        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone: {total_chunks} chunks ingested — collection now has "
                f"{points} points"
            )
        )
