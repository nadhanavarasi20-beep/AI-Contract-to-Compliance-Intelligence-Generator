import re
from pathlib import Path
from typing import List, Dict, Any, Tuple
import pypdf

class DocumentProcessor:
    """Parses PDF and plain text documents into clean, structured text with page tracking."""

    @staticmethod
    def extract_text_from_pdf(pdf_path: Path) -> List[Dict[str, Any]]:
        """Extracts text page-by-page from a PDF file."""
        pages = []
        try:
            reader = pypdf.PdfReader(str(pdf_path))
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                cleaned = DocumentProcessor.clean_text(page_text)
                if cleaned.strip():
                    pages.append({
                        "page_number": i + 1,
                        "text": cleaned
                    })
        except Exception as e:
            raise RuntimeError(f"Failed to extract text from PDF '{pdf_path.name}': {str(e)}")
            
        if not pages:
            pages.append({"page_number": 1, "text": "[Empty Document or Scanned Image PDF]"})
            
        return pages

    @staticmethod
    def extract_text_from_raw_string(text: str, doc_name: str = "Document") -> List[Dict[str, Any]]:
        """Parses raw text string, simulating pages if length is significant."""
        cleaned = DocumentProcessor.clean_text(text)
        # Approximate 3000 chars per page
        chunk_size = 3000
        if len(cleaned) <= chunk_size:
            return [{"page_number": 1, "text": cleaned}]
            
        pages = []
        chunks = [cleaned[i:i + chunk_size] for i in range(0, len(cleaned), chunk_size)]
        for i, chunk in enumerate(chunks):
            pages.append({
                "page_number": i + 1,
                "text": chunk.strip()
            })
        return pages

    @staticmethod
    def extract_from_file(file_path: Path) -> Tuple[List[Dict[str, Any]], str]:
        """Loads a file (.pdf, .txt, .md) and returns page structures and combined text."""
        ext = file_path.suffix.lower()
        if ext == ".pdf":
            pages = DocumentProcessor.extract_text_from_pdf(file_path)
        else:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            pages = DocumentProcessor.extract_text_from_raw_string(content, file_path.name)
            
        combined_text = "\n\n".join([p["text"] for p in pages])
        return pages, combined_text

    @staticmethod
    def clean_text(raw_text: str) -> str:
        """Removes excessive whitespace and standardizes formatting."""
        if not raw_text:
            return ""
        # Standardize newlines
        text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
        # Replace non-breaking spaces & tabs
        text = text.replace("\u00a0", " ").replace("\t", "    ")
        # Remove repeated hyphens or underscores
        text = re.sub(r'[-_]{4,}', '', text)
        # Standardize multiple blank lines
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()
