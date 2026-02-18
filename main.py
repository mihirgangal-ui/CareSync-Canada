import streamlit as st
import json
import os
from datetime import datetime
import pandas as pd

# --- CONFIG ---
DATA_FILE = "family_data.json"

# --- DATA PERSISTENCE ---
def load_data():
    default_data = {
        "meds": [], "notes": [], "status_reports": [], 
        "alerts": [], "docs": [], "calendar": [],
        "settings": {"senior_name": "", "caregiver_name": "", "caregiver_email": ""}
    }
    if not os.path.exists(DATA_FILE):
        return default_data
    try:
        with open(DATA_FILE, "r") as f:
            current_data = json.load(f)
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
data = load_data()

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# --- FRONT DOOR (OUTSIDE THE GATE) ---
if not st.session_state.authenticated:
    st.title("🛡️ CareSync Canada")
    
    # Professional Blurb
    st.markdown("""
    ### **The Unified Family Care Platform**
    Bridging the gap between seniors and their care teams with real-time synchronization.
    """)
    
    # Toggle between Login and Sign Up
    tab1, tab2 = st.tabs(["🔐 Sign In", "📝 Create Account"])
    
    with tab1:
        st.write("Welcome back! Please enter your credentials.")
        user_email = st.text_input("Email Address", key="login_email")
        if st.button("Log In"):
            # For the demo, we check if the email matches what's in our 'database'
            if data["settings"]["caregiver_email"] == user_email and user_email != "":
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Account not found. Please Sign Up if you are a new user.")
        st.caption("Recruiter Tip: If you haven't set up a profile yet, use the 'Create Account' tab.")

    with tab2:
        st.write("Register your family to begin coordinating care.")
        with st.form("signup_form"):
            s_name = st.text_input("Senior's Name (e.g., Robert)")
            c_name = st.text_input("Caregiver Name (e.g., Jane)")
            c_email = st.text_input("Caregiver Email (Used for Login)")
            
            if st.form_submit_button("Complete Intake & Sign Up"):
                if s_name and c_name and c_email:
                    data["settings"] = {
                        "senior_name": s_name,
                        "caregiver_name": c_name,
                        "caregiver_email": c_email
                    }
                    save_data(data)
                    st.success("Account created! You can now Log In.")
                else:
                    st.error("Please fill in all fields.")

# --- INSIDE THE GATE ---
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
        # Caregiver Sidebar
        if st.session_state.role == "Caregiver":
            st.sidebar.title("🩺 Caregiver Tools")
            page = st.sidebar.radio("Navigate to:", 
                ["Dashboard", "Medication Manager", "Editable Calendar", "Document Vault", "Coordination Notes"])
        else:
            page = "Senior View"

        # --- FEATURE: DASHBOARD ---
        if page == "Dashboard":
            st.title(f"📋 {s_name}'s Command Centre")
            m1, m2, m3 = st.columns(3)
            m1.metric("Meds Logged", len(data["meds"]))
            m2.metric("Events", len(data["calendar"]))
            m3.metric("Vault Docs", len(data["docs"]))
            st.markdown("---")
            col_a, col_b = st.columns(2)
            with col_a:
                st.subheader("📊 Senior Health Status")
                if data["status_reports"]:
                    st.success(f"Latest Mood: {data['status_reports'][-1]['mood']}")
                else: st.info("No reports yet.")
            with col_b:
                st.subheader("🚨 Recent Alerts")
                if data["alerts"]:
                    for a in reversed(data["alerts"][-3:]): st.warning(f"{a['type']} at {a['time']}")

        # --- FEATURE: MEDICATION MANAGER ---
        elif page == "Medication Manager":
            st.title("💊 Medication Log")
            with st.form("m_form"):
                n = st.text_input("Name")
                f = st.text_input("Frequency")
                if st.form_submit_button("Save"):
                    data["meds"].append({"name": n, "freq": f})
                    save_data(data); st.rerun()
            for i, m in enumerate(data["meds"]):
                c = st.columns([4, 1])
                c[0].write(f"**{m['name']}** - {m['freq']}")
                if c[1].button("🗑️", key=f"m_{i}"):
                    data["meds"].pop(i); save_data(data); st.rerun()

        # --- FEATURE: CALENDAR ---
        elif page == "Editable Calendar":
            st.title("📅 Care Calendar")
            with st.form("c_form"):
                e = st.text_input("Event")
                d = st.date_input("Date")
                if st.form_submit_button("Add Event"):
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
            mood = st.select_slider("How are you feeling?", options=["Low", "Ok", "Good", "Great"])
            if st.button("Update Family"):
                data["status_reports"].append({"mood": mood, "time": datetime.now().strftime("%H:%M")})
                save_data(data); st.success("Updated!")
            
            if st.button("🚨 I NEED HELP", use_container_width=True, type="primary"):
                msg = f"HELP REQUEST: {s_name} needs assistance!"
                data["alerts"].append({"time": datetime.now().strftime("%H:%M"), "type": msg})
                save_data(data); st.error(msg)

        # --- OTHER PAGES ---
        elif page == "Document Vault":
            st.title("📂 Vault")
            up = st.file_uploader("Upload PDF/Image")
            if up:
                data["docs"].append({"name": up.name, "date": str(datetime.now().date())})
                save_data(data); st.success("Saved.")
            if data["docs"]: st.table(pd.DataFrame(data["docs"]))

        elif page == "Coordination Notes":
            st.title("📝 Coordination Notes")
            nt = st.text_area("Update:")
            if st.button("Post"):
                data["notes"].append({"note": nt, "time": datetime.now().strftime("%H:%M")})
                save_data(data); st.rerun()
            for n in reversed(data["notes"]): st.info(f"{n['time']}: {n['note']}")

        st.sidebar.markdown("---")
        if st.sidebar.button("Logout / Exit"):
            st.session_state.role = None
            st.session_state.authenticated = False; st.rerun()
