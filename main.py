import streamlit as st
import json
import os
from datetime import datetime, date
import pandas as pd

# --- CONFIG ---
DATA_FILE = "family_data.json"

# --- DATA PERSISTENCE ---
def load_data():
    default_data = {
        "meds": [], "notes": [], "status_reports": [], 
        "alerts": [], "docs": [], "calendar": [],
        "settings": {"senior_name": "", "caregiver_name": "", "caregiver_email": "", "user_role": "", "is_pro": False}
    }
    if not os.path.exists(DATA_FILE): return default_data
    try:
        with open(DATA_FILE, "r") as f:
            current_data = json.load(f)
            # Ensure "settings" exists and is populated
            if "settings" not in current_data: current_data["settings"] = default_data["settings"]
            for key in default_data["settings"]:
                if key not in current_data["settings"]: current_data["settings"][key] = default_data["settings"][key]
            return current_data
    except: return default_data

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
            else: st.error("Account not found.")
    with t2:
        with st.form("signup"):
            sn, cn = st.text_input("Senior's Name"), st.text_input("Caregiver Name")
            ce, ur = st.text_input("Caregiver Email"), st.selectbox("Role", ["Caregiver", "Senior"])
            if st.form_submit_button("Sign Up"):
                if sn and cn and ce:
                    data["settings"] = {"senior_name": sn, "caregiver_name": cn, "caregiver_email": ce, "user_role": ur, "is_pro": False}
                    save_data(data); st.success("Created! Now Sign In.")
                else: st.error("All fields required.")

# --- 2. MAIN APP ---
else:
    s_name = data["settings"]["senior_name"]
    is_pro = data["settings"].get("is_pro", False)
    
    if st.session_state.role == "Caregiver":
        st.sidebar.title("🩺 Caregiver Tools")
        st.sidebar.write("✨ **PRO**" if is_pro else "🆓 **FREE**")
        page = st.sidebar.radio("Navigate:", ["Dashboard", "Medication Manager", "Care Calendar", "Document Vault", "Notes", "Subscription"])
    else: page = "Senior View"

    # --- MEDICATION MANAGER (Advanced) ---
    if page == "Medication Manager":
        st.title("💊 Detailed Medication Tracker")
        with st.expander("➕ Add New Medication", expanded=True):
            with st.form("med_form", clear_on_submit=True):
                m_name = st.text_input("Medication Name (e.g., Metformin)")
                m_freq = st.text_input("Frequency (e.g., Twice daily after meals)")
                c1, c2 = st.columns(2)
                m_start = c1.date_input("Start Date", value=date.today())
                m_end = c2.date_input("End Date (Optional)", value=date.today())
                if st.form_submit_button("Save Medication"):
                    if m_name:
                        data["meds"].append({
                            "name": m_name, "freq": m_freq, 
                            "start": str(m_start), "end": str(m_end)
                        })
                        save_data(data); st.rerun()
                    else: st.error("Please enter a medication name.")
        
        if data["meds"]:
            df_meds = pd.DataFrame(data["meds"])
            st.dataframe(df_meds, use_container_width=True)

    # --- CARE CALENDAR (With Validation) ---
    elif page == "Care Calendar":
        st.title("📅 Care Calendar")
        with st.form("cal_form", clear_on_submit=True):
            event_name = st.text_input("Event Description")
            event_date = st.date_input("Date", value=date.today())
            event_time = st.time_input("Time")
            if st.form_submit_button("Add Event"):
                if not event_name.strip():
                    st.error("⚠️ Event description cannot be blank.")
                else:
                    data["calendar"].append({"event": event_name, "date": str(event_date), "time": str(event_time)})
                    save_data(data); st.success("Event Added!"); st.rerun()
        
        for i, ev in enumerate(reversed(data["calendar"])):
            st.info(f"**{ev['date']} @ {ev.get('time', 'N/A')}**: {ev['event']}")

    # --- SENIOR VIEW ---
    elif page == "Senior View":
        st.title(f"👋 Hello {s_name}")
        mood = st.select_slider("How are you feeling?", options=["Low", "Ok", "Good", "Great"])
        if st.button("Update Family"):
            data["status_reports"].append({"mood": mood, "time": datetime.now().strftime("%H:%M")})
            save_data(data); st.success("Sent!")
        
        if st.button("🚨 I NEED HELP", use_container_width=True, type="primary"):
            data["alerts"].append({"time": datetime.now().strftime("%H:%M"), "type": "SOS Request"})
            save_data(data); st.error("Family Notified!")
        if st.button("Logout"):
            st.session_state.authenticated = False; st.rerun()

    # --- DASHBOARD & OTHER ---
    elif page == "Dashboard":
        st.title(f"📋 {s_name}'s Hub")
        cols = st.columns(3)
        cols[0].metric("Meds", len(data["meds"]))
        cols[1].metric("Events", len(data["calendar"]))
        cols[2].metric("Status", "Pro" if is_pro else "Free")
        if data["alerts"]:
            st.subheader("🚨 Recent Alerts")
            for a in reversed(data["alerts"][-3:]): st.warning(f"{a['type']} at {a['time']}")

    elif page == "Subscription":
        st.title("💎 Membership Plans")
        c1, c2 = st.columns(2)
        c1.info("### **Free Tier**\nBasic Logs & Calendar")
        with c2:
            st.success("### **Pro Tier ($9.99/mo)**\nUnlimited Vault & Shift Notes")
            if st.button("🚀 UPGRADE" if not is_pro else "DOWNGRADE"):
                data["settings"]["is_pro"] = not is_pro
                save_data(data); st.rerun()

    elif page == "Document Vault":
        st.title("📂 Vault")
        if not is_pro: st.error("🔒 Pro Feature: Upgrade to unlock.")
        else:
            up = st.file_uploader("Upload Record")
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
            else: st.error("Note cannot be empty.")
        for n in reversed(data["notes"]): st.info(n['note'])

    st.sidebar.markdown("---")
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False; st.rerun()
