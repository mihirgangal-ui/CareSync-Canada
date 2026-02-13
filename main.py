import streamlit as st
import json
import os
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import pandas as pd

# --- CONFIG & SECRETS ---
ACCESS_CODE = "care"

# Using st.secrets for safety. If not set, app will show a warning instead of crashing.
def get_secret(key):
    return st.secrets.get(key, "Not Configured")

# --- DATA PERSISTENCE ---
DATA_FILE = "family_data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"events": [], "meds": [], "notes": [], "status_reports": [], "alerts": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# --- EMAIL LOGIC ---
def send_sos_email():
    sender = get_secret("EMAIL_SENDER")
    password = get_secret("EMAIL_PASSWORD")
    receiver = get_secret("EMAIL_RECEIVER")

    if "Not Configured" in [sender, password, receiver]:
        st.error("Email secrets are not configured in Streamlit Settings.")
        return False

    try:
        msg = MIMEText(f"🚨 SOS ALERT: Assistance requested via CareSync Canada at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.")
        msg['Subject'] = "🚨 CareSync SOS Emergency"
        msg['From'] = sender
        msg['To'] = receiver

        with smtplib.SMTP_SSL('smtp.gmail.com', 456) as server:
            server.login(sender, password)
            server.sendmail(sender, receiver, msg.as_string())
        return True
    except Exception as e:
        st.error(f"Failed to send email: {e}")
        return False

# --- UI SETUP ---
st.set_page_config(page_title="CareSync Canada", page_icon="🛡️", layout="wide")

# --- LOGIN GATE ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🛡️ CareSync Canada")
    st.info("Welcome to the Portfolio Demo. Please use the access code provided in the LinkedIn description.")
    
    # Use the 'hint' suggestion to make it recruiter-friendly
    entry_code = st.text_input("Enter Access Code (Hint: care):", type="password")
    
    if st.button("Access Dashboard"):
        if entry_code == ACCESS_CODE:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect code. Please check the 'care' password.")
else:
    # --- MAIN APP ---
    data = load_data()
    
    # Sidebar Navigation
    st.sidebar.title("🛡️ CareSync Menu")
    page = st.sidebar.radio("Navigate to:", ["Dashboard", "Medication Tracker", "Status Reports", "Family Notes"])
    
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.rerun()

    # --- SOS BUTTON (Always Visible in Sidebar) ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("🚨 Emergency")
    if st.sidebar.button("SEND SOS ALERT"):
        with st.spinner("Notifying Caregivers..."):
            if send_sos_email():
                st.sidebar.success("SOS Sent to Team!")
                # Log the alert in the data
                data["alerts"].append({"time": str(datetime.now()), "type": "SOS Button Pressed"})
                save_data(data)

    # --- PAGE: DASHBOARD ---
    if page == "Dashboard":
        st.title("📋 Caregiving Overview")
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Recent Meds")
            if data["meds"]:
                st.table(pd.DataFrame(data["meds"]).tail(3))
            else:
                st.write("No meds logged yet.")

        with col2:
            st.subheader("Latest Status")
            if data["status_reports"]:
                last_report = data["status_reports"][-1]
                st.metric("Patient Mood", last_report["mood"])
                st.write(f"Updated: {last_report['time']}")

    # --- PAGE: MEDICATION TRACKER ---
    elif page == "Medication Tracker":
        st.title("💊 Medication Adherence")
        with st.form("med_form"):
            name = st.text_input("Medication Name")
            dosage = st.text_input("Dosage")
            if st.form_submit_button("Log Dose"):
                data["meds"].append({"name": name, "dosage": dosage, "time": str(datetime.now())})
                save_data(data)
                st.success(f"Logged {name}")
        
        st.dataframe(pd.DataFrame(data["meds"]))

    # --- PAGE: STATUS REPORTS ---
    elif page == "Status Reports":
        st.title("📊 Daily Status")
        mood = st.select_slider("Patient Mood/Energy", options=["Low", "Fair", "Good", "Excellent"])
        appetite = st.checkbox("Ate full meals?")
        if st.button("Submit Report"):
            data["status_reports"].append({"mood": mood, "appetite": appetite, "time": str(datetime.now())})
            save_data(data)
            st.success("Report saved.")

    # --- PAGE: FAMILY NOTES ---
    elif page == "Family Notes":
        st.title("📝 Care Coordination Notes")
        new_note = st.text_area("Add a note for the next shift:")
        if st.button("Post Note"):
            data["notes"].append({"note": new_note, "time": str(datetime.now())})
            save_data(data)
            st.experimental_rerun()
        
        for note in reversed(data["notes"]):
            st.info(f"{note['time']}: {note['note']}")
