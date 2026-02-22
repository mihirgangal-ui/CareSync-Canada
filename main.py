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
        "settings": {"senior_name": "", "caregiver_name": "", "caregiver_email": "", "user_role": "", "is_pro": False}
    }
    if not os.path.exists(DATA_FILE):
        return default_data
    try:
        with open(DATA_FILE, "r") as f:
            current_data = json.load(f)
            # Ensure monetization keys exist
            if "is_pro" not in current_data["settings"]:
                current_data["settings"]["is_pro"] = False
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

# --- 1. LOGIN / SIGNUP GATE ---
if not st.session_state.authenticated:
    st.title("🛡️ CareSync Canada")
    tab1, tab2 = st.tabs(["🔐 Sign In", "📝 Create Account"])
    
    with tab1:
        u_email = st.text_input("Email", key="login_email")
        if st.button("Log In"):
            if data["settings"]["caregiver_email"] == u_email and u_email != "":
                st.session_state.authenticated = True
                st.session_state.role = data["settings"].get("user_role", "Caregiver")
                st.rerun()
            else: st.error("Account not found.")

    with tab2:
        with st.form("signup"):
            sn = st.text_input("Senior's Name")
            cn = st.text_input("Caregiver Name")
            ce = st.text_input("Caregiver Email")
            ur = st.selectbox("I am a...", ["Caregiver", "Senior"])
            if st.form_submit_button("Sign Up"):
                data["settings"] = {"senior_name": sn, "caregiver_name": cn, "caregiver_email": ce, "user_role": ur, "is_pro": False}
                save_data(data); st.success("Account created! Now Sign In.")

# --- 2. THE APP INTERIOR ---
else:
    s_name = data["settings"]["senior_name"]
    is_pro = data["settings"].get("is_pro", False)

    if st.session_state.role == "Caregiver":
        st.sidebar.title("🩺 Caregiver Tools")
        
        # PRO STATUS BADGE
        if is_pro:
            st.sidebar.success("✨ PRO PLAN ACTIVE")
        else:
            st.sidebar.warning("🆓 FREE PLAN")
        
        page = st.sidebar.radio("Navigate:", 
            ["Dashboard", "Medication Manager", "Editable Calendar", "Premium: Document Vault", "Coordination Notes", "Subscription Plan"])
    else:
        page = "Senior View"

    # --- PAGE: SUBSCRIPTION (The Monetization Logic) ---
    if page == "Subscription Plan":
        st.title("💎 Membership & Monetization")
        st.write("CareSync follows a 'Freemium' model to maximize family adoption while securing recurring revenue.")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### **Free Tier**\n* Core Med Logs\n* Basic Calendar\n* 3-Day Alert History")
            if not is_pro: st.button("Current Plan", disabled=True)
        
        with col2:
            st.markdown("### **Pro Tier ($9.99/mo)**\n* **Unlimited Document Vault**\n* **Advanced SOS Routing**\n* **Family Coordination Notes**")
            if st.button("🚀 UPGRADE TO PRO" if not is_pro else "RE
