import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path

st.set_page_config(page_title="One‑Page ERP", layout="wide")

DATA_DIR = Path(__file__).parent

MACHINES = ["M001", "M002", "M003"]

# ---------------------------------------------------
# SHIFT LOGIC (8 AM – 8 PM = A, 8 PM – 8 AM = B)
# ---------------------------------------------------
def get_shift(dt):
    hour = dt.hour
    if 8 <= hour < 20:
        return "A"
    return "B"

# ---------------------------------------------------
# CSV HELPERS
# ---------------------------------------------------
def load_csv(name):
    file = DATA_DIR / name
    if file.exists():
        return pd.read_csv(file)
    return pd.DataFrame()

def save_csv(name, df):
    file = DATA_DIR / name
    df.to_csv(file, index=False)

# ---------------------------------------------------
# PAGE UI
# ---------------------------------------------------
st.title("One‑Page ERP Entry")

now = datetime.now()
auto_datetime = now.strftime("%Y-%m-%d %H:%M")
auto_shift = get_shift(now)

st.write(f"**Date & Time (auto):** {auto_datetime}")
st.write(f"**Shift (auto):** {auto_shift}")

# ---------------------------------------------------
# ONE SINGLE FORM
# ---------------------------------------------------
with st.form("one_page_form"):

    # MACHINE
    machine = st.selectbox("Machine", MACHINES)

    # OUTPUT
    out_kg = st.number_input("Output (kg)", min_value=0.0, step=0.01)
    out_bottles = st.number_input("Output (bottles)", min_value=0)

    # MATERIAL
    material_type = st.text_input("Material Type")
    material_kg = st.number_input("Material KG Used", min_value=0.0, step=0.01)

    # COLOUR
    colour = st.text_input("Colour")
    batches = st.number_input("Batches", min_value=0)

    # MASTERBATCH
    mb_type = st.text_input("MB Type")
    mb_kg = st.number_input("MB KG Used", min_value=0.0, step=0.01)

    # REJECTION
    rej_kg = st.number_input("Rejection (kg)", min_value=0.0, step=0.01)
    rej_bottles = st.number_input("Rejection (bottles)", min_value=0)
    rej_reason = st.text_input("Rejection Reason")

    submitted = st.form_submit_button("SAVE ENTRY")

# ---------------------------------------------------
# VALIDATION (ALL FIELDS MANDATORY)
# ---------------------------------------------------
if submitted:

    missing = []
    if material_type.strip() == "":
        missing.append("Material Type")
    if colour.strip() == "":
        missing.append("Colour")
    if mb_type.strip() == "":
        missing.append("MB Type")
    if rej_reason.strip() == "":
        missing.append("Rejection Reason")

    if missing:
        st.error("Please fill all fields: " + ", ".join(missing))
    else:
        # ---------------------------------------------------
        # SAVE TO MULTIPLE CSVs
        # ---------------------------------------------------

        # OUTPUT
        df_out = load_csv("output.csv")
        df_out = pd.concat([
            df_out,
            pd.DataFrame([{
                "DateTime": auto_datetime,
                "Shift": auto_shift,
                "Machine": machine,
                "Output (kg)": out_kg,
                "Output (bottles)": out_bottles
            }])
        ], ignore_index=True)
        save_csv("output.csv", df_out)

        # RAW MATERIAL
        df_rm = load_csv("raw_material.csv")
        df_rm = pd.concat([
            df_rm,
            pd.DataFrame([{
                "DateTime": auto_datetime,
                "Shift": auto_shift,
                "Machine": machine,
                "Material Type": material_type,
                "Material KG Used": material_kg
            }])
        ], ignore_index=True)
        save_csv("raw_material.csv", df_rm)

        # COLOUR
        df_col = load_csv("bottle_colour.csv")
        df_col = pd.concat([
            df_col,
            pd.DataFrame([{
                "DateTime": auto_datetime,
                "Shift": auto_shift,
                "Machine": machine,
                "Colour": colour,
                "Batches": batches
            }])
        ], ignore_index=True)
        save_csv("bottle_colour.csv", df_col)

        # MASTERBATCH
        df_mb = load_csv("masterbatch.csv")
        df_mb = pd.concat([
            df_mb,
            pd.DataFrame([{
                "DateTime": auto_datetime,
                "Shift": auto_shift,
                "Machine": machine,
                "MB Type": mb_type,
                "MB KG Used": mb_kg
            }])
        ], ignore_index=True)
        save_csv("masterbatch.csv", df_mb)

        # REJECTION
        df_rej = load_csv("rejection.csv")
        df_rej = pd.concat([
            df_rej,
            pd.DataFrame([{
                "DateTime": auto_datetime,
                "Shift": auto_shift,
                "Machine": machine,
                "Rejection (kg)": rej_kg,
                "Rejection (bottles)": rej_bottles,
                "Rejection Reason": rej_reason
            }])
        ], ignore_index=True)
        save_csv("rejection.csv", df_rej)

        st.success("All entries saved successfully!")
