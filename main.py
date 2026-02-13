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

# --- LOGIN GATE (WITH BLURB) ---
if not st.session_state.authenticated:
    st.title("🛡️ CareSync Canada")
    
    st.markdown("""
    ### **Welcome to the Family Care Prototype**
    CareSync Canada is a dual-interface dashboard designed to bridge the gap between seniors and their care teams.
    
    **This prototype demonstrates:**
    * 🩺 **Caregiver Command Centre:** Comprehensive tracking for meds, mood, and coordination.
    * 👵 **Senior Empowerment View:** A high-contrast, simplified interface for elder users.
    * 📅 **Dynamic Management:** Editable care calendars and medical document storage.
    * 🚨 **Integrated Safety:** Instant SOS logging and emergency alerts.
    
    ---
    *This is a live portfolio demonstration. Please use the access code below to enter.*
    """)
    
    entry_code = st.text_input("Enter Access Code (Hint: care):", type="password")
    
    if st.button("Access Dashboard"):
        if entry_code == ACCESS_CODE:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect code. Please use 'care'.")
else:
    data = load_data()
    
    if st.session_state.role is None:
        st.header("Select Interface")
        st.write("Choose a view to explore the dashboard's functionality:")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("👵 SENIOR VIEW (Simplified)", use_container_width=True):
                st.session_state.role = "Senior"; st.rerun()
        with col2:
            if st.button("🩺 CAREGIVER VIEW (Full Suite)", use_container_width=True):
                st.session_state.role = "Caregiver"; st.rerun()
    
    else:
        # --- SIDEBAR NAVIGATION ---
        if st.session_state.role == "Caregiver":
            st.sidebar.title("🩺 Caregiver Tools")
            page = st.sidebar.radio("Navigate to:", 
                ["Dashboard", "Medication Manager", "Editable Calendar", "Document Vault", "Coordination Notes"])
        else:
            page = "Senior View"

        # --- PAGE: DASHBOARD ---
        if page == "Dashboard":
            st.title("📋 Care Command Centre")
            
            # Metrics Row
            m1, m2, m3 = st.columns(3)
            m1.metric("Active Medications", len(data["meds"]))
            m2.metric("Calendar Events", len(data["calendar"]))
            m3.metric("Vault Documents", len(data["docs"]))
            
            st.markdown("---")
            
            col_a, col_b = st.columns(2)
            with col_a:
                st.subheader("💊 Medication Overview")
                if data["meds"]:
                    st.table(pd.DataFrame(data["meds"]).tail(5)[['name', 'freq']])
                else: st.info("No meds logged.")
                
                st.subheader("📊 Last Senior Status")
                if data["status_reports"]:
                    last = data["status_reports"][-1]
                    st.success(f"Reported Mood: **{last['mood']}**")
                    st.caption(f"Logged at: {last['time']}")
                else: st.info("No health reports yet.")

            with col_b:
                st.subheader("📅 Upcoming Agenda")
                if data["calendar"]:
                    df_cal = pd.DataFrame(data["calendar"]).sort_values(by='date').head(5)
                    for _, row in df_cal.iterrows():
                        st.write(f"🗓 **{row['date']}** | {row['time']} - {row['event']}")
                else: st.info("Calendar is empty.")

                st.subheader("🚨 Recent Alerts")
                if data["alerts"]:
                    for alert in reversed(data["alerts"][-3:]):
                        st.warning(f"{alert['type']} at {alert['time']}")
                else: st.write("No recent alerts.")

        # --- PAGE: MEDICATION MANAGER ---
        elif page == "Medication Manager":
            st.title("💊 Medication Management")
            with st.expander("➕ Add New Medication", expanded=True):
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

        # --- PAGE: EDITABLE CALENDAR ---
        elif page == "Editable Calendar":
            st.title("📅 Care Calendar")
            with st.expander("➕ Add Appointment/Task"):
                with st.form("cal_form"):
                    t_desc = st.text_input("Event Description")
                    t_date = st.date_input("Date")
                    t_time = st.time_input("Time")
                    if st.form_submit_button("Add to Calendar"):
                        data["calendar"].append({"event": t_desc, "date": str(t_date), "time": str(t_time)})
                        save_data(data); st.rerun()
            
            if data["calendar"]:
                for i, event in enumerate(data["calendar"]):
                    c = st.columns([4, 2, 2, 1])
                    c[0].write(f"📌 {event['event']}")
                    c[1].write(event['date'])
                    c[2].write(event['time'])
                    if c[3].button("🗑️", key=f"cal_{i}"):
                        data["calendar"].pop(i); save_data(data); st.rerun()

        # --- PAGE: SENIOR VIEW ---
        elif page == "Senior View":
            st.title("👵 Welcome Back!")
            st.subheader("How are you feeling right now?")
            mood = st.select_slider("My Energy Level:", options=["Very Low", "Low", "Ok", "Good", "Excellent"])
            if st.button("Save My Status"):
                data["status_reports"].append({"mood": mood, "time": datetime.now().strftime("%Y-%m-%d %H:%M")})
                save_data(data); st.success("Your family has been updated!")

            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🚨 I NEED HELP", use_container_width=True, type="primary"):
                    data["alerts"].append({"time": datetime.now().strftime("%H:%M"), "type": "SENIOR HELP REQUEST"})
                    save_data(data); st.error("Emergency Alert Sent!")
            with col2:
                if st.button("💊 I TOOK MY MEDS", use_container_width=True):
                    data["alerts"].append({"time": datetime.now().strftime("%H:%M"), "type": "Senior confirmed meds"})
                    save_data(data); st.success("Great job!")

        # --- OTHER PAGES ---
        elif page == "Document Vault":
            st.title("📂 Document Vault")
            up = st.file_uploader("Upload Record")
            if up:
                data["docs"].append({"name": up.name, "date": str(datetime.now().date())})
                save_data(data); st.success("Saved.")
            if data["docs"]: st.table(pd.DataFrame(data["docs"]))

        elif page == "Coordination Notes":
            st.title("📝 Team Notes")
            n = st.text_area("Update for next shift:")
            if st.button("Post Note"):
                if n:
                    data["notes"].append({"note": n, "time": datetime.now().strftime("%H:%M")})
                    save_data(data); st.rerun()
            for note in reversed(data["notes"]): st.info(f"{note['time']}: {note['note']}")

        # Footer
        st.sidebar.markdown("---")
        if st.sidebar.button("Logout / Switch View"):
            st.session_state.role = None
            st.session_state.authenticated = False; st.rerun()
