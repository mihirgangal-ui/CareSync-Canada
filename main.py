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
    * 📂 **Document Vault:** Secure storage for medical records.
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
    
    # ROLE SELECTION (The "Onboarding" choice)
    if st.session_state.role is None:
        st.header("Select Interface")
        st.write("How would you like to explore the prototype?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("👵 SENIOR VIEW (Simple)", use_container_width=True):
                st.session_state.role = "Senior"; st.rerun()
        with col2:
            if st.button("🩺 CAREGIVER VIEW (Full Tools)", use_container_width=True):
                st.session_state.role = "Caregiver"; st.rerun()
    
    else:
        # --- SIDEBAR NAVIGATION (Visible List) ---
        if st.session_state.role == "Caregiver":
            st.sidebar.title("🩺 Caregiver Tools")
            # Using radio buttons so all options are always visible
            page = st.sidebar.radio(
                "Navigate to:", 
                ["Dashboard", "Medication Manager", "Document Vault", "Care Calendar", "Daily Status", "Coordination Notes"]
            )
        else:
            page = "Senior View"

        # --- FEATURE: MEDICATION MANAGER ---
        if page == "Medication Manager":
            st.title("💊 Medication Management")
            
            with st.expander("➕ Add New Medication", expanded=True):
                with st.form("med_form"):
                    m_name = st.text_input("Medication Name")
                    m_freq = st.selectbox("Frequency", ["Once daily", "Twice daily", "Three times daily", "As needed"])
                    col_a, col_b = st.columns(2)
                    m_start = col_a.date_input("Start Date")
                    m_end = col_b.date_input("End Date")
                    if st.form_submit_button("Add to Schedule"):
                        data["meds"].append({
                            "name": m_name, "freq": m_freq, 
                            "start": str(m_start), "end": str(m_end)
                        })
                        save_data(data); st.success(f"{m_name} added!"); st.rerun()

            st.subheader("Current Schedule")
            if data["meds"]:
                for i, m in enumerate(data["meds"]):
                    cols = st.columns([3, 2, 2, 1])
                    cols[0].write(f"**{m['name']}**")
                    cols[1].write(f"⏱ {m['freq']}")
                    cols[2].write(f"🗓 {m['start']} to {m['end']}")
                    if cols[3].button("🗑️", key=f"del_{i}"):
                        data["meds"].pop(i); save_data(data); st.rerun()
            else: st.info("No medications scheduled.")

        # --- FEATURE: DOCUMENT VAULT ---
        elif page == "Document Vault":
            st.title("📂 Document Vault")
            uploaded_file = st.file_uploader("Upload Medical PDF/Image (Simulated)")
            if uploaded_file:
                data["docs"].append({"name": uploaded_file.name, "date": str(datetime.now().date())})
                save_data(data); st.success("Document metadata saved to vault.")
            
            if data["docs"]:
                st.write("### Stored Records")
                st.table(pd.DataFrame(data["docs"]))

        # --- FEATURE: CARE CALENDAR ---
        elif page == "Care Calendar":
            st.title("📅 Care Calendar")
            st.date_input("Select Date")
            st.info("Today's Agenda")
            st.markdown("""
            - **09:00 AM** - Morning Meds (Blood Pressure)
            - **11:30 AM** - Light Walk in Park
            - **02:00 PM** - Physiotherapy (Clinic A)
            - **06:00 PM** - Evening Meds
            """)

        # --- FEATURE: DAILY STATUS ---
        elif page == "Daily Status":
            st.title("📊 Health Status Tracking")
            mood = st.select_slider("Mood/Energy", options=["Very Low", "Low", "Neutral", "Good", "Excellent"])
            pain = st.slider("Pain Level (0-10)", 0, 10, 0)
            if st.button("Save Health Log"):
                data["status_reports"].append({"mood": mood, "pain": pain, "time": str(datetime.now())})
                save_data(data); st.success("Health log updated.")

        # --- FEATURE: SENIOR VIEW ---
        elif page == "Senior View":
            st.title("👋 Welcome Back!")
            st.write("### What would you like to do?")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🚨 I NEED HELP", use_container_width=True, type="primary"):
                    st.error("HELP ALERT LOGGED. Family is being notified.")
            with col2:
                if st.button("💊 I TOOK MY MEDS", use_container_width=True):
                    st.success("Great job! We've updated your schedule.")

        # --- FEATURE: DASHBOARD ---
        elif page == "Dashboard":
            st.title("📋 Home Dashboard")
            m_col, a_col = st.columns(2)
            m_col.metric("Active Meds", len(data["meds"]))
            a_col.metric("Unread Notes", len(data["notes"]))
            
            st.write("### Recent Activity Feed")
            if data["notes"]: st.write(f"Latest Note: {data['notes'][-1]['note']}")
            else: st.write("No recent activity.")

        # --- FEATURE: NOTES ---
        elif page == "Coordination Notes":
            st.title("📝 Coordination Notes")
            note = st.text_area("Update for the team:")
            if st.button("Post Note"):
                if note:
                    data["notes"].append({"note": note, "time": datetime.now().strftime("%Y-%m-%d %H:%M")})
                    save_data(data); st.rerun()
            for n in reversed(data["notes"]): st.info(f"{n['time']}: {n['note']}")

        # --- SYSTEM FOOTER ---
        st.sidebar.markdown("---")
        if st.sidebar.button("Logout / Switch Role"):
            st.session_state.role = None
            st.session_state.authenticated = False; st.rerun()
