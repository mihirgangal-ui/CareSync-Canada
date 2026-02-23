import streamlit as st
import json
import os
from datetime import datetime
import pandas as pd

# --- CONFIG & DATA PERSISTENCE ---
DATA_FILE = "platform_data.json"

def load_data():
    default = {"users": {}, "seniors": {}, "links": {}}
    if not os.path.exists(DATA_FILE): return default
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            return {**default, **data}
    except: return default

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

st.set_page_config(page_title="CareSync Platform", page_icon="🛡️", layout="wide")
db = load_data()

if "session_user" not in st.session_state: st.session_state.session_user = None
if "active_senior_id" not in st.session_state: st.session_state.active_senior_id = None

# --- 1. AUTHENTICATION ---
if not st.session_state.session_user:
    st.title("🛡️ CareSync Canada")
    t1, t2 = st.tabs(["🔐 Login", "📝 Create Account"])
    with t2:
        with st.form("signup"):
            u_role = st.selectbox("Role", ["Caregiver", "Senior"])
            u_name = st.text_input("Full Name")
            u_email = st.text_input("Email")
            u_mob = st.text_input("Mobile Number")
            cg_tag = st.text_input("Link to Caregiver Email (Optional)")
            if st.form_submit_button("Register"):
                if u_email and u_name and u_mob:
                    db["users"][u_email] = {"name": u_name, "role": u_role}
                    if u_role == "Caregiver": db["links"][u_email] = []
                    else:
                        sid = f"S-{u_email.split('@')[0]}"
                        db["seniors"][sid] = {"name": u_name, "email": u_email, "phone": u_mob, "meds": [], "calendar": [], "notes": [], "alerts": [], "is_pro": False}
                        if cg_tag in db["links"]: db["links"][cg_tag].append(sid)
                    save_data(db); st.success("Account created!")
                else: st.error("All fields required.")
    with t1:
        l_email = st.text_input("Login Email")
        if st.button("Log In"):
            if l_email in db["users"]:
                st.session_state.session_user = {"email": l_email, **db["users"][l_email]}
                st.rerun()
            else: st.error("User not found.")

# --- 2. MAIN APP ---
else:
    u = st.session_state.session_user
    
    if u["role"] == "Caregiver":
        st.sidebar.title(f"👨‍⚕️ {u['name']}")
        
        # --- GLOBAL ALERT CENTER (For Caregiver Only) ---
        my_seniors = db["links"].get(u["email"], [])
        for sid in my_seniors:
            s_alerts = db["seniors"][sid].get("alerts", [])
            if s_alerts:
                last_alert = s_alerts[-1]["time"]
                st.sidebar.error(f"🚨 SOS: {db['seniors'][sid]['name']} at {last_alert}")

        with st.sidebar.expander("➕ Add Senior"):
            with st.form("reg_s"):
                n, m = st.text_input("Name"), st.text_input("Mobile")
                if st.form_submit_button("Create"):
                    sid = f"S-{datetime.now().strftime('%M%S')}"
                    db["seniors"][sid] = {"name": n, "phone": m, "meds": [], "calendar": [], "notes": [], "alerts": [], "is_pro": False}
                    db["links"][u["email"]].append(sid)
                    save_data(db); st.rerun()

        st.title("📋 Care Roster")
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
            st.markdown(f"--- \n ### 📍 Managing: {sdata['name']}")
            t_med, t_cal, t_pay = st.tabs(["💊 Meds", "📅 Calendar", "💎 Sub"])
            
            with t_med:
                with st.form("mf"):
                    n, f = st.text_input("Med Name"), st.text_input("Freq")
                    if st.form_submit_button("Add Med"):
                        db["seniors"][sid]["meds"].append({"name": n, "freq": f, "taken": False})
                        save_data(db); st.rerun()
                if sdata["meds"]: st.table(pd.DataFrame(sdata["meds"]))

            with t_cal:
                with st.form("cf"):
                    e, t = st.text_input("Event"), st.text_input("Time (HH:MM)")
                    if st.form_submit_button("Add Event"):
                        db["seniors"][sid]["calendar"].append({"event": e, "time": t, "arrived": False})
                        save_data(db); st.rerun()
                if sdata["calendar"]: st.table(pd.DataFrame(sdata["calendar"]))

            with t_pay:
                is_pro = sdata.get("is_pro", False)
                if not is_pro:
                    st.info("Locked: Document Vault & Shift Notes.")
                    if st.button("🚀 Upgrade to Pro", key=f"up_{sid}"):
                        db["seniors"][sid]["is_pro"] = True; save_data(db); st.rerun()
                else:
                    st.success("✅ Pro Active")
                    c1, c2 = st.columns(2)
                    with c1:
                        st.write("📁 Document Vault")
                        st.file_uploader("Upload Health Docs", key=f"v_{sid}")
                    with c2:
                        st.write("📝 Hand-off Notes")
                        note = st.text_area("Log Entry", key=f"n_{sid}")
                        if st.button("Save", key=f"s_{sid}"):
                            db["seniors"][sid]["notes"].insert(0, f"{datetime.now().strftime('%H:%M')}: {note}")
                            save_data(db); st.rerun()

    # --- SENIOR VIEW (PATCHED) ---
    else:
        sid = f"S-{u['email'].split('@')[0]}"
        if sid in db["seniors"]:
            sdata = db["seniors"][sid]
            st.title(f"👋 {u['name']}'s Dashboard")
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("💊 My Meds")
                for i, m in enumerate(sdata["meds"]):
                    if st.checkbox(f"{m['name']} ({m['freq']})", value=m["taken"], key=f"sm_{i}"):
                        db["seniors"][sid]["meds"][i]["taken"] = True; save_data(db)
            with c2:
                st.subheader("📅 My Schedule")
                for i, e in enumerate(sdata["calendar"]):
                    if st.checkbox(f"{e['event']} @ {e['time']}", value=e["arrived"], key=f"sc_{i}"):
                        db["seniors"][sid]["calendar"][i]["arrived"] = True; save_data(db)
            
            st.divider()
            if st.button("🚨 SOS", type="primary", use_container_width=True):
                db["seniors"][sid]["alerts"].append({"time": datetime.now().strftime("%H:%M:%S")})
                save_data(db); st.error("SOS SENT!")

    if st.sidebar.button("Logout"):
        st.session_state.session_user = None; st.session_state.active_senior_id = None; st.rerun()
