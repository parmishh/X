import streamlit as st
import requests
import json
import os

st.set_page_config(page_title="Plum Multi-Agent Claims AI", layout="wide")

with open("data/policy_terms.json", "r") as f:
    policy = json.load(f)

members_list = policy.get("members", [])
employees = [m for m in members_list if m.get("relationship") == "SELF"]

st.title("🛡️ Plum Intelligent Claims Adjudication (V2)")
st.markdown("Powered by a fault-tolerant multi-agent state machine.")

with st.sidebar:
    st.header("Claim Details")
    
    # 1. Employee Selection
    emp_id = st.selectbox("Employee ID", [e["member_id"] for e in employees])
    selected_emp = next(e for e in employees if e["member_id"] == emp_id)
    
    # 2. Dynamic Dependent Detection
    dep_ids = selected_emp.get("dependents", [])
    dependents = [m for m in members_list if m["member_id"] in dep_ids]
    
    patient_options = {emp_id: f"{selected_emp['name']} (Self)"}
    for d in dependents:
        patient_options[d["member_id"]] = f"{d['name']} ({d['relationship']})"
        
    patient_id = st.selectbox("Patient For Claim", list(patient_options.keys()), format_func=lambda x: patient_options[x])
    patient_name = patient_options[patient_id].split(" (")[0]
    
    categories = [k.upper() for k in policy.get("opd_categories", {}).keys()]
    claim_category = st.selectbox("Category", categories)
    treatment_date = st.date_input("Treatment Date")
    claimed_amount = st.number_input("Claimed Amount (₹)", value=1500.0)
    
    st.divider()
    st.header("Fraud State Management")
    if st.button("Reset Employee State DB"):
        with open("data/employee_state.json", "w") as f:
            json.dump({}, f)
        st.success("Fraud tracking state reset!")

    st.divider()
    st.header("Eval Test Controls")
    simulate_fail = st.checkbox("💥 Simulate Component Failure (TC011)", value=False)
    enable_ai_forgery = st.checkbox("🔍 Enable AI Forgery Check", value=False)

doc_rules = policy.get("document_requirements", {}).get(claim_category, {"required": ["PRESCRIPTION", "HOSPITAL_BILL"], "optional": []})

st.header("Upload Medical Documents")
col1, col2 = st.columns(2)

required_files = []
with col1:
    st.subheader("Required Documents")
    for req_doc in doc_rules["required"]:
        uploaded = st.file_uploader(f"Upload {req_doc}*", key=f"req_{req_doc}")
        if uploaded: required_files.append((req_doc, uploaded))

optional_files = []
with col2:
    st.subheader("Optional Documents")
    for opt_doc in doc_rules["optional"]:
        uploaded = st.file_uploader(f"Upload {opt_doc}", key=f"opt_{opt_doc}")
        if uploaded: optional_files.append((opt_doc, uploaded))

if st.button("Run Multi-Agent Pipeline", type="primary"):
    if len(required_files) != len(doc_rules["required"]):
        st.error(f"Please upload all required documents: {', '.join(doc_rules['required'])}")
        st.stop()
        
    with st.spinner("Agents are analyzing documents and evaluating policy..."):
        all_uploads = required_files + optional_files
        files_data = [("files", (file.name, file.getvalue(), file.type)) for _, file in all_uploads]
        expected_types = ",".join([dt for dt, _ in all_uploads])
        
        payload = {
            "member_id": emp_id,
            "patient_id": patient_id,
            "patient_name": patient_name,
            "claim_category": claim_category,
            "treatment_date": str(treatment_date),
            "claimed_amount": claimed_amount,
            "expected_doc_types": expected_types,
            "simulate_component_failure": simulate_fail,
            "enable_ai_forgery_check": enable_ai_forgery
        }

        try:
            # response = requests.post("http://127.0.0.1:8000/api/v2/process-claim", data=payload, files=files_data)
            
            API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
            response = requests.post(f"{API_URL}/api/v2/process-claim", data=payload, files=files_data)
            result = response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"Network Connection Failed: Is Uvicorn running? Error: {e}")
            st.stop()

    st.divider()
    res_col1, res_col2 = st.columns([1, 2])
    
    with res_col1:
        st.subheader("Final Decision")
        decision = result.get("decision", "UNKNOWN")
        color = "green" if decision == "APPROVED" else "red" if decision in ["REJECTED", "HALTED"] else "orange"
        st.markdown(f"<h2 style='color:{color}'>{decision}</h2>", unsafe_allow_html=True)
        st.metric("Approved Amount", f"₹{result.get('approved_amount', 0.0)}")
        st.metric("System Confidence", f"{result.get('confidence_score', 0.0) * 100}%")
        
        reasons = result.get("rejection_reasons", [])
        if reasons:
            st.error("**Notes / Rejection Reasons:**\n\n" + "\n".join([f"- {r}" for r in reasons]))

    with res_col2:
        st.subheader("Agent Audit Trace")
        st.caption(f"Claim ID: {result.get('claim_id')}")
        for step in result.get("trace_log", []):
            status = step.get('status')
            icon = "✅" if status == "SUCCESS" else "❌" if status == "FAILED" else "⚠️"
            with st.expander(f"{icon} **{step.get('component')}** | {step.get('action')}"):
                st.write(step.get('details'))
