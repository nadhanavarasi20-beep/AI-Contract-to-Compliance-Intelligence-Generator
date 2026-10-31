from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class SourceCitation(BaseModel):
    document_name: str = Field(..., description="Source document name, e.g. Contract or Policy")
    section_number: str = Field(..., description="Section number e.g. '4.1' or 'Clause 7'")
    section_title: str = Field(..., description="Section title or heading")
    page_number: int = Field(1, description="Page number where the text appears")
    snippet: str = Field(..., description="Direct verbatim excerpt or quotation from the document")

class Clause(BaseModel):
    clause_id: str
    document_type: str = Field(..., description="'contract' or 'policy'")
    section_num: str
    title: str
    text: str
    page: int = 1
    char_count: int = 0

class Obligation(BaseModel):
    id: str
    party: str = Field("Vendor", description="Responsible party: 'Vendor', 'Client', or 'Mutual'")
    duty_summary: str = Field(..., description="Concise statement of the affirmative duty or requirement")
    obligation_type: str = Field("Operational", description="Category: e.g. Operational, Financial, Security, Reporting")
    priority: str = Field("High", description="'High', 'Medium', or 'Low'")
    citation: SourceCitation

class Deadline(BaseModel):
    id: str
    date_or_period: str = Field(..., description="e.g. 'Net 60 days', '90 days prior', 'within 24 hours'")
    deadline_type: str = Field(..., description="'Renewal', 'Notice Window', 'Payment Due', 'Cure Period', 'Breach Notification'")
    description: str
    trigger_event: str = Field(..., description="What event triggers this deadline")
    citation: SourceCitation

class RiskItem(BaseModel):
    id: str
    severity: str = Field(..., description="'High', 'Medium', or 'Low'")
    category: str = Field(..., description="'Liability', 'Data Privacy', 'IP Rights', 'Financial', 'Termination', 'Compliance'")
    risk_title: str
    rationale: str = Field(..., description="Why this clause poses legal or operational vulnerability")
    contract_clause_title: str
    recommendation: str = Field(..., description="Immediate redline or negotiation advice")
    citation: SourceCitation

class PolicyComparisonItem(BaseModel):
    policy_requirement_id: str
    policy_section: str
    policy_title: str
    policy_rule: str
    status: str = Field(..., description="'Compliant', 'Non-Compliant', 'Partially Compliant', or 'Missing'")
    contract_finding: str
    gap_analysis: str
    contract_citation: Optional[SourceCitation] = None
    policy_citation: SourceCitation

class MissingClause(BaseModel):
    id: str
    required_clause_name: str
    policy_source_section: str
    risk_level: str = Field("High", description="'High', 'Medium', 'Low'")
    description: str = Field(..., description="What is omitted and why it creates non-compliance")
    suggested_redline_text: str = Field(..., description="Suggested clause text to insert into contract")
    policy_citation: SourceCitation

class RecommendationItem(BaseModel):
    id: str
    priority: str = Field(..., description="'Immediate Action', 'Recommended Redline', or 'Negotiation Point'")
    target: str = Field(..., description="'Risk Mitigation', 'Missing Clause', or 'Policy Alignment'")
    title: str
    suggested_action: str
    draft_clause_text: Optional[str] = None

class ComplianceReport(BaseModel):
    report_id: str
    title: str = "Contract-to-Compliance Intelligence Report"
    contract_name: str
    policy_name: str
    engine_name: str = "Gemini-3.8-Flash (Hybrid Resilience Engine)"
    is_fallback_active: bool = False
    fallback_reason: Optional[str] = None
    
    compliance_score: float = Field(..., description="Overall score from 0.0 to 100.0")
    grade: str = Field("B", description="A, B, C, D, or F")
    executive_summary: str
    
    risk_breakdown: Dict[str, int] = Field(default_factory=dict)
    compliance_breakdown: Dict[str, int] = Field(default_factory=dict)
    
    obligations: List[Obligation] = Field(default_factory=list)
    deadlines: List[Deadline] = Field(default_factory=list)
    risks: List[RiskItem] = Field(default_factory=list)
    policy_comparisons: List[PolicyComparisonItem] = Field(default_factory=list)
    missing_clauses: List[MissingClause] = Field(default_factory=list)
    recommendations: List[RecommendationItem] = Field(default_factory=list)
    
    contract_clauses: List[Clause] = Field(default_factory=list)
    policy_clauses: List[Clause] = Field(default_factory=list)

class AnalysisRequest(BaseModel):
    contract_text: Optional[str] = None
    policy_text: Optional[str] = None
    contract_name: Optional[str] = "Vendor Contract"
    policy_name: Optional[str] = "Internal Compliance Policy"
    gemini_api_key: Optional[str] = None
    model_name: Optional[str] = "gemini-2.5-flash"
    force_fallback: bool = False

class AnalysisResponse(BaseModel):
    success: bool
    message: str
    report: Optional[ComplianceReport] = None
    error: Optional[str] = None
