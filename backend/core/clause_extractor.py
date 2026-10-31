import re
from typing import List, Dict, Any
from backend.models.schemas import Clause

class ClauseExtractor:
    """Splits contracts and policy documents into discrete clauses with section numbers and titles."""

    # Regex patterns for section headers
    HEADER_PATTERNS = [
        # SECTION 1. / Section 1.1 / Section 1.1.1
        re.compile(r'^(?:SECTION|Section|ARTICLE|Article|Clause|CLAUSE)\s+([0-9IVXLCDM]+(?:\.[0-9]+)*)[:.]?\s*(.*?)$', re.MULTILINE),
        # 1. / 1.1 / 1.1.1 followed by uppercase/titlecase title
        re.compile(r'^([0-9]+(?:\.[0-9]+)+)[:.]?\s+([A-Z][A-Za-z0-9 ,/\-&()]{2,60})$', re.MULTILINE),
        # 1. DEFINITIONS (pure number with uppercase words)
        re.compile(r'^([0-9]+)\.\s+([A-Z0-9\s,/\-&()]{3,60})$', re.MULTILINE),
        # Standalone uppercase legal heading (e.g., LIMITATION OF LIABILITY)
        re.compile(r'^([A-Z\s]{4,50})$', re.MULTILINE),
    ]

    @staticmethod
    def extract_clauses(pages: List[Dict[str, Any]], document_type: str = "contract") -> List[Clause]:
        """Extracts individual clauses from page list, preserving page citations."""
        clauses: List[Clause] = []
        
        # Build global text with page boundary markers
        full_text = ""
        page_offsets = [] # (start_char, end_char, page_number)
        
        current_offset = 0
        for p in pages:
            text = p["text"]
            start = current_offset
            full_text += text + "\n\n"
            current_offset = len(full_text)
            page_offsets.append((start, current_offset, p["page_number"]))

        def find_page_for_offset(offset: int) -> int:
            for start, end, page_num in page_offsets:
                if start <= offset <= end:
                    return page_num
            return 1

        # Look for section headings
        lines = full_text.split("\n")
        detected_sections = []
        char_counter = 0

        for line_idx, line in enumerate(lines):
            line_stripped = line.strip()
            line_start = char_counter
            char_counter += len(line) + 1 # +1 for newline

            if not line_stripped or len(line_stripped) > 80:
                continue

            # Check patterns
            matched = False
            for pattern in ClauseExtractor.HEADER_PATTERNS:
                match = pattern.match(line_stripped)
                if match:
                    groups = match.groups()
                    if len(groups) == 2:
                        sec_num = groups[0].strip()
                        sec_title = groups[1].strip() or f"Section {sec_num}"
                    else:
                        sec_num = f"Sec-{len(detected_sections)+1}"
                        sec_title = groups[0].strip()

                    detected_sections.append({
                        "section_num": sec_num,
                        "title": sec_title,
                        "line_idx": line_idx,
                        "char_offset": line_start,
                        "page": find_page_for_offset(line_start)
                    })
                    matched = True
                    break

        # If too few sections detected, fall back to paragraph block splitting
        if len(detected_sections) < 2:
            return ClauseExtractor._fallback_chunking(lines, full_text, find_page_for_offset, document_type)

        # Slice text between detected sections
        for idx, sec in enumerate(detected_sections):
            start_line = sec["line_idx"]
            end_line = detected_sections[idx + 1]["line_idx"] if idx + 1 < len(detected_sections) else len(lines)
            
            clause_lines = lines[start_line:end_line]
            clause_body = "\n".join(clause_lines).strip()
            
            # Clean up title if it's the first line
            body_without_title = "\n".join(clause_lines[1:]).strip() if len(clause_lines) > 1 else clause_body

            clauses.append(Clause(
                clause_id=f"{document_type}_clause_{idx+1}",
                document_type=document_type,
                section_num=sec["section_num"],
                title=sec["title"],
                text=body_without_title or clause_body,
                page=sec["page"],
                char_count=len(body_without_title or clause_body)
            ))

        return clauses

    @staticmethod
    def _fallback_chunking(lines: List[str], full_text: str, find_page_fn, document_type: str) -> List[Clause]:
        """Splits text into chunks of paragraphs when explicit section headers are absent."""
        clauses = []
        paragraphs = full_text.split("\n\n")
        chunk_idx = 1
        current_offset = 0

        for para in paragraphs:
            para_clean = para.strip()
            if len(para_clean) < 40:
                current_offset += len(para) + 2
                continue

            first_line = para_clean.split("\n")[0][:40]
            title = first_line.rstrip(".:-")
            page_num = find_page_fn(current_offset)

            clauses.append(Clause(
                clause_id=f"{document_type}_clause_{chunk_idx}",
                document_type=document_type,
                section_num=f"Para {chunk_idx}",
                title=title or f"Clause {chunk_idx}",
                text=para_clean,
                page=page_num,
                char_count=len(para_clean)
            ))
            chunk_idx += 1
            current_offset += len(para) + 2

        return clauses
