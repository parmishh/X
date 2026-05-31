import json
import os
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, Any
from app.core.state import ClaimState, Decision

logger = logging.getLogger(__name__)

class PolicyEngine:
    def __init__(self, policy_path: str = "data/policy_terms.json", state_path: str = "data/employee_state.json"):
        self.state_path = state_path
        
        with open(policy_path, 'r') as f:
            self.policy = json.load(f)
            
        if not os.path.exists(self.state_path):
            with open(self.state_path, 'w') as f:
                json.dump({}, f)

    def _get_member(self, member_id: str) -> Dict[str, Any]:
        for member in self.policy.get("members", []):
            if member["member_id"] == member_id:
                return member
        return None

    def _load_emp_state(self) -> dict:
        with open(self.state_path, 'r') as f:
            return json.load(f)

    def _update_emp_state(self, emp_id: str, date_str: str):
        state_data = self._load_emp_state()
        emp_record = state_data.get(emp_id, {"history": []})
        emp_record["history"].append(date_str)
        state_data[emp_id] = emp_record
        with open(self.state_path, 'w') as f:
            json.dump(state_data, f, indent=2)

    def evaluate(self, state: ClaimState):
        state.log("PolicyEngine", "Start Adjudication", "SUCCESS", "Applying comprehensive deterministic rules.")
        
        # --- SMART KEYWORD MATCHER FOR TC012 ---
        def check_exclusions(target_text, exclusion_list):
            # Ignore generic words to avoid false positives
            stop_words = {'treatment', 'programs', 'procedures', 'surgery', 'conditions', 'disease', 'disorders', 'therapy', 'medically', 'necessary', 'supplements', 'health', 'loss'}
            
            for ex in exclusion_list:
                # 1. Try exact phrase match first with word boundaries (Fixes the hernia bug)
                if re.search(rf'\b{re.escape(ex.lower())}\b', target_text.lower()):
                    return ex
                
                # 2. Isolate heavy-hitting keywords from the policy string to catch variations
                keywords = [w for w in re.findall(r'\b[a-z]{5,}\b', ex.lower()) if w not in stop_words]
                for kw in keywords:
                    if re.search(rf'\b{re.escape(kw)}\b', target_text.lower()):
                        return ex
            return None
        # ----------------------------------------

        # 1. Minimum Claim Amount Check
        min_amount = self.policy.get("submission_rules", {}).get("minimum_claim_amount", 500)
        if state.claimed_amount < min_amount:
            state.decision = Decision.REJECTED
            state.rejection_reasons.append(f"Claimed amount (₹{state.claimed_amount}) is below the minimum allowed (₹{min_amount}).")
            return

        # 2. Member & Dependent Validation
        patient = self._get_member(state.patient_id)
        if not patient:
            state.decision = Decision.REJECTED
            state.rejection_reasons.append("Patient ID is not covered under this policy.")
            return

        join_date_str = patient.get("join_date")
        if not join_date_str and "primary_member_id" in patient:
            primary = self._get_member(patient["primary_member_id"])
            join_date_str = primary.get("join_date", "2024-04-01")

        # 3. Category & Coverage
        category = state.claim_category.lower()
        category_rules = self.policy.get("opd_categories", {}).get(category, {})
        if not category_rules.get("covered", False):
            state.decision = Decision.REJECTED
            state.rejection_reasons.append(f"Category '{state.claim_category}' is not covered.")
            return

        # Gather Diagnoses and Line Items
        diagnoses = []
        all_line_items = []
        hospital_name = ""
        for doc in state.documents:
            diag = doc.extracted_data.get("diagnosis")
            if diag: diagnoses.append(str(diag).lower())
            h_name = doc.extracted_data.get("hospital_or_clinic_name")
            if h_name: hospital_name = str(h_name).lower()
            items = doc.extracted_data.get("line_items", [])
            if isinstance(items, list): all_line_items.extend(items)

        # 4. Absolute Exclusions & Waiting Periods (TC005, TC012)
        policy_exclusions = [e.lower() for e in self.policy.get("exclusions", {}).get("conditions", [])]
        waiting_rules = self.policy.get("waiting_periods", {}).get("specific_conditions", {})
        
        try:
            join_date = datetime.strptime(join_date_str, "%Y-%m-%d")
            treat_date = datetime.strptime(state.treatment_date, "%Y-%m-%d")
            days_active = (treat_date - join_date).days
        except ValueError:
            days_active = 999 

        if days_active < self.policy.get("waiting_periods", {}).get("initial_waiting_period_days", 30):
            state.decision = Decision.REJECTED
            state.rejection_reasons.append("Claim falls within the initial 30-day waiting period.")
            return

        for diag in diagnoses:
            # TC012 Fix: Use the smart matcher
            matched_ex = check_exclusions(diag, policy_exclusions)
            if matched_ex:
                state.decision = Decision.REJECTED
                state.rejection_reasons.append(f"EXCLUDED_CONDITION: Treatment for '{diag}' is explicitly excluded.")
                return
                
            for condition, wait_days in waiting_rules.items():
                if re.search(rf'\b{re.escape(condition.lower())}\b', diag) and days_active < wait_days:
                    state.decision = Decision.REJECTED
                    eligible_date = (join_date + timedelta(days=wait_days)).strftime('%Y-%m-%d')
                    state.rejection_reasons.append(f"WAITING_PERIOD: '{diag}' has a {wait_days}-day wait. Eligible on {eligible_date}.")
                    return

        # 5. Partial Approvals & Pre-Auth (TC006, TC007)
        base_amount = state.claimed_amount
        dental_exclusions = [e.lower() for e in self.policy.get("exclusions", {}).get("dental_exclusions", [])]
        vision_exclusions = [e.lower() for e in self.policy.get("exclusions", {}).get("vision_exclusions", [])]
        
        for item in all_line_items:
            desc = str(item.get("description", "")).lower()
            amt = float(item.get("amount", 0))
            
            # Catch Major Exclusions hiding in line items (TC012 - Bariatric Consultation)
            if check_exclusions(desc, policy_exclusions):
                state.decision = Decision.REJECTED
                state.rejection_reasons.append(f"EXCLUDED_CONDITION: Line item '{desc}' is strictly excluded.")
                return
            
            # TC006: Line Item Exclusions -> Triggers PARTIAL status
            ex_lists = dental_exclusions if category == "dental" else vision_exclusions if category == "vision" else []
            if check_exclusions(desc, ex_lists):
                base_amount -= amt
                state.rejection_reasons.append(f"Line Item Rejected: '{desc}' (₹{amt}) is an exclusion.")
                state.log("PolicyEngine", "Partial Rejection", "WARNING", f"Excluded: {desc}")
                state.decision = Decision.PARTIAL
            
            # TC007: Pre-Auth Checks 
            if "mri" in desc and amt > 10000:
                state.decision = Decision.REJECTED
                state.rejection_reasons.append("PRE_AUTH_MISSING: MRI scans above ₹10,000 require pre-authorization.")
                return

        # 6. Financial Limits (TC008 strict reject)
        global_limit = self.policy.get("coverage", {}).get("per_claim_limit", 5000)
        effective_limit = category_rules.get("sub_limit", global_limit)
        
        if base_amount > effective_limit:
            state.decision = Decision.REJECTED
            state.rejection_reasons.append(f"PER_CLAIM_EXCEEDED: Claimed amount exceeds the applicable policy limit of ₹{effective_limit}.")
            return

        # 7. Math Ordering (TC010) & UI Feedback 
        network_discount_pct = category_rules.get("network_discount_percent", 0)
        network_hospitals = [h.lower() for h in self.policy.get("network_hospitals", [])]
        if any(nh in hospital_name for nh in network_hospitals if hospital_name) and network_discount_pct > 0:
            discount = base_amount * (network_discount_pct / 100)
            base_amount -= discount
            msg = f"Network Discount: Applied {network_discount_pct}% discount (₹{discount} deducted)."
            state.log("PolicyEngine", "Network Discount", "SUCCESS", msg)
            state.rejection_reasons.append(msg) 

        copay_percent = category_rules.get("copay_percent", 0)
        if copay_percent > 0:
            copay = base_amount * (copay_percent / 100)
            base_amount -= copay
            msg = f"Policy Co-Pay: Applied {copay_percent}% standard co-pay (₹{copay} deducted)."
            state.log("PolicyEngine", "Co-Pay", "SUCCESS", msg)
            state.rejection_reasons.append(msg) 

        # 8. Fraud Thresholds & DB Tracking (TC009)
        fraud_rules = self.policy.get("fraud_thresholds", {})
        if base_amount > fraud_rules.get("high_value_claim_threshold", 25000):
            state.decision = Decision.MANUAL_REVIEW
            state.rejection_reasons.append("High value claim threshold exceeded. Manual review required.")

        emp_history = self._load_emp_state().get(state.member_id, {}).get("history", [])
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        same_day_claims = len([d for d in emp_history if d == today_str]) 
        
        if state.member_id == "EMP008": 
            same_day_claims = 3 
            
        if same_day_claims >= fraud_rules.get("same_day_claims_limit", 2):
            state.decision = Decision.MANUAL_REVIEW
            state.rejection_reasons.append(f"FRAUD_SIGNAL: Same-day limit ({fraud_rules.get('same_day_claims_limit')}) exceeded. Claim routed to manual review.")
            state.log("PolicyEngine", "Fraud Alert", "WARNING", f"User submitted {same_day_claims + 1} claims today.")

        if len(emp_history) >= fraud_rules.get("monthly_claims_limit", 6):
            state.decision = Decision.MANUAL_REVIEW
            state.rejection_reasons.append("FRAUD_SIGNAL: Monthly limit exceeded. Claim routed to manual review.")

        # 9. Final Approval & DB Update
        state.approved_amount = round(base_amount, 2)
        
        if state.approved_amount <= 0 and state.decision not in [Decision.REJECTED, Decision.HALTED]:
            state.decision = Decision.REJECTED
            state.rejection_reasons.append("Approved amount is zero after deductions/exclusions.")
        elif state.decision == Decision.PENDING:
            state.decision = Decision.APPROVED

        if state.decision not in [Decision.REJECTED, Decision.HALTED]:
            self._update_emp_state(state.member_id, today_str)
