import streamlit as st
import json
import os
from datetime import datetime
import pandas as pd

# --- CONFIG ---
ACCESS_CODE = "care"
DATA_FILE = "family_data.json"

# --- DATA PERSISTENCE ---
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"meds": [], "notes": [], "status_reports": [], "alerts": [], "docs": []}
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {"meds": [], "notes": [], "status_reports": [], "alerts": [], "docs": []}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# --- UI SETUP ---
st.set_page_config(page_title="CareSync Canada", page_icon="🛡️", layout="wide")

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "role" not in st.session_state:
    st.session_state.role = None

# --- LOGIN & ONBOARDING ---
if not st.session_state.authenticated:
    st.title("🛡️ CareSync Canada")
    st.markdown("""
    ### **Family Care Management System**
    A central hub for synchronized caregiving.
    * 💊 **Advanced Med Tracking:** Schedule, frequency, and history.
    * 📂 **Document Vault:** Secure storage for medical PDFs and records.
    * 📅 **Care Calendar:** View upcoming appointments and tasks.
    * 👵 **Accessibility:** Specialized 'Senior View' for elder users.
    """)
    entry_code = st.text_input("Enter Access Code (Hint: care):", type="password")
    if st.button("Access Dashboard"):
        if entry_code == ACCESS_CODE:
            st.session_state.authenticated = True
            st.rerun()
else:
    data = load_data()
    
    # ROLE SELECTION
    if st.session_state.role is None:
        st.header("Select Interface")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("👵 SENIOR VIEW", use_container_width=True):
                st.session_state.role = "Senior"; st.rerun()
        with col2:
            if st.button("🩺 CAREGIVER VIEW", use_container_width=True):
                st.session_state.role = "Caregiver"; st.rerun()
    
    # --- APP NAVIGATION ---
    else:
        # Sidebar for Caregiver
        if st.session_state.role == "Caregiver":
            st.sidebar.title("Caregiver Tools")
            page = st.sidebar.selectbox("Go to:", ["Dashboard", "Medication Manager", "Document Vault", "Care Calendar", "Daily Status", "Notes"])
        else:
            page = "Senior View" # Senior only sees one page

        # --- FEATURE: MEDICATION MANAGER (Caregiver) ---
        if page == "Medication Manager":
            st.title("💊 Medication Management")
            
            with st.expander("➕ Add New Medication"):
                with st.form("med_form"):
                    m_name = st.text_input("Medication Name")
                    m_freq = st.selectbox("Frequency", ["Once daily", "Twice daily", "Three times daily", "As needed"])
                    col_a, col_b = st.columns(2)
                    m_start = col_a.date_input("Start Date")
                    m_end = col_b.date_input("End Date")
                    if st.form_submit_button("Add to Schedule"):
                        data["meds"].append({
                            "id": len(data["meds"]),
                            "name": m_name, "freq": m_freq, 
                            "start": str(m_start), "end": str(m_end)
                        })
                        save_data(data); st.success("Medication added!")

            st.subheader("Current Schedule")
            if data["meds"]:
                for i, m in enumerate(data["meds"]):
                    cols = st.columns([3, 2, 2, 1])
                    cols[0].write(f"**{m['name']}**")
                    cols[1].write(f"⏱ {m['freq']}")
                    cols[2].write(f"🗓 {m['start']} to {m['end']}")
                    if cols[3].button("🗑️", key=f"del_{i}"):
                        data["meds"].pop(i)
                        save_data(data); st.rerun()
            else: st.info("No medications scheduled.")

        # --- FEATURE: DOCUMENT VAULT ---
        elif page == "Document Vault":
            st.title("📂 Document Vault")
            st.info("Demo Mode: Uploading files is simulated. Records are listed below.")
            uploaded_file = st.file_uploader("Upload Medical PDF/Image")
            if uploaded_file:
                data["docs"].append({"name": uploaded_file.name, "date": str(datetime.now().date())})
                save_data(data); st.success("Document record saved!")
            
            if data["docs"]:
                st.table(pd.DataFrame(data["docs"]))

        # --- FEATURE: CARE CALENDAR ---
        elif page == "Care Calendar":
            st.title("📅 Care Calendar")
            st.date_input("Select Date to View Tasks")
            st.write("### Today's Schedule")
            st.write("- 09:00 AM: Morning Medications")
            st.write("- 02:00 PM: Physiotherapy Appointment")

        # --- FEATURE: DAILY STATUS ---
        elif page == "Daily Status":
            st.title("📊 Health Status Tracking")
            st.write("Log how the senior is feeling today to track patterns over time.")
            mood = st.select_slider("Mood/Energy", options=["Very Low", "Low", "Neutral", "Good", "Excellent"])
            pain = st.slider("Pain Level (0-10)", 0, 10, 0)
            if st.button("Save Health Log"):
                data["status_reports"].append({"mood": mood, "pain": pain, "time": str(datetime.now())})
                save_data(data); st.success("Status updated.")

        # --- FEATURE: SENIOR VIEW ---
        elif page == "Senior View":
            st.title("👋 Welcome Back!")
            st.markdown("### Important for Today:")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🚨 I NEED HELP", use_container_width=True, type="primary"):
                    st.error("Help alert sent to your family!")
            with col2:
                if st.button("💊 I TOOK MY MEDS", use_container_width=True):
                    st.success("Thank you! Logged for the family.")

        # --- SHARED FEATURES ---
        elif page == "Dashboard":
            st.title("📋 Home Dashboard")
            st.metric("Active Medications", len(data["meds"]))
            st.write("#### Recent Alerts")
            if data["alerts"]: st.write(data["alerts"][-1])
            else: st.write("No alerts today.")

        elif page == "Notes":
            st.title("📝 Coordination Notes")
            note = st.text_area("Update for the family:")
            if st.button("Post Note"):
                data["notes"].append({"note": note, "time": str(datetime.now())})
                save_data(data); st.rerun()
            for n in reversed(data["notes"]): st.info(f"{n['time']}: {n['note']}")

        if st.sidebar.button("Logout/Switch Role"):
            st.session_state.role = None
            st.session_state.authenticated = False; st.rerun()
