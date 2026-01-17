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
        # ---------------------------------------------------
# DASHBOARD (SHIFT‑WISE + MONTHLY + DOWNLOAD)
# ---------------------------------------------------
st.sidebar.title("Navigation")
menu = st.sidebar.radio("Go to", ["Entry", "Dashboard"])

if menu == "Dashboard":
    st.title("Dashboard – Shift‑wise & Monthly Summary")

    # -----------------------------
    # OUTPUT SUMMARY
    # -----------------------------
    st.header("Output Summary")

    df_out = load_csv("output.csv")
    if not df_out.empty:
        df_out["DateTime"] = pd.to_datetime(df_out["DateTime"])
        df_out["Date"] = df_out["DateTime"].dt.date
        df_out["Month"] = df_out["DateTime"].dt.to_period("M").astype(str)

        # SHIFT‑WISE
        st.subheader("Shift‑wise Output")
        shift_out = df_out.groupby(["Date", "Shift"])[["Output (kg)", "Output (bottles)"]].sum().reset_index()
        st.dataframe(shift_out, use_container_width=True)

        csv = shift_out.to_csv(index=False).encode("utf-8")
        st.download_button("Download Shift‑wise Output CSV", csv, "shift_output.csv")

        # MONTHLY
        st.subheader("Monthly Output")
        month_out = df_out.groupby("Month")[["Output (kg)", "Output (bottles)"]].sum().reset_index()
        st.dataframe(month_out, use_container_width=True)

        csv2 = month_out.to_csv(index=False).encode("utf-8")
        st.download_button("Download Monthly Output CSV", csv2, "monthly_output.csv")

    else:
        st.info("No output data available.")

    st.markdown("---")

    # -----------------------------
    # RAW MATERIAL SUMMARY
    # -----------------------------
    st.header("Raw Material Summary")

    df_rm = load_csv("raw_material.csv")
    if not df_rm.empty:
        df_rm["DateTime"] = pd.to_datetime(df_rm["DateTime"])
        df_rm["Date"] = df_rm["DateTime"].dt.date
        df_rm["Month"] = df_rm["DateTime"].dt.to_period("M").astype(str)

        st.subheader("Shift‑wise Raw Material")
        shift_rm = df_rm.groupby(["Date", "Shift"])[["Material KG Used"]].sum().reset_index()
        st.dataframe(shift_rm, use_container_width=True)

        csv = shift_rm.to_csv(index=False).encode("utf-8")
        st.download_button("Download Shift‑wise RM CSV", csv, "shift_rm.csv")

        st.subheader("Monthly Raw Material")
        month_rm = df_rm.groupby("Month")[["Material KG Used"]].sum().reset_index()
        st.dataframe(month_rm, use_container_width=True)

        csv2 = month_rm.to_csv(index=False).encode("utf-8")
        st.download_button("Download Monthly RM CSV", csv2, "monthly_rm.csv")

    else:
        st.info("No raw material data available.")

    st.markdown("---")

    # -----------------------------
    # REJECTION SUMMARY
    # -----------------------------
    st.header("Rejection Summary")

    df_rej = load_csv("rejection.csv")
    if not df_rej.empty:
        df_rej["DateTime"] = pd.to_datetime(df_rej["DateTime"])
        df_rej["Date"] = df_rej["DateTime"].dt.date
        df_rej["Month"] = df_rej["DateTime"].dt.to_period("M").astype(str)

        st.subheader("Shift‑wise Rejection")
        shift_rej = df_rej.groupby(["Date", "Shift"])[["Rejection (kg)", "Rejection (bottles)"]].sum().reset_index()
        st.dataframe(shift_rej, use_container_width=True)

        csv = shift_rej.to_csv(index=False).encode("utf-8")
        st.download_button("Download Shift‑wise Rejection CSV", csv, "shift_rejection.csv")

        st.subheader("Monthly Rejection")
        month_rej = df_rej.groupby("Month")[["Rejection (kg)", "Rejection (bottles)"]].sum().reset_index()
        st.dataframe(month_rej, use_container_width=True)

        csv2 = month_rej.to_csv(index=False).encode("utf-8")
        st.download_button("Download Monthly Rejection CSV", csv2, "monthly_rejection.csv")

    else:
        st.info("No rejection data available.")
