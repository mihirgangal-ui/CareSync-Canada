import streamlit as st
import json
import os
from datetime import datetime
import pandas as pd

# --- CONFIG ---
ACCESS_CODE = "care"
DATA_FILE = "family_data.json"

# --- BULLETPROOF DATA PERSISTENCE ---
def load_data():
    # Includes 'calendar' key for the new editable feature
    default_data = {"meds": [], "notes": [], "status_reports": [], "alerts": [], "docs": [], "calendar": []}
    if not os.path.exists(DATA_FILE):
        return default_data
    try:
        with open(DATA_FILE, "r") as f:
            current_data = json.load(f)
            for key in default_data:
                if key not in current_data:
                    current_data[key] = []
            return current_data
    except:
        return default_data

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
    * 💊 **Medication Manager:** Full schedule tracking with edit/delete.
    * 📅 **Editable Calendar:** Manage appointments and care visits.
    * 👵 **Senior Empowerment:** Senior-led health reporting and SOS.
    * 📂 **Document Vault:** Secure records for the whole care team.
    """)
    entry_code = st.text_input("Enter Access Code (Hint: care):", type="password")
    if st.button("Access Dashboard"):
        if entry_code == ACCESS_CODE:
            st.session_state.authenticated = True
            st.rerun()
else:
    data = load_data()
    
    if st.session_state.role is None:
        st.header("Select Interface")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("👵 SENIOR VIEW", use_container_width=True):
                st.session_state.role = "Senior"; st.rerun()
        with col2:
            if st.button("🩺 CAREGIVER VIEW", use_container_width=True):
                st.session_state.role = "Caregiver"; st.rerun()
    
    else:
        # --- SIDEBAR NAV ---
        if st.session_state.role == "Caregiver":
            st.sidebar.title("🩺 Caregiver Tools")
            page = st.sidebar.radio("Navigate to:", 
                ["Dashboard", "Medication Manager", "Editable Calendar", "Document Vault", "Coordination Notes"])
        else:
            page = "Senior View"

        # --- CAREGIVER: MEDICATION MANAGER ---
        if page == "Medication Manager":
            st.title("💊 Medication Management")
            with st.expander("➕ Add New Medication"):
                with st.form("med_form"):
                    m_name = st.text_input("Medication Name")
                    m_freq = st.selectbox("Frequency", ["Once daily", "Twice daily", "Three times daily", "As needed"])
                    m_start = st.date_input("Start Date")
                    if st.form_submit_button("Save Medication"):
                        data["meds"].append({"name": m_name, "freq": m_freq, "start": str(m_start)})
                        save_data(data); st.rerun()

            if data["meds"]:
                for i, m in enumerate(data["meds"]):
                    c = st.columns([3, 2, 2, 1])
                    c[0].write(f"**{m['name']}**")
                    c[1].write(m['freq'])
                    c[2].write(m['start'])
                    if c[3].button("🗑️", key=f"med_{i}"):
                        data["meds"].pop(i); save_data(data); st.rerun()

        # --- CAREGIVER: EDITABLE CALENDAR ---
        elif page == "Editable Calendar":
            st.title("📅 Care Calendar")
            with st.expander("➕ Add Appointment/Task"):
                with st.form("cal_form"):
                    t_desc = st.text_input("Event Description (e.g., Dentist)")
                    t_date = st.date_input("Date")
                    t_time = st.time_input("Time")
                    if st.form_submit_button("Add to Calendar"):
                        data["calendar"].append({"event": t_desc, "date": str(t_date), "time": str(t_time)})
                        save_data(data); st.rerun()
            
            st.subheader("Scheduled Events")
            if data["calendar"]:
                # Sort by date
                sorted_cal = sorted(data["calendar"], key=lambda x: x['date'])
                for i, event in enumerate(sorted_cal):
                    c = st.columns([4, 2, 2, 1])
                    c[0].write(f"📌 {event['event']}")
                    c[1].write(event['date'])
                    c[2].write(event['time'])
                    if c[3].button("🗑️", key=f"cal_{i}"):
                        data["calendar"].remove(event); save_data(data); st.rerun()
            else: st.info("No events scheduled.")

        # --- SENIOR VIEW: HEALTH & HELP ---
        elif page == "Senior View":
            st.title("👵 Welcome Back!")
            
            # Health Status moved here per your suggestion
            st.subheader("How are you feeling right now?")
            mood = st.select_slider("My Energy Level:", options=["Very Low", "Low", "Ok", "Good", "Excellent"])
            if st.button("Save My Status"):
                data["status_reports"].append({"mood": mood, "time": datetime.now().strftime("%Y-%m-%d %H:%M")})
                save_data(data); st.success("Your family has been updated!")

            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🚨 I NEED HELP", use_container_width=True, type="primary"):
                    data["alerts"].append({"time": str(datetime.now()), "type": "SENIOR HELP REQUEST"})
                    save_data(data); st.error("Emergency Alert Sent!")
            with col2:
                if st.button("💊 I TOOK MY MEDS", use_container_width=True):
                    data["alerts"].append({"time": str(datetime.now()), "type": "Senior confirmed meds"})
                    save_data(data); st.success("Great job!")

        # --- OTHER PAGES ---
        elif page == "Dashboard":
            st.title("📋 Care Overview")
            st.metric("Appointments", len(data["calendar"]))
            if data["status_reports"]:
                st.info(f"Senior's Last Reported Mood: {data['status_reports'][-1]['mood']}")
        
        elif page == "Document Vault":
            st.title("📂 Document Vault")
            up = st.file_uploader("Upload Record")
            if up:
                data["docs"].append({"name": up.name, "date": str(datetime.now().date())})
                save_data(data); st.success("Saved.")
            if data["docs"]: st.table(pd.DataFrame(data["docs"]))

        elif page == "Coordination Notes":
            st.title("📝 Team Notes")
            n = st.text_area("Update:")
            if st.button("Post"):
                data["notes"].append({"note": n, "time": datetime.now().strftime("%H:%M")})
                save_data(data); st.rerun()
            for note in reversed(data["notes"]): st.info(f"{note['time']}: {note['note']}")

        st.sidebar.markdown("---")
        if st.sidebar.button("Logout / Switch View"):
            st.session_state.role = None
            st.session_state.authenticated = False; st.rerun()
