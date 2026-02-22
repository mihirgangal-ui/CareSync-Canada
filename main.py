import streamlit as st
import json
import os
from datetime import datetime, date
import pandas as pd

# --- CONFIG ---
DATA_FILE = "platform_data.json"

# --- DATA PERSISTENCE (Multi-Tenant Logic) ---
def load_data():
    default_structure = {
        "users": {}, # {email: {name, role}}
        "seniors": {}, # {id: {name, meds:[], calendar:[], notes:[], alerts:[], docs:[], is_pro: False}}
        "links": {} # {caregiver_email: [senior_ids]}
    }
    if not os.path.exists(DATA_FILE): return default_structure
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            # Self-healing logic for the new schema
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
                        s_id = f"S-{u_email.split('@')[0]}" # Unique ID based on email
                        db["seniors"][s_id] = {
                            "name": u_name, "meds": [], "calendar": [], 
                            "notes": [], "alerts": [], "docs": [], "is_pro": False
                        }
                    save_data(db); st.success("Registered! Please Log In.")
                else: st.error("All fields required.")

    with tab1:
        l_email = st.text_input("Email")
        if st.button("Log In"):
            if l_email in db["users"]:
                st.session_state.session_user = {"email": l_email, **db["users"][l_email]}
                st.rerun()
            else: st.error("User not found.")

# --- 2. THE APP INTERIOR ---
else:
    u = st.session_state.session_user
    
    # --- CAREGIVER DASHBOARD (The Roster) ---
    if u["role"] == "Caregiver":
        st.sidebar.title(f"👨‍⚕️ {u['name']}")
        
        # 1. ADD NEW SENIOR (Caregiver creates a profile)
        with st.sidebar.expander("➕ Register New Senior"):
            new_s_name = st.text_input("Senior's Name")
            if st.button("Create Profile"):
                new_id = f"S-{datetime.now().strftime('%M%S')}"
                db["seniors"][new_id] = {
                    "name": new_s_name, "meds": [], "calendar": [], 
                    "notes": [], "alerts": [], "docs": [], "is_pro": False
                }
                db["links"][u["email"]].append(new_id)
                save_data(db); st.rerun()

        # 2. SELECT FROM ROSTER
        st.title("📋 My Senior Roster")
        my_seniors = db["links"].get(u["email"], [])
        
        if not my_seniors:
            st.info("You haven't added any seniors yet. Use the sidebar to begin.")
        else:
            cols = st.columns(3)
            for idx, s_id in enumerate(my_seniors):
                with cols[idx % 3]:
                    s_data = db["seniors"][s_id]
                    st.markdown(f"### {s_data['name']}")
                    st.write(f"💊 Meds: {len(s_data['meds'])} | 📅 Events: {len(s_data['calendar'])}")
                    if st.button(f"Manage {s_data['name']}", key=s_id):
                        st.session_state.active_senior_id = s_id
                        st.rerun()

        # 3. MANAGE ACTIVE SENIOR
        if st.session_state.active_senior_id:
            s_id = st.session_state.active_senior_id
            s_data = db["seniors"][s_id]
            st.markdown("---")
            st.header(f"📍 Managing: {s_data['name']}")
            
            # --- INTEGRATED TOOLS ---
            t_dash, t_med, t_cal, t_pay = st.tabs(["Summary", "Medications", "Calendar", "Subscription"])
            
            with t_dash:
                m1, m2 = st.columns(2)
                m1.metric("Current Plan", "PRO" if s_data["is_pro"] else "FREE")
                m2.metric("SOS History", len(s_data["alerts"]))
                if s_data["meds"]: st.write("Latest Med:", s_data["meds"][-1]["name"])

            with t_med:
                with st.form("med_add", clear_on_submit=True):
                    n = st.text_input("Med Name")
                    f = st.text_input("Frequency")
                    if st.form_submit_button("Save"):
                        if n:
                            db["seniors"][s_id]["meds"].append({"name": n, "freq": f, "date": str(date.today())})
                            save_data(db); st.rerun()
                st.table(pd.DataFrame(s_data["meds"]))

            with t_cal:
                with st.form("cal_add"):
                    ev = st.text_input("Event")
                    if st.form_submit_button("Add Event"):
                        if ev.strip():
                            db["seniors"][s_id]["calendar"].append({"event": ev, "date": str(date.today())})
                            save_data(db); st.rerun()
                st.table(pd.DataFrame(s_data["calendar"]))

            with t_pay:
                st.write("Upgrade this senior's profile to unlock Document Vault.")
                if st.button("🚀 Upgrade to Pro" if not s_data["is_pro"] else "Revert to Free"):
                    db["seniors"][s_id]["is_pro"] = not s_data["is_pro"]
                    save_data(db); st.rerun()

    # --- SENIOR VIEW (Tag a Caregiver) ---
    else:
        s_id = f"S-{u['email'].split('@')[0]}"
        s_data = db["seniors"].get(s_id)
        
        st.title(f"👵 Hello {u['name']}")
        
        # TAGGING LOGIC
        with st.expander("🔗 Link to a Caregiver"):
            c_email = st.text_input("Enter Caregiver's Email")
            if st.button("Tag Caregiver"):
                if c_email in db["links"]:
                    if s_id not in db["links"][c_email]:
                        db["links"][c_email].append(s_id)
                        save_data(db); st.success("Link established!")
                    else: st.warning("Already linked.")
                else: st.error("Caregiver email not found.")

        if st.button("🚨 SOS", type="primary", use_container_width=True):
            db["seniors"][s_id]["alerts"].append({"time": str(datetime.now())})
            save_data(db); st.error("Emergency Alert Logged!")

    if st.sidebar.button("Logout"):
        st.session_state.session_user = None
        st.session_state.active_senior_id = None
        st.rerun()
