import streamlit as st
import pandas as pd
from datetime import datetime

# -----------------------------
# Machine setup
# -----------------------------
MACHINES = {
    "M001": "Extruder A",
    "M002": "Extruder B",
    "M003": "Extruder C"
}

# -----------------------------
# CSV helpers
# -----------------------------
def load_csv(file):
    try:
        return pd.read_csv(file)
    except FileNotFoundError:
        return pd.DataFrame()

def save_csv(file, df):
    df.to_csv(file, index=False)

# -----------------------------
# Entry forms
# -----------------------------
def entry_form(title, fields, filename):
    st.subheader(title)
    data = {}
    for label, field_type in fields:
        if field_type == "text":
            data[label] = st.text_input(label)
        elif field_type == "number":
            data[label] = st.number_input(label, step=0.01)
        elif field_type == "select_machine":
            data[label] = st.selectbox(label, options=list(MACHINES.keys()))
        elif field_type == "select":
            data[label] = st.selectbox(label[0], options=label[1])
        elif field_type == "datetime":
            data[label] = st.text_input(label, value=datetime.now().strftime("%Y-%m-%d %H:%M"))
    if st.button(f"Save {title}"):
        df = load_csv(filename)
        df = pd.concat([df, pd.DataFrame([data])], ignore_index=True)
        save_csv(filename, df)
        st.success(f"{title} saved.")
    st.markdown("---")
    st.dataframe(load_csv(filename), use_container_width=True)

# -----------------------------
# Dashboard
# -----------------------------
def dashboard():
    st.title("🏭 Blow Moulding ERP Dashboard")
    output = load_csv("output.csv")
    rejection = load_csv("rejection.csv")
    downtime = load_csv("downtime.csv")
    rm = load_csv("raw_material.csv")
    mb = load_csv("masterbatch.csv")

    st.metric("Total Output (bottles)", int(output["Output (bottles)"].sum()) if not output.empty else 0)
    st.metric("Total Output (kg)", round(output["Output (kg)"].sum(), 2) if not output.empty else 0)
    st.metric("Total Rejection (kg)", round(rejection["Rejection (kg)"].sum(), 2) if not rejection.empty else 0)
    st.metric("Total Downtime Entries", len(downtime))
    st.metric("Total RM Used (kg)", round(rm["KG Used"].sum(), 2) if not rm.empty else 0)
    st.metric("Total MB Used (kg)", round(mb["KG Used"].sum(), 2) if not mb.empty else 0)

    st.subheader("Machines")
    st.table(pd.DataFrame([{"Machine ID": k, "Name": v} for k, v in MACHINES.items()]))

# -----------------------------
# App layout
# -----------------------------
st.set_page_config(page_title="Blow Moulding ERP", layout="wide")
menu = st.sidebar.radio("Navigate", [
    "Dashboard", "Output", "Raw Material", "Masterbatch",
    "Bottle Colour", "Rejection", "Downtime"
])

if menu == "Dashboard":
    dashboard()

elif menu == "Output":
    entry_form("Output", [
        ("Date", "text"),
        ("Shift", "text"),
        ("Machine", "select_machine"),
        ("Output (bottles)", "number"),
        ("Output (kg)", "number"),
        ("Target Output (kg)", "number")
    ], "output.csv")

elif menu == "Raw Material":
    entry_form("Raw Material", [
        ("Date & Time", "datetime"),
        ("Machine", "select_machine"),
        (("Material Type", ["HDPE", "PP", "Others"]), "select"),
        ("Grade", "text"),
        ("Batch Number", "text"),
        ("KG Used", "number")
    ], "raw_material.csv")

elif menu == "Masterbatch":
    entry_form("Masterbatch", [
        ("Date & Time", "datetime"),
        ("Machine", "select_machine"),
        (("MB Type", ["Colour", "Additive"]), "select"),
        ("MB Code", "text"),
        ("Batch Number", "text"),
        ("KG Used", "number"),
        ("Dosage %", "number")
    ], "masterbatch.csv")

elif menu == "Bottle Colour":
    entry_form("Bottle Colour", [
        ("Date & Time", "datetime"),
        ("Machine", "select_machine"),
        ("Colour Name", "text"),
        ("Colour Code", "text"),
        ("MB Batch Number", "text")
    ], "bottle_colour.csv")

elif menu == "Rejection":
    entry_form("Rejection", [
        ("Date & Time", "datetime"),
        ("Machine", "select_machine"),
        ("Rejection (bottles)", "number"),
        ("Rejection (kg)", "number"),
        (("Reason", ["Short shot", "Flash", "Weight high", "Weight low", "Colour issue", "Leak", "Others"]), "select")
    ], "rejection.csv")

elif menu == "Downtime":
    entry_form("Downtime", [
        ("Machine", "select_machine"),
        ("Start Time", "text"),
        ("End Time", "text"),
        (("Reason", ["Mechanical", "Electrical", "Mould change", "No material", "QC hold", "Others"]), "select"),
        ("Remarks", "text")
    ], "downtime.csv")
