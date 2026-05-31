from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

class Decision(str, Enum):
    APPROVED = "APPROVED"
    PARTIAL = "PARTIAL"
    REJECTED = "REJECTED"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    PENDING = "PENDING"
    HALTED = "HALTED" 

class TraceStep(BaseModel):
    component: str
    action: str
    status: str
    details: str

class ExtractedDocument(BaseModel):
    file_id: str
    file_name: str
    actual_type: str = "UNKNOWN"
    required_type: str
    is_valid: bool = False
    is_ai_forged: bool = False
    extracted_data: Dict[str, Any] = {}

class ClaimState(BaseModel):
    claim_id: str
    member_id: str 
    patient_id: str 
    patient_name: str
    policy_id: str
    claim_category: str
    treatment_date: str
    claimed_amount: float
    documents: List[ExtractedDocument] = []
    
    simulate_component_failure: bool = False
    enable_ai_forgery_check: bool = False
    
    decision: Decision = Decision.PENDING
    approved_amount: float = 0.0
    rejection_reasons: List[str] = []
    confidence_score: float = 1.0
    trace_log: List[TraceStep] = []

    def log(self, component: str, action: str, status: str, details: str):
        self.trace_log.append(TraceStep(component=component, action=action, status=status, details=details))
        
    def degrade_confidence(self, penalty: float, reason: str):
        self.confidence_score = max(0.0, round(self.confidence_score - penalty, 2))
        if self.decision not in [Decision.REJECTED, Decision.HALTED]:
            self.decision = Decision.MANUAL_REVIEW
        self.log("System", "Confidence Penalty", "WARNING", f"Reduced by {penalty}: {reason}")