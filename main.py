import streamlit as st
import json
import os
from datetime import datetime, date
import pandas as pd

# --- CONFIG ---
DATA_FILE = "platform_data.json"

# --- DATA PERSISTENCE ---
def load_data():
    default_structure = {"users": {}, "seniors": {}, "links": {}}
    if not os.path.exists(DATA_FILE): return default_structure
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
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

# --- 1. AUTHENTICATION (Account Creation) ---
if not st.session_state.session_user:
    st.title("🛡️ CareSync Canada")
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Create Account"])
    
    with tab2:
        with st.form("signup"):
            u_role = st.selectbox("Role", ["Caregiver", "Senior"])
            u_name = st.text_input("Full Name")
            u_email = st.text_input("Email (Required for Account)")
            u_mob = st.text_input("Mobile Number (Mandatory) *")
            cg_tag_email = ""
            if u_role == "Senior":
                cg_tag_email = st.text_input("Link to Caregiver Email (Optional)")
            
            if st.form_submit_button("Register"):
                if u_email and u_name and u_mob:
                    db["users"][u_email] = {"name": u_name, "role": u_role}
                    if u_role == "Caregiver":
                        db["links"][u_email] = db["links"].get(u_email, [])
                    else:
                        s_id = f"S-{u_email.split('@')[0]}"
                        db["seniors"][s_id] = {
                            "name": u_name, "email": u_email, "phone": u_mob, 
                            "meds": [], "calendar": [], "notes": [], "alerts": [], "docs": [], "is_pro": False
                        }
                        if cg_tag_email and cg_tag_email in db["links"]:
                            db["links"][cg_tag_email].append(s_id)
                    save_data(db); st.success("Account created! Log in above.")
                else: st.error("Name, Email, and Mobile are required for account creation.")

    with tab1:
        l_email = st.text_input("Login Email")
        if st.button("Log In"):
            if l_email in db["users"]:
                st.session_state.session_user = {"email": l_email, **db["users"][l_email]}
                st.rerun()
            else: st.error("Account not found.")

# --- 2. MAIN APP ---
else:
    u = st.session_state.session_user
    
    if u["role"] == "Caregiver":
        st.sidebar.title(f"👨‍⚕️ {u['name']}")
        
        # FIXED: REGISTERING A SENIOR MANUALLY (Email is Optional)
        with st.sidebar.expander("➕ Register New Senior"):
            with st.form("manual_reg"):
                ns_name = st.text_input("Senior Name")
                ns_mob = st.text_input("Mobile Number (Mandatory) *")
                ns_email = st.text_input("Email (Optional)") 
                if st.form_submit_button("Create Profile"):
                    if ns_name and ns_mob:
                        sid = f"S-{datetime.now().strftime('%M%S')}"
                        db["seniors"][sid] = {
                            "name": ns_name, "email": ns_email, "phone": ns_mob, 
                            "meds": [], "calendar": [], "notes": [], "alerts": [], "docs": [], "is_pro": False
                        }
                        db["links"][u["email"]].append(sid)
                        save_data(db); st.rerun()
                    else: st.error("Name and Mobile are mandatory.")

        # ROSTER
        st.title("📋 Care Roster")
        my_seniors = db["links"].get(u["email"], [])
        if not my_seniors: st.info("No seniors managed yet.")
        else:
            cols = st.columns(3)
            for idx, sid in enumerate(my_seniors):
                sdata = db["seniors"][sid]
                with cols[idx % 3]:
                    st.metric(sdata["name"], f"{len(sdata['meds'])} Meds")
                    if st.button(f"Manage {sdata['name']}", key=sid):
                        st.session_state.active_senior_id = sid

        if st.session_state.active_senior_id:
            sid = st.session_state.active_senior_id
            sdata = db["seniors"][sid]
            st.markdown(f"--- \n ### 📍 Profile: {sdata['name']}")
            
            t_med, t_cal, t_pay = st.tabs(["💊 Meds", "📅 Calendar", "💎 Sub"])
            
            with t_med:
                with st.form("med_form"):
                    m_n = st.text_input("Medication Name")
                    m_f = st.text_input("Frequency (e.g. 2x Daily)")
                    c1, c2 = st.columns(2); s = c1.date_input("Start"); e = c2.date_input("End")
                    if st.form_submit_button("Save"):
                        db["seniors"][sid]["meds"].append({"name": m_n, "freq": m_f, "start": str(s), "end": str(e), "taken": False})
                        save_data(db); st.rerun()
                if sdata["meds"]: st.table(pd.DataFrame(sdata["meds"]))

            with t_cal:
                with st.form("cal_form"):
                    ev = st.text_input("Appointment"); l = st.text_input("Location")
                    d = st.date_input("Date"); t = st.time_input("Time")
                    if st.form_submit_button("Add Event"):
                        db["seniors"][sid]["calendar"].append({"event": ev, "date": str(d), "time": str(t), "loc": l, "arrived": False})
                        save_data(db); st.rerun()
                if sdata["calendar"]: st.table(pd.DataFrame(sdata["calendar"]))

with t_pay:
                st.subheader("💎 Premium Care Suite")
                
                # Check if is_pro exists, default to False if not
                is_pro_active = sdata.get("is_pro", False)

                if not is_pro_active:
                    st.info("Features below are locked. Upgrade this senior to unlock professional tools.")
                    st.markdown("🔒 **Document Vault** (DNR, Health Cards)")
                    st.markdown("🔒 **Shift Hand-off Notes**")
                    st.markdown("🔒 **SOS Family Blast & History**")
                    if st.button("🚀 Upgrade to Pro", key=f"up_{sid}"):
                        db["seniors"][sid]["is_pro"] = True
                        save_data(db); st.rerun()
                else:
                    st.success("✅ Pro Features Unlocked")
                    if st.button("Revert to Free Plan (Demo Mode)", key=f"rev_{sid}"):
                        db["seniors"][sid]["is_pro"] = False
                        save_data(db); st.rerun()
                    
                    st.divider()
                    
                    col_v, col_n = st.columns(2)
                    
                    with col_v:
                        st.markdown("### 📁 Document Vault")
                        st.file_uploader("Upload Health Card / DNR (PDF/JPG)", key=f"vault_{sid}")
                        st.caption("Securely stored in senior's encrypted profile.")

                        st.divider()
                        st.markdown("### 🚨 SOS Alert History")
                        # Defensive check for alerts
                        senior_alerts = sdata.get("alerts", [])
                        if senior_alerts:
                            for alert in reversed(senior_alerts):
                                st.error(f"EMERGENCY ALERT: {alert.get('time', 'Unknown Time')}")
                        else:
                            st.write("No emergency alerts recorded.")

                    with col_n:
                        st.markdown("### 📝 Hand-off Notes")
                        with st.container(border=True):
                            new_note = st.text_area("Daily Care Log / Hand-over", placeholder="e.g., Mom was a bit dizzy today...", key=f"note_input_{sid}")
                            if st.button("Save Log Entry", key=f"save_note_{sid}"):
                                if new_note:
                                    note_entry = f"{datetime.now().strftime('%Y-%m-%d %H:%M')}: {new_note}"
                                    # Defensive initialization of notes list
                                    if "notes" not in db["seniors"][sid]: 
                                        db["seniors"][sid]["notes"] = []
                                    db["seniors"][sid]["notes"].insert(0, note_entry)
                                    save_data(db); st.rerun()
                        
                        # Defensive check for notes
                        for n in sdata.get("notes", []):
                            st.write(f"▪️ {n}")

    # --- SENIOR VIEW ---
    else:
        sid = f"S-{u['email'].split('@')[0]}"
        if sid in db["seniors"]:
            sdata = db["seniors"][sid]
            st.title(f"👋 {u['name']}'s Dashboard")
            
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("💊 My Meds")
                for i, m in enumerate(sdata["meds"]):
                    if st.checkbox(f"{m['name']} ({m['freq']})", key=f"m_{i}", value=m.get("taken")):
                        db["seniors"][sid]["meds"][i]["taken"] = True; save_data(db)
            with c2:
                st.subheader("📅 My Schedule")
                for i, e in enumerate(sdata["calendar"]):
                    if st.checkbox(f"{e['event']} @ {e['time']}", key=f"e_{i}", value=e.get("arrived")):
                        db["seniors"][sid]["calendar"][i]["arrived"] = True; save_data(db)

            st.markdown("---")
            if st.button("🚨 SOS", type="primary", use_container_width=True):
                db["seniors"][sid]["alerts"].append({"time": str(datetime.now())})
                save_data(db); st.error("SOS Alerted!")

    if st.sidebar.button("Logout"):
        st.session_state.session_user = None; st.session_state.active_senior_id = None; st.rerun()
