from app.core.state import ClaimState, Decision
from app.agents.gatekeeper import GatekeeperAgent
from app.agents.extractor import ExtractionAgent
from app.engine.adjudicator import PolicyEngine

class ClaimOrchestrator:
    def __init__(self):
        self.gatekeeper = GatekeeperAgent()
        self.extractor = ExtractionAgent()
        self.engine = PolicyEngine()

    async def process_claim(self, state: ClaimState, raw_files: dict) -> dict:
        state.log("Orchestrator", "Start", "SUCCESS", f"Processing claim for {state.patient_name}")

        # Phase 1: Gatekeeper
        try:
            if not await self.gatekeeper.validate_documents(state, raw_files):
                state.decision = Decision.HALTED
                return state.model_dump()
        except Exception as e:
            state.log("Gatekeeper", "Error", "FAILED", str(e))
            state.degrade_confidence(0.5, "Gatekeeper failure.")

        # Phase 2: Extraction & Failover
        if state.simulate_component_failure:
            state.log("Extractor", "Component Crash", "FAILED", "Simulated extraction component failure mid-processing.")
            state.degrade_confidence(0.4, "Component failed. Proceeding with degraded data.")
            state.rejection_reasons.append("SYSTEM NOTE: Processing pipeline degraded. Manual review recommended.")
        else:
            for doc in state.documents:
                if doc.is_valid:
                    try:
                        doc.extracted_data = await self.extractor.extract(doc, raw_files[doc.file_id])
                        state.log("Extractor", f"Extracted {doc.file_name}", "SUCCESS", "Entities extracted.")
                    except Exception as e:
                        state.log("Extractor", "API Timeout", "WARNING", f"Failed extraction for {doc.file_name}")
                        state.degrade_confidence(0.2, "Timeout during extraction.")

        # Phase 3: Verifier
        extracted_names = set()
        for doc in state.documents:
            n = doc.extracted_data.get("patient_name")
            if n: extracted_names.add(str(n).lower().strip())
            
        if len(extracted_names) > 1:
            state.log("Verifier", "Patient Mismatch", "FAILED", f"Names found: {', '.join(extracted_names)}")
            state.rejection_reasons.append(f"Document mismatch (TC003). Found names: {', '.join(extracted_names)}. Ensure all docs belong to {state.patient_name}.")
            state.decision = Decision.HALTED
            return state.model_dump()
            
        if extracted_names:
            first_name = state.patient_name.split()[0].lower()
            match_found = any(first_name in ex_name for ex_name in extracted_names)
            if not match_found:
                state.log("Verifier", "Name Mismatch", "WARNING", f"Expected {state.patient_name}, got {extracted_names}")
                state.degrade_confidence(0.2, "Document patient name does not exactly match policy member name.")

        # Phase 4: Adjudication
        self.engine.evaluate(state)
        return state.model_dump()
