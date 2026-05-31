import re
from app.core.state import ClaimState
from app.agents.base import BaseAgent

class VerificationAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        
        # Regex pattern matching Indian Medical Registration Formats
        # Matches: KA/45678/2015, MH/23456/2018, AYUR/KL/2345/2019, etc.
        self.reg_no_pattern = re.compile(r"^([A-Z]{2}|AYUR/[A-Z]{2})/\d{4,6}/\d{4}$", re.IGNORECASE)

    async def check_consistency(self, state: ClaimState) -> bool:
        """
        Cross-checks entities across extracted documents to detect mismatches and validates critical formatting.
        """
        patient_names = set()
        invalid_reg_numbers = []
        
        for doc in state.documents:
            if doc.is_valid and doc.extracted_data:
                # 1. Gather patient names for cross-checking
                name = doc.extracted_data.get("patient_name")
                if name and isinstance(name, str):
                    patient_names.add(name.lower().strip())
                
                # 2. Validate Doctor Registration Number (if present)
                reg_no = doc.extracted_data.get("doctor_registration_number")
                if reg_no and isinstance(reg_no, str):
                    # Clean up spaces that OCR might have accidentally added
                    clean_reg_no = reg_no.replace(" ", "").upper()
                    if not self.reg_no_pattern.match(clean_reg_no):
                        invalid_reg_numbers.append(f"{doc.file_name}: '{reg_no}'")

        # Check 1: Patient Name Mismatch (TC003)
        if len(patient_names) > 1:
            state.log(
                "VerificationAgent", 
                "Patient Name Mismatch", 
                "FAILED", 
                f"Conflicting names detected across documents: {', '.join(patient_names)}."
            )
            state.rejection_reasons.append(
                f"Document mismatch detected. We found multiple patient names ({', '.join(patient_names)}) "
                "across your uploads. Please ensure all documents belong to the same patient."
            )
            state.degrade_confidence(0.4, "Cross-document verification failed due to name mismatch.")
            return False
            
        # Check 2: Invalid Doctor Registration Number Format
        if invalid_reg_numbers:
            state.log(
                "VerificationAgent",
                "Registration Format Check",
                "WARNING",
                f"Suspicious doctor registration numbers found: {', '.join(invalid_reg_numbers)}"
            )
            # We don't hard reject for this (because handwriting can be messy), but we flag it for manual review
            state.degrade_confidence(0.15, "Possible invalid or misread doctor registration number.")

        state.log("VerificationAgent", "Consistency Check", "SUCCESS", "All cross-document validations passed.")
        return True