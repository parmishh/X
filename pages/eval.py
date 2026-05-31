import streamlit as st

st.set_page_config(page_title="Plum Claims | Eval Report", layout="wide")

st.title("📊 Master System Evaluation Report")
st.markdown("Comprehensive, end-to-end review of all 12 edge-cases for the Intelligent Claims Adjudication pipeline.")
st.divider()

# ==========================================
# TC001: Wrong Document Uploaded
# ==========================================
st.header("TC001 - Wrong Document Uploaded")
st.markdown("**Scenario:** Member submits two prescriptions for a consultation claim that requires a prescription and a hospital bill.")
col_left, col_right = st.columns([1.5, 1], gap="large")

with col_left:
    st.subheader("📥 Input Documents")
    img1, img2 = st.columns(2)
    with img1:

        st.image("TC/Input-Prescription.png", use_container_width=True,caption="Prescription")
    with img2:

        st.image("TC/Input-Prescription.png", use_container_width=True,caption="Prescription")

with col_right:
    st.subheader("📤 System Output")

    st.image("TC/Output-1.png", use_container_width=True)
    
    st.markdown("**Expected:**")
    st.success("🛑 **HALTED.** System must stop before making any claim decision. Must tell the member specifically what document type was uploaded and what is needed instead.")
st.divider()


# ==========================================
# TC002: Unreadable Document
# ==========================================
st.header("TC002 - Unreadable Document")
st.markdown("**Scenario:** Member uploads a valid prescription but a blurry, unreadable photo of their pharmacy bill.")
col_left, col_right = st.columns([1.5, 1], gap="large")

with col_left:
    st.subheader("📥 Input Documents")
    img1, img2 = st.columns(2)
    with img1:
        st.image("TC/Input-Prescription.png", use_container_width=True,caption="Prescription")
    with img2:
        st.image("TC/input-blur.jpg", use_container_width=True,caption="Hospital Bill")

with col_right:
    st.subheader("📤 System Output")
    st.image("TC/output-blur.png", use_container_width=True)
    
    st.markdown("**Expected:**")
    st.success("🛑 **HALTED.** Identify that the pharmacy bill cannot be read. Ask the member to re-upload that specific document.")
st.divider()


# ==========================================
# TC003: Documents Belong to Different Patients
# ==========================================
st.header("TC003 - Documents Belong to Different Patients")
st.markdown("**Scenario:** The prescription and hospital bill is for a different patient")
col_left, col_right = st.columns([1.5, 1], gap="large")

with col_left:
    st.subheader("📥 Input Documents")
    img1, img2 = st.columns(2)
    with img1:
        st.image("TC/Input-Prescription.png", use_container_width=True,caption="Prescription")
    with img2:
        st.image("TC/input3.png", use_container_width=True,caption="Hospital Bill")

with col_right:
    st.subheader("📤 System Output")
    st.image("TC/output-name_mismatch.png", use_container_width=True)
    
    st.markdown("**Expected:**")
    st.success("🛑 **HALTED.** Detect that the documents belong to different people. Surface this to the member with specific names.")
st.divider()


# ==========================================
# TC004: Clean Consultation — Full Approval
# ==========================================
st.header("TC004 - Clean Consultation — Full Approval")
st.markdown("**Scenario:** Complete, valid consultation claim with correct documents, valid member, covered treatment, within all limits.")
col_left, col_right = st.columns([1.5, 1], gap="large")

with col_left:
    st.subheader("📥 Input Documents")
    img1, img2 = st.columns(2)
    with img1:
        st.image("TC/Input-Prescription.png", use_container_width=True, caption="Prescription")
    with img2:
        st.image("TC/input0.png", use_container_width=True, caption="Hospital Bill")

with col_right:
    st.subheader("📤 System Output")
    st.image("TC/sucess2.png", use_container_width=True, caption="Final Output")
    
    st.markdown("**Expected:**")
    st.success("✅ **APPROVED.** Apply 10% co-pay on consultation category. Confidence score must be above 0.85.")
st.divider()


# ==========================================
# TC005: Waiting Period — Diabetes
# ==========================================
st.header("TC005 - Waiting Period — Diabetes")
st.markdown("**Scenario:** Member joined 2024-09-01. Claims for diabetes treatment on 2024-10-15 (within 90-day waiting period).")
col_left, col_right = st.columns([1.5, 1], gap="large")

with col_left:
    st.subheader("📥 Input Documents")
    img1, img2 = st.columns(2)
    with img1:
        st.image("TC/input-prescription-diabetis.png", use_container_width=True, caption="Prescription")
    with img2:
        st.image("TC/input-diabetis-hospital_bill.png", use_container_width=True, caption="Hospital Bill")

with col_right:
    st.subheader("📤 System Output")
    st.image("TC/sucess-diabetis.png", use_container_width=True, caption="Prescription")
    
    st.markdown("**Expected:**")
    st.success("❌ **REJECTED.** State the exact date from which the member will be eligible for diabetes-related claims.")
st.divider()


# ==========================================
# TC006: Dental Partial Approval — Cosmetic Exclusion
# ==========================================
st.header("TC006 - Dental Partial Approval — Cosmetic Exclusion")
st.markdown("**Scenario:** Bill includes root canal treatment (covered) and teeth whitening (cosmetic, excluded).")
col_left, col_right = st.columns([1.5, 1], gap="large")

with col_left:
    st.subheader("📥 Input Documents")
    img1,img2 = st.columns(2)
    with img1:
        st.image("TC/input-Dental-cosmetic.png", use_container_width=True, caption="Hospital Bill")

with col_right:
    st.subheader("📤 System Output")
    st.image("TC/dental-sucess.png", use_container_width=True)
    
    st.markdown("**Expected:**")
    st.success("⚠️ **PARTIAL.** Itemize which line items were approved and which were rejected. State the reason for each rejection at the line-item level.")
st.divider()


# ==========================================
# TC007: MRI Without Pre-Authorization
# ==========================================
st.header("TC007 - MRI Without Pre-Authorization")
st.markdown("**Scenario:** MRI scan costing ₹15,000 submitted without pre-authorization.")
col_left, col_right = st.columns([1.5, 1], gap="large")

with col_left:
    st.subheader("📥 Input Documents")
    img1, img2, img3 = st.columns(3)
    with img1:
        st.image("TC/MRI-prescription.png", use_container_width=True, caption="Prescription")
    with img2:
        st.image("TC/MRI-HOSPITAL.png", use_container_width=True, caption="Hospital Bill")
    with img3:
        st.image("TC/MRI-Lab.png", use_container_width=True, caption="Lab Report")

with col_right:
    st.subheader("📤 System Output")
    st.image("TC/MRI-SUCESS.png", use_container_width=True,)
    
    st.markdown("**Expected:**")
    st.success("❌ **REJECTED.** Explain that pre-authorization was required and not obtained. Tell the member how to resubmit.")
st.divider()


# ==========================================
# TC008: Per-Claim Limit Exceeded
# ==========================================
st.header("TC008 - Per-Claim Limit Exceeded")
st.markdown("**Scenario:** Per Claimed amount limit exceeded")
col_left, col_right = st.columns([1.5, 1], gap="large")

with col_left:
    st.subheader("📥 Input Documents")
    img1, img2 = st.columns(2)
    with img1:
        st.image("TC/Input-Prescription.png", use_container_width=True, caption="Prescription")
    with img2:
        st.image("TC/exceed-per-claim-limit.png", use_container_width=True, caption="Hospital Bill")

with col_right:
    st.subheader("📤 System Output")
    st.image("TC/exceed-per-limit-sucess.png", use_container_width=True)
    
    st.markdown("**Expected:**")
    st.success("❌ **REJECTED.** State the per-claim limit and the claimed amount clearly in the rejection message.")
st.divider()


# ==========================================
# TC009: Fraud Signal — Multiple Same-Day Claims
# ==========================================
st.header("TC009 - Fraud Signal — Multiple Same-Day Claims")
st.markdown("**Scenario:** Exceed 2 per day claim from the same member on the same day.")
col_left, col_right = st.columns([1.5, 1], gap="large")

with col_left:
    st.subheader("[Click on Reset Employee state db on UI to reset limit]")


with col_right:
    st.subheader("📤 System Output") 
    st.image("TC/TC009.png", use_container_width=True)
    
    st.markdown("**Expected:**")
    st.success("👀 **MANUAL_REVIEW.** Flag the unusual same-day claim pattern. Include the specific signals that triggered the flag.")
st.divider()


# ==========================================
# TC010: Network Hospital — Discount Applied
# ==========================================
st.header("TC010 - Network Hospital — Discount Applied")
st.markdown("**Scenario:** Valid claim at Apollo Hospitals, a network hospital.")
col_left, col_right = st.columns([1.5, 1], gap="large")

with col_left:
    st.subheader("📥 Input Documents")
    img1, img2 = st.columns(2)
    with img1:
        st.image("TC/apollo-prescription.png", use_container_width=True, caption="Prescription")
    with img2:
        st.image("TC/apollo-hospital.png", use_container_width=True, caption="Hospital Bill")

with col_right:
    st.subheader("📤 System Output")
    st.image("TC/network-discount.png", use_container_width=True)
    
    st.markdown("**Expected:**")
    st.success("✅ **APPROVED.** Apply network discount before co-pay, not after. Show the breakdown of discount and co-pay in the decision output.")
st.divider()


# ==========================================
# TC011: Component Failure — Graceful Degradation
# ==========================================
st.header("TC011 - Component Failure — Graceful Degradation")
st.markdown("**Scenario:** One component of your system fails mid-processing.")
col_left, col_right = st.columns([1.5, 1], gap="large")

with col_left:
    st.subheader("[Simulate Component Failure] using the option in the UI")


with col_right:
    st.subheader("📤 System Output")
    st.image("TC/TC011.png", use_container_width=True, caption="Degraded Pipeline Output")
    
    st.markdown("**Expected:**")
    st.success("👀 **MANUAL_REVIEW.** Not crash or return a 500 error. Indicate in the output that a component failed. Return a lower confidence score.")
st.divider()


# ==========================================
# TC012: Excluded Treatment
# ==========================================
st.header("TC012 - Excluded Treatment")
st.markdown("**Scenario:** Member claims for bariatric consultation and a diet program (Obesity treatment).")
col_left, col_right = st.columns([1.5, 1], gap="large")

with col_left:
    st.subheader("📥 Input Documents")
    img1, img2, img3 = st.columns(3)
    with img1:
        st.image("TC/TC-012-prescription.png", use_container_width=True, caption="Prescription")
    with img2:
        st.image("TC/TC-012-hospital.png", use_container_width=True, caption="Hospital Bill")

with col_right:
    st.subheader("📤 System Output")
    st.image("TC/Tc-012.png", use_container_width=True)
    
    st.markdown("**Expected:**")
    st.success("❌ **REJECTED.** Rejection reason: EXCLUDED_CONDITION. Confidence score above 0.90.")
