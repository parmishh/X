from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from typing import List
import uuid
from app.core.state import ClaimState, ExtractedDocument
from app.orchestrator import ClaimOrchestrator

app = FastAPI(title="Plum Claims Orchestrator")
orchestrator = ClaimOrchestrator()

@app.post("/api/v2/process-claim")
async def process_claim_endpoint(
    member_id: str = Form(...),
    patient_id: str = Form(...),
    patient_name: str = Form(...),
    claim_category: str = Form(...),
    treatment_date: str = Form(...),
    claimed_amount: float = Form(...),
    expected_doc_types: str = Form(...),
    simulate_component_failure: bool = Form(False),
    enable_ai_forgery_check: bool = Form(False),
    files: List[UploadFile] = File(...)
):
    print(f"\n🚀 [API HIT] Received claim request for Member: {member_id}, Patient: {patient_name}")
    
    raw_files = {}
    doc_types = [t.strip() for t in expected_doc_types.split(",")]
    
    initial_documents = []
    for i, file in enumerate(files):
        file_id = f"F_{uuid.uuid4().hex[:8]}"
        raw_files[file_id] = await file.read()
        initial_documents.append(ExtractedDocument(file_id=file_id, file_name=file.filename, required_type=doc_types[i]))

    state = ClaimState(
        claim_id=f"CLM_{uuid.uuid4().hex[:8].upper()}",
        member_id=member_id,
        patient_id=patient_id,
        patient_name=patient_name,
        policy_id="PLUM_GHI_2024",
        claim_category=claim_category,
        treatment_date=treatment_date,
        claimed_amount=claimed_amount,
        documents=initial_documents,
        simulate_component_failure=simulate_component_failure,
        enable_ai_forgery_check=enable_ai_forgery_check
    )

    return await orchestrator.process_claim(state, raw_files)
