import json
import os
import shutil
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse

from backend.config import settings
from backend.models.schemas import AnalysisResponse, ComplianceReport
from backend.core.intelligence_pipeline import ComplianceIntelligencePipeline
from backend.core.report_generator import ReportGenerator
from backend.core.gemini_client import GeminiClient

router = APIRouter(prefix="/api", tags=["Compliance Intelligence API"])
pipeline = ComplianceIntelligencePipeline()

# In-memory report cache for quick retrieval
REPORT_CACHE: dict[str, ComplianceReport] = {}

@router.get("/health")
async def health_check():
    """Returns system health, configuration, and model status."""
    has_env_key = bool(settings.GEMINI_API_KEY)
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION,
        "gemini_model": settings.DISPLAY_MODEL_NAME,
        "env_api_key_configured": has_env_key,
        "quota_shield_active": True,
        "local_nlp_engine_ready": True
    }

@router.get("/samples")
async def get_sample_documents():
    """Returns sample contract and compliance policy text and filenames."""
    sample_contract_txt = settings.SAMPLE_DIR / "sample_vendor_contract.txt"
    sample_policy_txt = settings.SAMPLE_DIR / "sample_compliance_policy.txt"
    
    contract_content = ""
    policy_content = ""
    
    if sample_contract_txt.exists():
        with open(sample_contract_txt, "r", encoding="utf-8") as f:
            contract_content = f.read()
            
    if sample_policy_txt.exists():
        with open(sample_policy_txt, "r", encoding="utf-8") as f:
            policy_content = f.read()

    return {
        "contract": {
            "filename": "sample_vendor_contract.pdf",
            "title": "Master Services Agreement (Apex Cloud Solutions LLC)",
            "content": contract_content
        },
        "policy": {
            "filename": "sample_compliance_policy.pdf",
            "title": "Enterprise Third-Party Compliance & Legal Risk Policy v4.2",
            "content": policy_content
        }
    }

@router.post("/test-key")
async def test_api_key(gemini_api_key: str = Form(...)):
    """Tests if a user-supplied Gemini API key is valid."""
    try:
        client = GeminiClient(api_key=gemini_api_key)
        if not client.is_configured():
            return {"valid": False, "message": "Failed to initialize Gemini client."}
        
        # Test with tiny prompt
        response = client.generate_json_response(
            "Return JSON: {\"status\": \"ok\", \"model\": \"gemini\"}"
        )
        return {
            "valid": True,
            "message": "Gemini API Key validated successfully!",
            "details": response
        }
    except Exception as e:
        return {
            "valid": False,
            "message": f"Gemini test call returned: {str(e)}",
            "shield_recommendation": "The system's built-in Quota Shield will automatically use the high-precision local engine so you can still run complete audits without error."
        }

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_documents(
    contract_file: Optional[UploadFile] = File(None),
    policy_file: Optional[UploadFile] = File(None),
    contract_text: Optional[str] = Form(None),
    policy_text: Optional[str] = Form(None),
    contract_name: Optional[str] = Form("Vendor Contract"),
    policy_name: Optional[str] = Form("Internal Compliance Policy"),
    gemini_api_key: Optional[str] = Form(None),
    model_name: Optional[str] = Form(None),
    force_fallback: Optional[bool] = Form(False)
):
    """Processes contract and policy documents and generates full compliance intelligence."""
    saved_files = []
    try:
        contract_path: Optional[Path] = None
        policy_path: Optional[Path] = None

        # Save uploaded contract file if present
        if contract_file and contract_file.filename:
            contract_path = settings.UPLOAD_DIR / contract_file.filename
            with open(contract_path, "wb") as buffer:
                shutil.copyfileobj(contract_file.file, buffer)
            saved_files.append(contract_path)
            contract_name = contract_file.filename

        # Save uploaded policy file if present
        if policy_file and policy_file.filename:
            policy_path = settings.UPLOAD_DIR / policy_file.filename
            with open(policy_path, "wb") as buffer:
                shutil.copyfileobj(policy_file.file, buffer)
            saved_files.append(policy_path)
            policy_name = policy_file.filename

        # If no files uploaded and no text provided, fall back to sample data
        if not contract_path and not contract_text:
            contract_path = settings.SAMPLE_DIR / "sample_vendor_contract.pdf"
            contract_name = "sample_vendor_contract.pdf"

        if not policy_path and not policy_text:
            policy_path = settings.SAMPLE_DIR / "sample_compliance_policy.pdf"
            policy_name = "sample_compliance_policy.pdf"

        # Run pipeline
        report = pipeline.run_analysis(
            contract_text=contract_text,
            policy_text=policy_text,
            contract_file=contract_path,
            policy_file=policy_path,
            contract_name=contract_name,
            policy_name=policy_name,
            gemini_api_key=gemini_api_key,
            model_name=model_name or settings.DISPLAY_MODEL_NAME,
            force_fallback=bool(force_fallback)
        )

        # Cache report and persist JSON & PDF
        REPORT_CACHE[report.report_id] = report
        ReportGenerator.save_json_report(report)
        ReportGenerator.generate_pdf_report(report)

        return AnalysisResponse(
            success=True,
            message="Compliance intelligence successfully generated.",
            report=report
        )

    except Exception as e:
        # Emergency safeguard: Never leave user stranded with 500 error
        return AnalysisResponse(
            success=False,
            message=f"Analysis encountered an issue: {str(e)}",
            error=str(e)
        )
    finally:
        # Clean up temporary uploaded files (leaving samples intact)
        for p in saved_files:
            try:
                if p.exists() and "sample_data" not in str(p):
                    p.unlink(missing_ok=True)
            except Exception:
                pass

@router.get("/reports/{report_id}")
async def get_report_json(report_id: str):
    """Retrieves cached or stored JSON compliance report."""
    if report_id in REPORT_CACHE:
        return REPORT_CACHE[report_id]

    json_path = settings.REPORTS_DIR / f"{report_id}.json"
    if json_path.exists():
        report = ComplianceReport.model_validate_json(json_path.read_text(encoding="utf-8"))
        return JSONResponse(content=report.model_dump(mode="json"))

    raise HTTPException(status_code=404, detail="Compliance report not found.")

@router.get("/reports/{report_id}/pdf")
async def download_report_pdf(report_id: str):
    """Downloads the official executive PDF compliance audit report."""
    report = REPORT_CACHE.get(report_id)
    if report is None:
        json_path = settings.REPORTS_DIR / f"{report_id}.json"
        if not json_path.exists():
            raise HTTPException(status_code=404, detail="PDF report not found.")
        report = ComplianceReport.model_validate_json(json_path.read_text(encoding="utf-8"))

    pdf_path = ReportGenerator.generate_pdf_report(report)

    return FileResponse(
        path=pdf_path,
        filename=f"Compliance_Intelligence_Audit_{report_id}.pdf",
        media_type="application/pdf"
    )
