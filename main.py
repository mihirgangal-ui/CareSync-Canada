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

# --- LOGIN GATE ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🛡️ CareSync Canada")
    st.info("Welcome to the Portfolio Demo.")
    
    entry_code = st.text_input("Enter Access Code (Hint: care):", type="password")
    
    if st.button("Access Dashboard"):
        if entry_code == ACCESS_CODE:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect code. Please use 'care'.")
else:
    # --- MAIN APP ---
    data = load_data()
    
    # Sidebar Navigation
    st.sidebar.title("🛡️ CareSync Menu")
    page = st.sidebar.radio("Navigate to:", ["Dashboard", "Medication Tracker", "Status Reports", "Family Notes"])
    
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.rerun()

    # --- SOS BUTTON (Demo Mode) ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("🚨 Emergency")
    if st.sidebar.button("SEND SOS ALERT"):
        # In Demo Mode, we just log it locally instead of sending an actual email
        alert_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        data["alerts"].append({"time": alert_time, "type": "SOS Button Pressed"})
        save_data(data)
        st.sidebar.success(f"SOS Logged at {alert_time}!")
        st.sidebar.caption("Note: Email notifications are disabled in this demo version.")

    # --- PAGE: DASHBOARD ---
    if page == "Dashboard":
        st.title("📋 Caregiving Overview")
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Recent Meds")
            if data["meds"]:
                df_meds = pd.DataFrame(data["meds"])
                st.table(df_meds.tail(3))
            else:
                st.write("No meds logged yet.")

        with col2:
            st.subheader("Latest Status")
            if data["status_reports"]:
                last_report = data["status_reports"][-1]
                st.metric("Patient Mood", last_report["mood"])
                st.write(f"Updated: {last_report['time']}")
            else:
                st.write("No status reports yet.")

    # --- PAGE: MEDICATION TRACKER ---
    elif page == "Medication Tracker":
        st.title("💊 Medication Adherence")
        with st.form("med_form"):
            name = st.text_input("Medication Name")
            dosage = st.text_input("Dosage")
            if st.form_submit_button("Log Dose"):
                data["meds"].append({"name": name, "dosage": dosage, "time": datetime.now().strftime('%Y-%m-%d %H:%M')})
                save_data(data)
                st.success(f"Logged {name}")
        
        if data["meds"]:
            st.dataframe(pd.DataFrame(data["meds"]))

    # --- PAGE: STATUS REPORTS ---
    elif page == "Status Reports":
        st.title("📊 Daily Status")
        mood = st.select_slider("Patient Mood/Energy", options=["Low", "Fair", "Good", "Excellent"])
        appetite = st.checkbox("Ate full meals?")
        if st.button("Submit Report"):
            data["status_reports"].append({"mood": mood, "appetite": appetite, "time": datetime.now().strftime('%Y-%m-%d %H:%M')})
            save_data(data)
            st.success("Report saved.")

    # --- PAGE: FAMILY NOTES ---
    elif page == "Family Notes":
        st.title("📝 Care Coordination Notes")
        new_note = st.text_area("Add a note for the next shift:")
        if st.button("Post Note"):
            if new_note:
                data["notes"].append({"note": new_note, "time": datetime.now().strftime('%Y-%m-%d %H:%M')})
                save_data(data)
                st.rerun()
        
        for note in reversed(data["notes"]):
            st.info(f"{note['time']}: {note['note']}")
