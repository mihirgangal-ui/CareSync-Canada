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
        return {"events": [], "meds": [], "notes": [], "status_reports": [], "alerts": []}
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {"events": [], "meds": [], "notes": [], "status_reports": [], "alerts": []}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# --- UI SETUP ---
st.set_page_config(page_title="CareSync Canada", page_icon="🛡️", layout="wide")

# --- LOGIN & ONBOARDING GATE ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "role" not in st.session_state:
    st.session_state.role = None

if not st.session_state.authenticated:
    st.title("🛡️ CareSync Canada")
    
    st.markdown("""
    ### **Welcome to the Family Care Prototype**
    CareSync Canada is a dual-interface dashboard designed to bridge the gap between seniors and their care teams.
    
    **This prototype demonstrates:**
    * 👵 **Senior View:** A high-contrast, simplified interface for ease of use.
    * 🩺 **Caregiver View:** Comprehensive tracking for meds, mood, and coordination.
    * 🚨 **Integrated Safety:** Instant SOS logging and emergency alerts.
    
    ---
    *Use the access code below to explore the dashboard.*
    """)
    
    entry_code = st.text_input("Enter Access Code (Hint: care):", type="password")
    
    if st.button("Access Dashboard"):
        if entry_code == ACCESS_CODE:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect code.")

elif st.session_state.role is None:
    # ROLE SELECTION PAGE
    st.title("Who is using the app right now?")
    st.write("Please select a view to continue:")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("👵 I am the Senior (Simple View)", use_container_width=True):
            st.session_state.role = "Senior"
            st.rerun()
    with col2:
        if st.button("🩺 I am a Caregiver (Full View)", use_container_width=True):
            st.session_state.role = "Caregiver"
            st.rerun()

else:
    # --- MAIN APP LOGIC ---
    data = load_data()

    # --- VIEW 1: SENIOR VIEW (Simple, Large Buttons) ---
    if st.session_state.role == "Senior":
        st.title("👋 Hello!")
        st.subheader("How can we help you today?")
        
        st.markdown("---")
        col_sos, col_med = st.columns(2)
        
        with col_sos:
            if st.button("🚨 CALL FOR HELP", use_container_width=True, type="primary"):
                alert_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                data["alerts"].append({"time": alert_time, "type": "SENIOR REQUESTED HELP"})
                save_data(data)
                st.error("Help request sent to your family!")

        with col_med:
            if st.button("💊 I TOOK MY MEDS", use_container_width=True):
                data["meds"].append({"name": "Self-Reported", "dosage": "Standard", "time": datetime.now().strftime('%Y-%m-%d %H:%M')})
                save_data(data)
                st.success("Great job! We've let the family know.")

        if st.button("Switch to Caregiver View"):
            st.session_state.role = None
            st.rerun()

    # --- VIEW 2: CAREGIVER VIEW (Standard Dashboard) ---
    else:
        st.sidebar.title("🩺 Caregiver Menu")
        page = st.sidebar.radio("Navigate to:", ["Dashboard", "Medication Tracker", "Status Reports", "Family Notes"])
        
        if st.sidebar.button("Switch Role"):
            st.session_state.role = None
            st.rerun()

        # SOS Logic for Caregiver
        st.sidebar.markdown("---")
        if st.sidebar.button("🚨 LOG SOS ALERT"):
            alert_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            data["alerts"].append({"time": alert_time, "type": "Caregiver Flagged Emergency"})
            save_data(data)
            st.sidebar.warning(f"Emergency Logged: {alert_time}")

        # PAGE: DASHBOARD
        if page == "Dashboard":
            st.title("📋 Caregiving Overview")
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Recent Activity")
                if data["meds"]:
                    st.table(pd.DataFrame(data["meds"]).tail(3))
                else: st.write("No meds logged.")
            with col2:
                st.subheader("Latest Alerts")
                if data["alerts"]:
                    st.warning(f"Last Alert: {data['alerts'][-1]['type']} at {data['alerts'][-1]['time']}")
                else: st.write("No recent alerts.")

        # PAGE: MEDICATION TRACKER
        elif page == "Medication Tracker":
            st.title("💊 Medication Log")
            with st.form("med_form"):
                name = st.text_input("Medication Name")
                dosage = st.text_input("Dosage")
                if st.form_submit_button("Log Dose"):
                    data["meds"].append({"name": name, "dosage": dosage, "time": datetime.now().strftime('%Y-%m-%d %H:%M')})
                    save_data(data)
                    st.success(f"Logged {name}")
            if data["meds"]: st.dataframe(pd.DataFrame(data["meds"]))

        # PAGE: STATUS REPORTS
        elif page == "Status Reports":
            st.title("📊 Daily Status")
            mood = st.select_slider("Mood/Energy", options=["Low", "Fair", "Good", "Excellent"])
            if st.button("Submit Report"):
                data["status_reports"].append({"mood": mood, "time": datetime.now().strftime('%Y-%m-%d %H:%M')})
                save_data(data)
                st.success("Report saved.")

        # PAGE: FAMILY NOTES
        elif page == "Family Notes":
            st.title("📝 Coordination Notes")
            new_note = st.text_area("Add a note:")
            if st.button("Post Note"):
                if new_note:
                    data["notes"].append({"note": new_note, "time": datetime.now().strftime('%Y-%m-%d %H:%M')})
                    save_data(data)
                    st.rerun()
            for note in reversed(data["notes"]):
                st.info(f"{note['time']}: {note['note']}")

    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.role = None
        st.rerun()
