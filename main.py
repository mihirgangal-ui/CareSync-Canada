import streamlit as st
import json
import os
from datetime import datetime
import pandas as pd

# --- CONFIG ---
DATA_FILE = "family_data.json"

# --- DATA PERSISTENCE (Backwards Compatible) ---
def load_data():
    default_data = {
        "meds": [], "notes": [], "status_reports": [], 
        "alerts": [], "docs": [], "calendar": [],
        "settings": {"senior_name": "", "caregiver_name": "", "caregiver_email": "", "user_role": "", "is_pro": False}
    }
    if not os.path.exists(DATA_FILE):
        return default_data
    try:
        with open(DATA_FILE, "r") as f:
            current_data = json.load(f)
            # Ensure "settings" exists and is populated
            if "settings" not in current_data:
                current_data["settings"] = default_data["settings"]
            for key in default_data["settings"]:
                if key not in current_data["settings"]:
                    current_data["settings"][key] = default_data["settings"][key]
            # Ensure all lists exist
            for key in ["meds", "notes", "status_reports", "alerts", "docs", "calendar"]:
                if key not in current_data:
                    current_data[key] = []
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
    st.markdown("### **The Unified Family Care Platform**")
    
    tab1, tab2 = st.tabs(["🔐 Sign In", "📝 Create Account"])
    
    with tab1:
        u_email = st.text_input("Email Address", key="login_email")
        if st.button("Log In"):
            if data["settings"]["caregiver_email"] == u_email and u_email != "":
                st.session_state.authenticated = True
                st.session_state.role = data["settings"].get("user_role", "Caregiver")
                st.rerun()
            else:
                st.error("Account not found. Please Create an Account first.")

    with tab2:
        with st.form("signup_form"):
            col1, col2 = st.columns(2)
            with col1:
                sn = st.text_input("Senior's Name")
                cn = st.text_input("Caregiver Name")
            with col2:
                ce = st.text_input("Caregiver Email")
                ur = st.selectbox("I am signing up as a:", ["Caregiver", "Senior"])
            
            if st.form_submit_button("Complete Sign Up"):
                if sn and cn and ce:
                    data["settings"] = {
                        "senior_name": sn, "caregiver_name": cn, 
                        "caregiver_email": ce, "user_role": ur, "is_pro": False
                    }
                    save_data(data)
                    st.success("Account created! Please switch to the Sign In tab.")
                else:
                    st.error("Please fill in all fields.")

# --- 2. MAIN APP ---
else:
    s_name = data["settings"]["senior_name"]
    is_pro = data["settings"].get("is_pro", False)
    
    if st.session_state.role == "Caregiver":
        st.sidebar.title("🩺 Caregiver Tools")
        st.sidebar.write("✨ **PRO**" if is_pro else "🆓 **FREE**")
        page = st.sidebar.radio("Navigate:", 
            ["Dashboard", "Medication Manager", "Editable Calendar", "Premium: Document Vault", "Coordination Notes", "Subscription Plan"])
    else:
        page = "Senior View"

    # --- SUBSCRIPTION PAGE (Revenue Logic) ---
    if page == "Subscription Plan":
        st.title("💎 Membership Plans")
        col1, col2 = st.columns(2)
        with col1:
            st.info("### **Free Tier**")
            st.markdown("* ✅ Basic Medication Log\n* ✅ Shared Care Calendar\n* ✅ 24-Hour Alert Logs")
            if not is_pro: st.button("Current Plan", disabled=True)
            
        with col2:
            st.success("### **Pro Tier ($9.99/mo)**")
            st.markdown("* ⭐ **Unlimited Document Vault**\n* ⭐ **Advanced SOS Routing**\n* ⭐ **Family Coordination Notes**")
            if st.button("🚀 UPGRADE TO PRO" if not is_pro else "REVERT TO FREE"):
                data["settings"]["is_pro"] = not is_pro
                save_data(data); st.rerun()

    # --- DOCUMENT VAULT (Paywall Example) ---
    elif page == "Premium: Document Vault":
        st.title("📂 Document Vault")
        if not is_pro:
            st.error("🔒 Feature Locked: Upgrade to Pro to use the Document Vault.")
        else:
            up = st.file_uploader("Upload Record")
            if up:
                data["docs"].append({"name": up.name, "date": str(datetime.now().date())})
                save_data(data); st.success("Document stored.")
            if data["docs"]: st.table(pd.DataFrame(data["docs"]))

    # --- DASHBOARD ---
    elif page == "Dashboard":
        st.title(f"📋 {s_name}'s Hub")
        m1, m2, m3 = st.columns(3)
        m1.metric("Meds", len(data["meds"]))
        m2.metric("Events", len(data["calendar"]))
        m3.metric("Plan", "Pro" if is_pro else "Free")
        
        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("📊 Status")
            if data["status_reports"]: st.info(f"Mood: {data['status_reports'][-1]['mood']}")
            else: st.write("No data.")
        with c2:
            st.subheader("🚨 Alerts")
            for a in reversed(data["alerts"][-3:]): st.warning(a['type'])

    # --- SENIOR VIEW ---
    elif page == "Senior View":
        st.title(f"👋 Hello {s_name}")
        mood = st.select_slider("How are you?", options=["Low", "Ok", "Good", "Great"])
        if st.button("Update Family"):
            data["status_reports"].append({"mood": mood, "time": datetime.now().strftime("%H:%M")})
            save_data(data); st.success("Updated!")
        
        if st.button("🚨 I NEED HELP", use_container_width=True, type="primary"):
            data["alerts"].append({"time": datetime.now().strftime("%H:%M"), "type": f"SOS: {s_name} needs help!"})
            save_data(data); st.error("Alert Sent!")
            
        if st.button("Logout"):
            st.session_state.authenticated = False; st.rerun()

    # --- OTHER FEATURES ---
    elif page == "Medication Manager":
        st.title("💊 Meds")
        with st.form("m"):
            n = st.text_input("Medication Name")
            if st.form_submit_button("Add"):
                data["meds"].append({"name": n})
                save_data(data); st.rerun()
        for m in data["meds"]: st.write(f"- {m['name']}")

    elif page == "Editable Calendar":
        st.title("📅 Calendar")
        with st.form("c"):
            e = st.text_input("Event")
            if st.form_submit_button("Add"):
                data["calendar"].append({"event": e, "date": "TBD"})
                save_data(data); st.rerun()
        for ev in data["calendar"]: st.write(f"- {ev['event']}")

    elif page == "Coordination Notes":
        st.title("📝 Team Notes")
        nt = st.text_area("Note:")
        if st.button("Post"):
            data["notes"].append({"note": nt, "time": datetime.now().strftime("%H:%M")})
            save_data(data); st.rerun()
        for n in reversed(data["notes"]): st.info(n['note'])

    st.sidebar.markdown("---")
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False; st.rerun()
