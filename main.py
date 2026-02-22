import streamlit as st
import json
import os
from datetime import datetime, date
import pandas as pd

# --- CONFIG ---
DATA_FILE = "platform_data.json"

# --- DATA PERSISTENCE (Multi-Tenant & Safe) ---
def load_data():
    default_structure = {"users": {}, "seniors": {}, "links": {}}
    if not os.path.exists(DATA_FILE): return default_structure
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            # Ensure top-level keys exist
            for key in default_structure.keys():
                if key not in data: data[key] = default_structure[key]
            return data
    except: return default_structure

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# --- UI SETUP ---
st.set_page_config(page_title="CareSync Platform", page_icon="🛡️", layout="wide")
db = load_data()

if "session_user" not in st.session_state: st.session_state.session_user = None
if "active_senior_id" not in st.session_state: st.session_state.active_senior_id = None

# --- 1. AUTHENTICATION & ONBOARDING ---
if not st.session_state.session_user:
    st.title("🛡️ CareSync Canada: Network Edition")
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Create Account"])
    
    with tab2:
        with st.form("signup"):
            u_role = st.selectbox("I am a...", ["Caregiver", "Senior"])
            u_email = st.text_input("Email")
            u_name = st.text_input("Full Name")
            if st.form_submit_button("Register"):
                if u_email and u_name:
                    db["users"][u_email] = {"name": u_name, "role": u_role}
                    if u_role == "Caregiver":
                        db["links"][u_email] = []
                    else:
                        s_id = f"S-{u_email.split('@')[0]}"
                        # Preserving all fields from previous versions + new contact info
                        db["seniors"][s_id] = {
                            "name": u_name, "email": u_email, "phone": "", 
                            "meds": [], "calendar": [], "notes": [], 
                            "alerts": [], "docs": [], "is_pro": False
                        }
                    save_data(db); st.success("Registered! Now Log In.")
                else: st.error("Fields cannot be empty.")

    with tab1:
        l_email = st.text_input("Email")
        if st.button("Log In"):
            if l_email in db["users"]:
                st.session_state.session_user = {"email": l_email, **db["users"][l_email]}
                st.rerun()
            else: st.error("Account not found.")

# --- 2. MAIN APP ---
else:
    u = st.session_state.session_user
    
    # --- CAREGIVER VIEW ---
    if u["role"] == "Caregiver":
        st.sidebar.title(f"👨‍⚕️ {u['name']}")
        
        # ADD NEW SENIOR
        with st.sidebar.expander("➕ Register New Senior"):
            ns_name = st.text_input("Senior's Name")
            ns_phone = st.text_input("Senior's Phone")
            if st.button("Create Profile"):
                sid = f"S-{datetime.now().strftime('%M%S')}"
                db["seniors"][sid] = {
                    "name": ns_name, "email": "", "phone": ns_phone, 
                    "meds": [], "calendar": [], "notes": [], 
                    "alerts": [], "docs": [], "is_pro": False
                }
                db["links"][u["email"]].append(sid)
                save_data(db); st.rerun()

        # SELECT SENIOR
        st.title("📋 Care Roster")
        my_seniors = db["links"].get(u["email"], [])
        
        if not my_seniors:
            st.info("No seniors managed yet. Add one in the sidebar.")
        else:
            cols = st.columns(3)
            for idx, sid in enumerate(my_seniors):
                sdata = db["seniors"][sid]
                with cols[idx % 3]:
                    st.markdown(f"### {sdata['name']}")
                    st.write(f"📞 {sdata['phone']}")
                    if st.button(f"Manage {sdata['name']}", key=sid):
                        st.session_state.active_senior_id = sid
                        st.rerun()

        # ACTIVE MANAGEMENT AREA
        if st.session_state.active_senior_id:
            sid = st.session_state.active_senior_id
            sdata = db["seniors"][sid]
            st.markdown("---")
            st.header(f"📍 Managing: {sdata['name']}")
            
            t_med, t_cal, t_pay = st.tabs(["💊 Med Tracker", "📅 Calendar", "💎 Subscription"])
            
            with t_med:
                with st.expander("Add Medication", expanded=False):
                    with st.form("med_form", clear_on_submit=True):
                        n = st.text_input("Medication Name")
                        f = st.text_input("Frequency (e.g., Daily)")
                        c1, c2 = st.columns(2)
                        s = c1.date_input("Start Date")
                        e = c2.date_input("End Date")
                        if st.form_submit_button("Save"):
                            db["seniors"][sid]["meds"].append({
                                "name": n, "freq": f, "start": str(s), "end": str(e), "taken": False
                            })
                            save_data(db); st.rerun()
                if sdata["meds"]: st.table(pd.DataFrame(sdata["meds"]))

            with t_cal:
                with st.form("cal_form"):
                    ev = st.text_input("Appointment/Event")
                    loc = st.text_input("Location")
                    dt = st.date_input("Date")
                    tm = st.time_input("Time")
                    if st.form_submit_button("Add Event"):
                        if ev.strip():
                            db["seniors"][sid]["calendar"].append({
                                "event": ev, "date": str(dt), "time": str(tm), "loc": loc, "arrived": False
                            })
                            save_data(db); st.rerun()
                if sdata["calendar"]: st.table(pd.DataFrame(sdata["calendar"]))

            with t_pay:
                st.subheader("Premium Monetization")
                st.write("Unlock for this senior:")
                st.markdown("* **Document Vault** (Secure IP)\n* **Coordination Notes** (Team Sync)\n* **SOS Priority Routing**")
                if st.button("🚀 Upgrade to Pro" if not sdata["is_pro"] else "Revert Plan"):
                    db["seniors"][sid]["is_pro"] = not sdata["is_pro"]
                    save_data(db); st.rerun()

    # --- SENIOR VIEW (Adherence & Loop Closing) ---
    else:
        s_id = f"S-{u['email'].split('@')[0]}"
        if s_id not in db["seniors"]:
            st.error("Please contact your caregiver to link your account.")
        else:
            sdata = db["seniors"][s_id]
            st.title(f"👵 {u['name']}'s Task List")
            
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("💊 Meds")
                for i, m in enumerate(sdata["meds"]):
                    status = "✅" if m.get("taken") else "⏳"
                    if st.checkbox(f"{status} {m['name']} ({m['freq']})", key=f"m_{i}", value=m.get("taken")):
                        db["seniors"][s_id]["meds"][i]["taken"] = True
                        save_data(db)
            
            with c2:
                st.subheader("📅 Schedule")
                for i, e in enumerate(sdata["calendar"]):
                    status = "✅" if e.get("arrived") else "📍"
                    if st.checkbox(f"{status} {e['event']} @ {e['time']}", key=f"e_{i}", value=e.get("arrived")):
                        db["seniors"][s_id]["calendar"][i]["arrived"] = True
                        save_data(db)

            st.markdown("---")
            if st.button("🚨 SOS: ALERT FAMILY", type="primary", use_container_width=True):
                db["seniors"][s_id]["alerts"].append({"time": str(datetime.now())})
                save_data(db); st.error("Emergency Alert Sent!")

    if st.sidebar.button("Logout"):
        st.session_state.session_user = None; st.session_state.active_senior_id = None; st.rerun()
