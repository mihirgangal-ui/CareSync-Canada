import streamlit as st
import json
import os
from datetime import datetime
import pandas as pd

# --- CONFIG ---
ACCESS_CODE = "care"
DATA_FILE = "family_data.json"

# --- BULLETPROOF DATA LOADING ---
def load_data():
    default_settings = {"caregiver_name": "Family Member", "caregiver_email": "family@example.com", "senior_name": "Senior"}
    default_data = {
        "meds": [], "notes": [], "status_reports": [], 
        "alerts": [], "docs": [], "calendar": [],
        "settings": default_settings
    }
    
    if not os.path.exists(DATA_FILE):
        return default_data
    
    try:
        with open(DATA_FILE, "r") as f:
            current_data = json.load(f)
            # Safety check: if a new key is missing in the file, add the default empty list/dict
            for key in default_data:
                if key not in current_data:
                    current_data[key] = default_data[key]
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

# --- LOGIN GATE ---
if not st.session_state.authenticated:
    st.title("🛡️ CareSync Canada")
    st.markdown("### **Family Care Management System**")
    entry_code = st.text_input("Access Code (care):", type="password")
    if st.button("Access Dashboard"):
        if entry_code == ACCESS_CODE:
            st.session_state.authenticated = True
            st.rerun()
else:
    data = load_data()
    s_name = data["settings"].get("senior_name", "Senior")
    c_name = data["settings"].get("caregiver_name", "Caregiver")
    
    if st.session_state.role is None:
        st.header("Select Interface")
        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"👵 {s_name.upper()}'S VIEW", use_container_width=True):
                st.session_state.role = "Senior"; st.rerun()
        with col2:
            if st.button("🩺 CAREGIVER VIEW", use_container_width=True):
                st.session_state.role = "Caregiver"; st.rerun()
    
    else:
        # --- SIDEBAR NAV ---
        if st.session_state.role == "Caregiver":
            st.sidebar.title("🩺 Caregiver Tools")
            page = st.sidebar.radio("Navigate to:", 
                ["Dashboard", "Medication Manager", "Editable Calendar", "Document Vault", "Coordination Notes", "Intake & Settings"])
        else:
            page = "Senior View"

        # --- FEATURE: INTAKE & SETTINGS ---
        if page == "Intake & Settings":
            st.title("⚙️ System Intake")
            with st.form("settings_form"):
                new_s = st.text_input("Senior's Name", value=s_name)
                new_c = st.text_input("Primary Caregiver Name", value=c_name)
                new_e = st.text_input("Alert Email", value=data["settings"].get("caregiver_email", ""))
                if st.form_submit_button("Update Profile"):
                    data["settings"] = {"senior_name": new_s, "caregiver_name": new_c, "caregiver_email": new_e}
                    save_data(data); st.success("Profile Updated"); st.rerun()

        # --- FEATURE: DASHBOARD ---
        elif page == "Dashboard":
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
                else: st.info("No reports.")
            with col_b:
                st.subheader("🚨 Recent Alerts")
                if data["alerts"]:
                    for a in reversed(data["alerts"][-3:]): st.warning(f"{a['type']} at {a['time']}")

        # --- FEATURE: MEDICATION MANAGER ---
        elif page == "Medication Manager":
            st.title("💊 Medications")
            with st.expander("Add Med"):
                with st.form("m_form"):
                    n = st.text_input("Name")
                    f = st.selectbox("Freq", ["Daily", "Weekly", "As needed"])
                    if st.form_submit_button("Save"):
                        data["meds"].append({"name": n, "freq": f, "start": str(datetime.now().date())})
                        save_data(data); st.rerun()
            for i, m in enumerate(data["meds"]):
                c = st.columns([4, 1])
                c[0].write(f"**{m['name']}** - {m['freq']}")
                if c[1].button("🗑️", key=f"m_{i}"):
                    data["meds"].pop(i); save_data(data); st.rerun()

        # --- FEATURE: EDITABLE CALENDAR ---
        elif page == "Editable Calendar":
            st.title("📅 Calendar")
            with st.form("c_form"):
                e = st.text_input("Event")
                d = st.date_input("Date")
                if st.form_submit_button("Add"):
                    data["calendar"].append({"event": e, "date": str(d)})
                    save_data(data); st.rerun()
            for i, ev in enumerate(data["calendar"]):
                c = st.columns([4, 1])
                c[0].write(f"{ev['date']}: {ev['event']}")
                if c[1].button("🗑️", key=f"e_{i}"):
                    data["calendar"].pop(i); save_data(data); st.rerun()

        # --- FEATURE: SENIOR VIEW ---
        elif page == "Senior View":
            st.title(f"👋 Hello {s_name}")
            mood = st.select_slider("How are you?", options=["Low", "Ok", "Good", "Great"])
            if st.button("Tell Family"):
                data["status_reports"].append({"mood": mood, "time": datetime.now().strftime("%H:%M")})
                save_data(data); st.success("Updated!")
            
            if st.button("🚨 I NEED HELP", use_container_width=True, type="primary"):
                msg = f"HELP REQUEST: {s_name} needs assistance!"
                data["alerts"].append({"time": datetime.now().strftime("%H:%M"), "type": msg})
                save_data(data); st.error(msg)

        # --- REMAINING PAGES ---
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
