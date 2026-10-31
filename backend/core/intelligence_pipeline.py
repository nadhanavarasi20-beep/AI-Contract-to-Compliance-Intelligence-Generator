import logging
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path

from backend.config import settings
from backend.models.schemas import (
    Clause,
    ComplianceReport,
    AnalysisRequest,
    AnalysisResponse,
    SourceCitation,
    Obligation,
    Deadline,
    RiskItem,
    PolicyComparisonItem,
    MissingClause,
    RecommendationItem
)
from backend.core.document_processor import DocumentProcessor
from backend.core.clause_extractor import ClauseExtractor
from backend.core.rag_engine import RAGEngine
from backend.core.gemini_client import GeminiClient, GeminiQuotaExhaustedError, GeminiAPIError
from backend.core.fallback_engine import FallbackEngine

logger = logging.getLogger("compliance_intelligence")

class ComplianceIntelligencePipeline:
    """Master Pipeline orchestrating the 10 modular legal GenAI components."""

    def __init__(self):
        self.rag = RAGEngine()
        self.fallback = FallbackEngine(self.rag)

    def run_analysis(
        self,
        contract_text: Optional[str] = None,
        policy_text: Optional[str] = None,
        contract_file: Optional[Path] = None,
        policy_file: Optional[Path] = None,
        contract_name: str = "Vendor Contract",
        policy_name: str = "Corporate Compliance Policy",
        gemini_api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        force_fallback: bool = False
    ) -> ComplianceReport:
        """Executes full pipeline across documents."""

        # Step 1: Document Processing (PDF / Plain text)
        if contract_file and contract_file.exists():
            contract_pages, _ = DocumentProcessor.extract_from_file(contract_file)
            contract_name = contract_file.name
        elif contract_text:
            contract_pages = DocumentProcessor.extract_text_from_raw_string(contract_text, contract_name)
        else:
            raise ValueError("No contract document or text provided.")

        if policy_file and policy_file.exists():
            policy_pages, _ = DocumentProcessor.extract_from_file(policy_file)
            policy_name = policy_file.name
        elif policy_text:
            policy_pages = DocumentProcessor.extract_text_from_raw_string(policy_text, policy_name)
        else:
            raise ValueError("No compliance policy document or text provided.")

        # Step 2: Clause Extraction
        contract_clauses = ClauseExtractor.extract_clauses(contract_pages, document_type="contract")
        policy_clauses = ClauseExtractor.extract_clauses(policy_pages, document_type="policy")

        # Step 3: RAG Vector Store Indexing
        self.rag.index_documents(contract_clauses, policy_clauses)

        # Check if we should execute via Gemini LLM or Local High-Precision Engine
        api_key = gemini_api_key or settings.GEMINI_API_KEY
        should_try_gemini = bool(api_key and not force_fallback)

        if should_try_gemini:
            try:
                gemini_client = GeminiClient(api_key=api_key, model_name=model_name or settings.DISPLAY_MODEL_NAME)
                if gemini_client.is_configured():
                    report = self._run_gemini_analysis(
                        gemini_client=gemini_client,
                        contract_name=contract_name,
                        policy_name=policy_name,
                        contract_clauses=contract_clauses,
                        policy_clauses=policy_clauses
                    )
                    return report
            except (GeminiQuotaExhaustedError, GeminiAPIError, Exception) as exc:
                logger.warning(f"Gemini API invocation shifted to fallback engine: {str(exc)}")
                # Quota Shield: Transparently fallback to local engine with clear status flag
                reason = f"Gemini API Quota/Offline Shield Active: {type(exc).__name__} ({str(exc)[:120]})"
                return self.fallback.execute_intelligence_analysis(
                    contract_name=contract_name,
                    policy_name=policy_name,
                    contract_clauses=contract_clauses,
                    policy_clauses=policy_clauses,
                    reason_label=reason
                )

        # Fallback Engine (Zero Quota, Offline, High-Precision)
        return self.fallback.execute_intelligence_analysis(
            contract_name=contract_name,
            policy_name=policy_name,
            contract_clauses=contract_clauses,
            policy_clauses=policy_clauses,
            reason_label="Deterministic Offline Compliance Intelligence Engine Active"
        )

    def _run_gemini_analysis(
        self,
        gemini_client: GeminiClient,
        contract_name: str,
        policy_name: str,
        contract_clauses: List[Clause],
        policy_clauses: List[Clause]
    ) -> ComplianceReport:
        """Synthesizes compliance intelligence using Gemini LLM with single-pass prompt."""

        contract_summary = "\n\n".join([
            f"[Clause {c.section_num} - {c.title} (Page {c.page})]\n{c.text[:500]}"
            for c in contract_clauses[:15]
        ])

        policy_summary = "\n\n".join([
            f"[Policy Sec {p.section_num} - {p.title}]\n{p.text[:400]}"
            for p in policy_clauses[:10]
        ])

        prompt = f"""You are an elite Legal & Compliance GenAI Specialist. Analyze the following Contract against the Compliance Policy.
Generate a comprehensive, structured JSON report matching the specified schema.

CONTRACT ({contract_name}):
{contract_summary}

INTERNAL COMPLIANCE POLICY ({policy_name}):
{policy_summary}

Respond with ONLY valid JSON adhering to this exact structure:
{{
  "compliance_score": 72.5,
  "grade": "C",
  "executive_summary": "Concise 3-4 sentence audit summary...",
  "risk_breakdown": {{"high": 2, "medium": 3, "low": 1}},
  "compliance_breakdown": {{"compliant": 3, "non_compliant": 2, "partially_compliant": 1, "missing": 2}},
  "obligations": [
    {{
      "id": "OBL-001",
      "party": "Vendor",
      "duty_summary": "Vendor must maintain 99.9% uptime",
      "obligation_type": "Operational",
      "priority": "High",
      "citation": {{
        "document_name": "{contract_name}",
        "section_number": "3.1",
        "section_title": "Service Levels",
        "page_number": 1,
        "snippet": "Verbatim quote from contract..."
      }}
    }}
  ],
  "deadlines": [
    {{
      "id": "DLN-001",
      "date_or_period": "Net 60 days",
      "deadline_type": "Payment Due",
      "description": "Client must pay invoices within 60 days",
      "trigger_event": "Invoice Receipt",
      "citation": {{
        "document_name": "{contract_name}",
        "section_number": "2.2",
        "section_title": "Fees and Invoicing",
        "page_number": 1,
        "snippet": "Verbatim quote..."
      }}
    }}
  ],
  "risks": [
    {{
      "id": "RSK-001",
      "severity": "High",
      "category": "Liability",
      "risk_title": "Onerous 1-month liability limit",
      "rationale": "Leaves enterprise exposed to major damages",
      "contract_clause_title": "Limitation of Liability",
      "recommendation": "Redline to 12 months minimum",
      "citation": {{
        "document_name": "{contract_name}",
        "section_number": "4.1",
        "section_title": "Limitation of Liability",
        "page_number": 1,
        "snippet": "Verbatim quote..."
      }}
    }}
  ],
  "policy_comparisons": [
    {{
      "policy_requirement_id": "POL-01",
      "policy_section": "1.1",
      "policy_title": "Data Breach Notification",
      "policy_rule": "Mandatory 24h notice",
      "status": "Non-Compliant",
      "contract_finding": "Contract allows 7 days",
      "gap_analysis": "Discrepancy of 6 days violates GDPR and enterprise policy",
      "policy_citation": {{
        "document_name": "{policy_name}",
        "section_number": "1.1",
        "section_title": "Incident Notification",
        "page_number": 1,
        "snippet": "Vendor shall notify within 24 hours..."
      }}
    }}
  ],
  "missing_clauses": [
    {{
      "id": "MIS-001",
      "required_clause_name": "SOC 2 Type II Annual Audit",
      "policy_source_section": "2.3",
      "risk_level": "High",
      "description": "Contract lacks security audit right",
      "suggested_redline_text": "Vendor agrees to provide annual SOC 2 Type II audit report...",
      "policy_citation": {{
        "document_name": "{policy_name}",
        "section_number": "2.3",
        "section_title": "Security Audits",
        "page_number": 1,
        "snippet": "Audit compliance mandate..."
      }}
    }}
  ],
  "recommendations": [
    {{
      "id": "REC-001",
      "priority": "Immediate Action",
      "target": "Risk Mitigation",
      "title": "Redline Liability Cap",
      "suggested_action": "Increase liability cap to 12 months aggregate fees",
      "draft_clause_text": "Aggregate liability shall not exceed fees paid in past 12 months."
    }}
  ]
}}"""

        data = gemini_client.generate_json_response(prompt)
        
        # Parse into Pydantic models
        obligations = [Obligation(**o) for o in data.get("obligations", [])]
        deadlines = [Deadline(**d) for d in data.get("deadlines", [])]
        risks = [RiskItem(**r) for r in data.get("risks", [])]
        policy_comparisons = [PolicyComparisonItem(**p) for p in data.get("policy_comparisons", [])]
        missing_clauses = [MissingClause(**m) for m in data.get("missing_clauses", [])]
        recommendations = [RecommendationItem(**rec) for rec in data.get("recommendations", [])]

        return ComplianceReport(
            report_id=f"REP-{abs(hash(contract_name + policy_name)) % 1000000:06d}",
            title="Contract-to-Compliance Intelligence Report",
            contract_name=contract_name,
            policy_name=policy_name,
            engine_name=f"{settings.DISPLAY_MODEL_NAME} (Active GenAI)",
            is_fallback_active=False,
            compliance_score=float(data.get("compliance_score", 75.0)),
            grade=str(data.get("grade", "B")),
            executive_summary=str(data.get("executive_summary", "Audit completed successfully.")),
            risk_breakdown=data.get("risk_breakdown", {}),
            compliance_breakdown=data.get("compliance_breakdown", {}),
            obligations=obligations,
            deadlines=deadlines,
            risks=risks,
            policy_comparisons=policy_comparisons,
            missing_clauses=missing_clauses,
            recommendations=recommendations,
            contract_clauses=contract_clauses,
            policy_clauses=policy_clauses
        )
