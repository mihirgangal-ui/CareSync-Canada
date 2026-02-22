import streamlit as st
import json
import os
from datetime import datetime, date
import pandas as pd

# --- CONFIG ---
DATA_FILE = "family_data.json"

# --- DATA PERSISTENCE (Self-Healing Logic) ---
def load_data():
    # This is the 'Master Schema'
    default_data = {
        "meds": [], 
        "notes": [], 
        "status_reports": [], 
        "alerts": [], 
        "docs": [], 
        "calendar": [],
        "settings": {
            "senior_name": "", 
            "caregiver_name": "", 
            "caregiver_email": "", 
            "user_role": "", 
            "is_pro": False
        }
    }
    
    if not os.path.exists(DATA_FILE):
        return default_data
    
    try:
        with open(DATA_FILE, "r") as f:
            current_data = json.load(f)
            
            # CRITICAL: Check for missing top-level keys (Fixes Line 131 KeyError)
            for key in default_data.keys():
                if key not in current_data:
                    current_data[key] = default_data[key]
            
            # Ensure settings sub-keys exist
            for s_key in default_data["settings"].keys():
                if s_key not in current_data["settings"]:
                    current_data["settings"][s_key] = default_data["settings"][s_key]
                    
            return current_data
    except:
        return default_data

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# --- UI SETUP ---
st.set_page_config(page_title="CareSync Canada", page_icon="🛡️", layout="wide")
data = load_data()

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# --- 1. LOGIN / SIGNUP ---
if not st.session_state.authenticated:
    st.title("🛡️ CareSync Canada")
    t1, t2 = st.tabs(["🔐 Sign In", "📝 Create Account"])
    with t1:
        u_email = st.text_input("Email Address", key="login_email")
        if st.button("Log In"):
            if data["settings"]["caregiver_email"] == u_email and u_email != "":
                st.session_state.authenticated = True
                st.session_state.role = data["settings"].get("user_role", "Caregiver")
                st.rerun()
            else: st.error("Account not found. Please Sign Up.")
    with t2:
        with st.form("signup"):
            sn, cn = st.text_input("Senior's Name"), st.text_input("Caregiver Name")
            ce, ur = st.text_input("Caregiver Email"), st.selectbox("Role", ["Caregiver", "Senior"])
            if st.form_submit_button("Sign Up"):
                if sn and cn and ce:
                    data["settings"] = {"senior_name": sn, "caregiver_name": cn, "caregiver_email": ce, "user_role": ur, "is_pro": False}
                    save_data(data); st.success("Account created! Now Sign In.")
                else: st.error("Please fill in all fields.")

# --- 2. THE APP INTERIOR ---
else:
    s_name = data["settings"]["senior_name"]
    is_pro = data["settings"].get("is_pro", False)
    
    if st.session_state.role == "Caregiver":
        st.sidebar.title("🩺 Caregiver Tools")
        st.sidebar.write("✨ **PRO**" if is_pro else "🆓 **FREE**")
        page = st.sidebar.radio("Navigate:", ["Dashboard", "Medication Manager", "Care Calendar", "Document Vault", "Notes", "Subscription"])
    else: 
        page = "Senior View"

    # --- MEDICATION MANAGER (Advanced) ---
    if page == "Medication Manager":
        st.title("💊 Detailed Medication Tracker")
        with st.expander("➕ Add New Medication", expanded=True):
            with st.form("med_form", clear_on_submit=True):
                m_name = st.text_input("Medication Name")
                m_freq = st.text_input("Frequency (e.g. 2x Daily)")
                c1, c2 = st.columns(2)
                m_start = c1.date_input("Start Date", value=date.today())
                m_end = c2.date_input("End Date", value=date.today())
                if st.form_submit_button("Save Medication"):
                    if m_name:
                        data["meds"].append({
                            "name": m_name, "freq": m_freq, 
                            "start": str(m_start), "end": str(m_end)
                        })
                        save_data(data); st.rerun()
                    else: st.error("Medication name is required.")
        
        if data["meds"]:
            st.table(pd.DataFrame(data["meds"]))

    # --- CARE CALENDAR (With Validation) ---
    elif page == "Care Calendar":
        st.title("📅 Care Calendar")
        with st.form("cal_form", clear_on_submit=True):
            event_name = st.text_input("Event Description")
            event_date = st.date_input("Date", value=date.today())
            if st.form_submit_button("Add Event"):
                if not event_name.strip():
                    st.error("⚠️ Event description cannot be blank.")
                else:
                    data["calendar"].append({"event": event_name, "date": str(event_date)})
                    save_data(data); st.success("Added!"); st.rerun()
        
        for ev in reversed(data["calendar"]):
            st.info(f"**{ev['date']}**: {ev['event']}")

    # --- DASHBOARD (Fix for Line 131) ---
    elif page == "Dashboard":
        st.title(f"📋 {s_name}'s Hub")
        m1, m2, m3 = st.columns(3)
        # These now have the repair logic protecting them
        m1.metric("Meds", len(data.get("meds", [])))
        m2.metric("Events", len(data.get("calendar", [])))
        m3.metric("Status", "Pro" if is_pro else "Free")
        
        st.markdown("---")
        if data["alerts"]:
            st.subheader("🚨 Recent Alerts")
            for a in reversed(data["alerts"][-3:]): st.warning(f"{a['type']} at {a['time']}")

    # --- SENIOR VIEW ---
    elif page == "Senior View":
        st.title(f"👋 Hello {s_name}")
        mood = st.select_slider("How are you feeling?", options=["Low", "Ok", "Good", "Great"])
        if st.button("Update Family"):
            data["status_reports"].append({"mood": mood, "time": datetime.now().strftime("%H:%M")})
            save_data(data); st.success("Updated!")
        
        if st.button("🚨 I NEED HELP", use_container_width=True, type="primary"):
            data["alerts"].append({"time": datetime.now().strftime("%H:%M"), "type": "SOS Alert"})
            save_data(data); st.error("Alert Sent!")
        
        if st.button("Logout"):
            st.session_state.authenticated = False; st.rerun()

    # --- REMAINING PAGES ---
    elif page == "Subscription":
        st.title("💎 Membership")
        c1, c2 = st.columns(2)
        c1.info("Free Tier")
        with c2:
            st.success("Pro Tier ($9.99/mo)")
            if st.button("🚀 UPGRADE" if not is_pro else "DOWNGRADE"):
                data["settings"]["is_pro"] = not is_pro
                save_data(data); st.rerun()

    elif page == "Document Vault":
        st.title("📂 Vault")
        if not is_pro: st.error("🔒 Pro Feature.")
        else:
            up = st.file_uploader("Upload")
            if up:
                data["docs"].append({"name": up.name, "date": str(date.today())})
                save_data(data); st.rerun()
            if data["docs"]: st.table(pd.DataFrame(data["docs"]))

    elif page == "Notes":
        st.title("📝 Notes")
        nt = st.text_area("Update:")
        if st.button("Post"):
            if nt:
                data["notes"].append({"note": nt, "time": datetime.now().strftime("%H:%M")})
                save_data(data); st.rerun()
            else: st.error("Cannot be empty.")
        for n in reversed(data["notes"]): st.info(n['note'])

    st.sidebar.markdown("---")
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False; st.rerun()
