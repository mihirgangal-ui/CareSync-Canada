import streamlit as st
import pandas as pd
from datetime import datetime, time, date
import pytz
import json
import os

# --- 1. CONFIG & SYSTEM SETUP ---
ADMIN_PASSWORD = "care"
DB_FILE = "family_data.json"
VAULT_DIR = "care_vault"
LOCAL_TZ = pytz.timezone("America/Toronto") 

if not os.path.exists(VAULT_DIR): os.makedirs(VAULT_DIR)

def get_now(): return datetime.now(LOCAL_TZ)

def load_db():
    schema = {"events": [], "meds": [], "notes": [], "status_reports": [], "alerts": []}
    if not os.path.exists(DB_FILE): return schema
    try:
        with open(DB_FILE, "r") as f:
            data = json.load(f)
            for key in schema:
                if key not in data: data[key] = []
            return data
    except: return schema

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

db = load_db()

# --- 2. LOGIC ENGINE ---
def get_precision_alerts():
    alerts = []
    now = get_now()
    cur_t, today_d, today_s = now.strftime("%H:%M"), now.date(), now.strftime("%Y-%m-%d")
    prescriptions = [m for m in db['meds'] if m.get('type') == 'SCHEDULE']
    logs = [m for m in db['meds'] if m.get('type') == 'LOG']

    for p in prescriptions:
        det = p['details']
        start = datetime.strptime(det['start'], "%Y-%m-%d").date()
        end = datetime.strptime(det['end'], "%Y-%m-%d").date()
        if start <= today_d <= end:
            for slot in det.get('slots', []):
                if cur_t > slot:
                    taken = any(l['name'] == det['name'] and l['time'].startswith(today_s) and 
                                abs((datetime.strptime(slot, "%H:%M") - datetime.strptime(l['time'][11:16], "%H:%M")).total_seconds()) < 7200 for l in logs)
                    if not taken: alerts.append({"name": det['name'], "slot": slot})
    return alerts

# --- 3. LOGIN & NAVIGATION ---
if 'auth' not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    st.title("🛡️ CareSync Canada")
    pwd = st.text_input("Access Code:", type="password")
    if st.button("Unlock Dashboard"):
        if pwd == ADMIN_PASSWORD: st.session_state.auth = True; st.rerun()
    st.stop()

st.set_page_config(page_title="CareSync v3.5", layout="wide")

# --- 4. SIDEBAR (RESET RESTORED) ---
with st.sidebar:
    st.title("🛡️ CareSync")
    role = st.selectbox("Role:", ["Caregiver", "Senior"], key="sb_role")
    nav = st.radio("Menu:", ["Dashboard", "Calendar", "Med Center", "Document Vault"] if role=="Caregiver" else ["Senior Portal"])
    st.divider()
    if st.button("Logout", key="logout"): st.session_state.auth = False; st.rerun()

    # FACTORY RESET RESTORED
    if st.button("🗑️ Factory Reset", key="reset_btn"):
        save_db({"events":[], "meds":[], "notes":[], "status_reports":[], "alerts":[]})
        st.warning("Database Cleared.")
        st.rerun()

# --- 5. GLOBAL SOS ---
if role == "Caregiver":
    for a in [item for item in db['alerts'] if not item.get('resolved')]:
        st.error(f"🚨 **SOS: {a.get('user')} ({a.get('time')})**")
        if st.button(f"Resolve Alert {a.get('id')}", key=f"sos_{a.get('id')}"):
            for item in db['alerts']:
                if item.get('id') == a.get('id'): item['resolved'] = True
            save_db(db); st.rerun()

# --- 6. SENIOR PORTAL ---
if nav == "Senior Portal":
    st.title("Hi Mom & Dad! 👋")
    c1, c2, c3 = st.columns(3)
    ts = get_now().strftime("%Y-%m-%d %H:%M")
    if c1.button("😊 I'm Great", use_container_width=True): db['status_reports'].append({"status":"Great","time":ts,"color":"green"}); save_db(db); st.success("Notified!")
    if c2.button("😐 Just Okay", use_container_width=True): db['status_reports'].append({"status":"Okay","time":ts,"color":"orange"}); save_db(db); st.info("Logged.")
    if c3.button("🆘 NEED HELP", use_container_width=True): 
        db['alerts'].append({"id":str(int(get_now().timestamp())),"user":"Mom/Dad","time":ts,"resolved":False})
        db['status_reports'].append({"status":"EMERGENCY","time":ts,"color":"red"}); save_db(db); st.error("SOS SENT!")

# --- 7. CAREGIVER: DASHBOARD ---
elif nav == "Dashboard":
    st.title("Care Overview")
    st.subheader("📊 Well-being Tracker")
    for s in reversed(db['status_reports'][-3:]):
        if s['color'] == "green": st.success(f"😊 {s['status']} ({s['time']})")
        elif s['color'] == "orange": st.warning(f"😐 {s['status']} ({s['time']})")
        else: st.error(f"🆘 {s['status']} ({s['time']})")
    st.divider()
    st.subheader("💊 Med Adherence")
    missed = get_precision_alerts()
    if not missed: st.success("All meds on schedule.")
    else:
        for m in missed: st.error(f"**MISSING:** {m['name']} at {m['slot']}")
    st.divider()
    l, r = st.columns(2)
    with l:
        st.subheader("💬 Notice Board")
        for n in db['notes'][-3:]: st.info(f"**{n['name']}**: {n['content']}")
        note = st.text_input("New Note", key="n_in")
        if st.button("Post Note", key="n_btn"): db['notes'].append({"name":user,"content":note,"time":get_now().strftime("%H:%M")}); save_db(db); st.rerun()
    with r:
        st.subheader("📅 Today")
        tasks = [e for e in db['events'] if e.get('Date') == get_now().strftime("%Y-%m-%d")]
        if not tasks: st.write("No events.")
        for i, t in enumerate(tasks): st.checkbox(f"{t['Time']} - {t['Event']}", key=f"t_{i}")

# --- 8. MED CENTER (SMART EDIT) ---
elif nav == "Med Center":
    st.title("Medication Management")
    t1, t2, t3 = st.tabs(["💊 Log Dose", "➕ Manage Schedule", "📜 History"])

    with t1:
        active = [m['details']['name'] for m in db['meds'] if m.get('type') == 'SCHEDULE']
        if active:
            target = st.selectbox("Log Dose:", active)
            if st.button("Record Dose Taken"):
                db['meds'].append({"type":"LOG","name":target,"time":get_now().strftime("%Y-%m-%d %H:%M"),"by":user})
                save_db(db); st.balloons(); st.rerun()

    with t2:
        st.subheader("Add or Update Medication")
        all_m = [m for m in db['meds'] if m.get('type') == 'SCHEDULE']
        med_names = ["-- New Medication --"] + [m['details']['name'] for m in all_m]
        selection = st.selectbox("Select Med to Edit:", med_names, key="edit_selector")

        # Load existing data if editing
        existing_data = next((m['details'] for m in all_m if m['details']['name'] == selection), None)

        with st.form("med_form"):
            name = st.text_input("Medication Name", value=existing_data['name'] if existing_data else "")
            sd = st.date_input("Start Date", datetime.strptime(existing_data['start'], "%Y-%m-%d") if existing_data else get_now())
            ed = st.date_input("End Date", datetime.strptime(existing_data['end'], "%Y-%m-%d") if existing_data else get_now().replace(year=get_now().year+1))
            s1, s2, s3 = st.columns(3)
            # Default times if no data exists
            v1 = s1.time_input("T1", datetime.strptime(existing_data['slots'][0], "%H:%M").time() if existing_data and len(existing_data['slots'])>0 else time(8,0))
            v2 = s2.time_input("T2", datetime.strptime(existing_data['slots'][1], "%H:%M").time() if existing_data and len(existing_data['slots'])>1 else time(13,0))
            v3 = s3.time_input("T3", datetime.strptime(existing_data['slots'][2], "%H:%M").time() if existing_data and len(existing_data['slots'])>2 else time(18,0))
            freq = st.radio("Doses/Day", [1, 2, 3], index=(len(existing_data['slots'])-1) if existing_data else 0, horizontal=True)

            if st.form_submit_button("Save Changes"):
                slots = [v1.strftime("%H:%M"), v2.strftime("%H:%M"), v3.strftime("%H:%M")][:freq]
                new_entry = {"type": "SCHEDULE", "details": {"name": name, "slots": slots, "start": str(sd), "end": str(ed)}}

                # UPDATE LOGIC: If editing, remove old record before adding updated one
                if existing_data:
                    db['meds'] = [m for m in db['meds'] if not (m.get('type') == 'SCHEDULE' and m['details']['name'] == selection)]

                db['meds'].append(new_entry)
                save_db(db); st.success("Schedule Updated!"); st.rerun()

        if existing_data:
            if st.button("🗑️ Delete Medication", key="del_m"):
                db['meds'] = [m for m in db['meds'] if not (m.get('type') == 'SCHEDULE' and m['details']['name'] == selection)]
                save_db(db); st.rerun()

    with t3:
        logs = [m for m in db['meds'] if m.get('type') == 'LOG']
        if logs: st.dataframe(pd.DataFrame(logs)[['name', 'time', 'by']], use_container_width=True)

# --- 9. CALENDAR & VAULT ---
elif nav == "Calendar":
    st.title("Calendar")
    with st.form("cal"):
        en, ed, et = st.text_input("Event"), st.date_input("Date"), st.time_input("Time")
        if st.form_submit_button("Add Event"):
            db['events'].append({"Event": en, "Date": str(ed), "Time": et.strftime("%I:%M %p")})
            save_db(db); st.rerun()
    if db['events']: st.table(pd.DataFrame(db['events']).sort_values(by="Date"))

elif nav == "Document Vault":
    st.title("📂 Vault")
    up = st.file_uploader("Upload Record", type=['pdf', 'jpg', 'png'], key="v_up")
    if up:
        with open(os.path.join(VAULT_DIR, up.name), "wb") as f: f.write(up.getbuffer())
        st.success("Saved.")
    for f_name in os.listdir(VAULT_DIR):
        c1, c2 = st.columns([3, 1])
        c1.write(f"📄 {f_name}")
        with open(os.path.join(VAULT_DIR, f_name), "rb") as f:
            c2.download_button("Download", f, file_name=f_name, key=f"dl_{f_name}")