import streamlit as st
import json
import os
from datetime import datetime
import pandas as pd

# --- CONFIG ---
DATA_FILE = "family_data.json"

# --- DATA PERSISTENCE (Safe & Modular) ---
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
            # Repair logic: ensure all keys exist for the Freemium update
            if "settings" not in current_data:
                current_data["settings"] = default_data["settings"]
            for key in default_data["settings"]:
                if key not in current_data["settings"]:
                    current_data["settings"][key] = default_data["settings"][key]
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

# --- 1. FRONT DOOR (ONBOARDING & LOGIN) ---
if not st.session_state.authenticated:
    st.title("🛡️ CareSync Canada")
    st.markdown("### **The Unified Family Care Platform**")
    
    tab1, tab2 = st.tabs(["🔐 Sign In", "📝 Create Account"])
    
    with tab1:
        st.write("Welcome back! Please enter your email.")
        u_email = st.text_input("Email Address", key="login_email")
        if st.button("Log In"):
            if data["settings"]["caregiver_email"] == u_email and u_email != "":
                st.session_state.authenticated = True
                st.session_state.role = data["settings"].get("user_role", "Caregiver")
                st.rerun()
            else:
                st.error("Account not found. Please use the 'Create Account' tab.")

    with tab2:
        st.write("Register your family to begin.")
        with st.form("signup_form"):
            col1, col2 = st.columns(2)
            with col1:
                sn = st.text_input("Senior's Name (e.g., Robert)")
                cn = st.text_input("Caregiver Name (e.g., Jane)")
            with col2:
                ce = st.text_input("Caregiver Email (Used for Login)")
                ur = st.selectbox("I am signing up as a:", ["Caregiver", "Senior"])
            
            if st.form_submit_button("Complete Sign Up"):
                if sn and cn and ce:
                    data["settings"] = {
                        "senior_name": sn, "caregiver_name": cn, 
                        "caregiver_email": ce, "user_role": ur, "is_pro": False
                    }
                    save_data(data)
                    st.success("Account created! You can now Sign In.")
                else:
                    st.error("Please fill in all fields.")

# --- 2. THE APP INTERIOR (INSIDE THE GATE) ---
else:
    s_name = data["settings"]["senior_name"]
    is_pro = data["settings"].get("is_pro", False)
    
    # Navigation logic based on the role captured during signup
    if st.session_state.role == "Caregiver":
        st.sidebar.title("🩺 Caregiver Tools")
        if is_pro:
