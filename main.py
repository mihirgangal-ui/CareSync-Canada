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
    default_data = {
        "meds": [], "notes": [], "status_reports": [], 
        "alerts": [], "docs": [], "calendar": [],
        "settings": None # We set this to None to trigger onboarding
    }
    if not os.path.exists(DATA_FILE):
        return default_data
    try:
        with open(DATA_FILE, "r") as f:
            current_data = json.load(f)
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

# --- 1. LOGIN GATE ---
if not st.session_state.authenticated:
    st.title("🛡️ CareSync Canada")
    st.markdown("### **Family Care Management System**\n*Enter 'care' to begin the setup demo.*")
    entry_code = st.text_input("Access Code:", type="password")
    if st.button("Enter"):
        if entry_code == ACCESS_CODE:
            st.session_state.authenticated = True
            st.rerun()

else:
    data = load_data()

    # --- 2. ONBOARDING / INTAKE WIZARD ---
    # If settings don't exist, we force the user through intake first
    if data["settings"] is None:
        st.title("⚙️ CareSync Setup Wizard")
        st.write("Welcome! Let's personalize your care dashboard.")
        
        with st.form("intake_form"):
            st.subheader("Profile Information")
            s_name = st.text_input("Who is being cared for? (Senior's Name)", placeholder="e.g. Robert")
            c_name = st.text_input("Primary Caregiver Name", placeholder="e.g. Jane Doe")
            c_email = st.text_input("Emergency Notification Email", placeholder="caregiver@example.com")
            
            submit = st.form_submit_button("Complete Setup & Launch Dashboard")
            
            if submit:
                if s_name and c_name:
                    data["settings"] = {
                        "senior_name": s_name,
                        "caregiver_name": c_name,
                        "caregiver_email": c_email
                    }
                    save_data(data)
                    st.success("Profile created!")
                    st.rerun()
                else:
                    st.warning("Please provide names to personalize the experience.")

    # --- 3. MAIN DASHBOARD ---
    else:
        s_name = data["settings"]["senior_name"]
        
        if "role" not in st.session_state or st.session_state.role is None:
            st.header(f"Welcome to {s_name}'s Care Hub")
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"👵 {s_name.upper()}'S VIEW", use_container_width=True):
                    st.session_state.role = "Senior"; st.rerun()
            with col2:
                if st.button("🩺 CAREGIVER VIEW", use_container_width=True):
                    st.session_state.role = "Caregiver"; st.rerun()
        
        else:
            # Navigation logic for Caregiver
            if st.session_state.role == "Caregiver":
                st.sidebar.title("🩺 Caregiver Tools")
                page = st.sidebar.radio("Navigate to:", 
                    ["Dashboard", "Medication Manager", "Editable Calendar", "Document Vault", "Coordination Notes"])
                
                if st.sidebar.button("Reset App (Delete Profile)"):
                    data["settings"] = None
                    save_data(data)
                    st.session_state.role = None
                    st.rerun()
            else:
                page = "Senior View"

            # --- FEATURES ---
            if page == "Dashboard":
                st.title(f"📋 {s_name}'s Command Centre")
                m1, m2, m3 = st.columns(3)
                m1.metric("Meds", len(data["meds"]))
                m2.metric("Events", len(data["calendar"]))
                m3.metric("Docs", len(data["docs"]))
                
                st.markdown("---")
                col_a, col_b = st.columns(2)
                with col_a:
                    st.subheader("📊 Health Status")
                    if data["status_reports"]:
                        st.success(f"Latest Mood: {data['status_reports'][-1]['mood']}")
                    else: st.info("No reports yet.")
                with col_b:
                    st.subheader("🚨 Recent Alerts")
                    if data["alerts"]:
                        for a in reversed(data["alerts"][-3:]): st.warning(f"{a['type']} at {a['time']}")

            elif page == "Senior View":
                st.title(f"👋 Hello {s_name}")
                mood = st.select_slider("How are you feeling?", options=["Low", "Ok", "Good", "Great"])
                if st.button("Update Family"):
                    data["status_reports"].append({"mood": mood, "time": datetime.now().strftime("%H:%M")})
                    save_data(data); st.success("Updated!")
                
                if st.button("🚨 I NEED HELP", use_container_width=True, type="primary"):
                    msg = f"HELP REQUEST: {s_name} needs assistance!"
                    data["alerts"].append({"time": datetime.now().strftime("%H:%M"), "type": msg})
                    save_data(data); st.error(msg)

            # (The other features like Meds, Calendar, Vault, and Notes remain the same)
            elif page == "Medication Manager":
                st.title("💊 Medication Log")
                with st.form("m_form"):
                    n = st.text_input("Medication Name")
                    f = st.text_input("Frequency")
                    if st.form_submit_button("Save"):
                        data["meds"].append({"name": n, "freq": f})
                        save_data(data); st.rerun()
                for i, m in enumerate(data["meds"]):
                    st.write(f"**{m['name']}** - {m['freq']}")

            elif page == "Editable Calendar":
                st.title("📅 Calendar")
                with st.form("c_form"):
                    e = st.text_input("Appointment")
                    d = st.date_input("Date")
                    if st.form_submit_button("Add"):
                        data["calendar"].append({"event": e, "date": str(d)})
                        save_data(data); st.rerun()
                for i, ev in enumerate(data["calendar"]):
                    st.write(f"{ev['date']}: {ev['event']}")

            elif page == "Document Vault":
                st.title("📂 Vault")
                up = st.file_uploader("Upload")
                if up:
                    data["docs"].append({"name": up.name, "date": str(datetime.now().date())})
                    save_data(data); st.success("Saved.")
                if data["docs"]: st.table(pd.DataFrame(data["docs"]))

            elif page == "Coordination Notes":
                st.title("📝 Notes")
                nt = st.text_area("Update:")
                if st.button("Post"):
                    data["notes"].append({"note": nt, "time": datetime.now().strftime("%H:%M")})
                    save_data(data); st.rerun()
                for n in reversed(data["notes"]): st.info(f"{n['time']}: {n['note']}")

            st.sidebar.markdown("---")
            if st.sidebar.button("Logout / Switch View"):
                st.session_state.role = None
                st.session_state.authenticated = False; st.rerun()
