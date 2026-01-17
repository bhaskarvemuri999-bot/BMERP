import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path

st.set_page_config(page_title="One-Page ERP", layout="wide")
DATA_DIR = Path(__file__).parent
MACHINES = ["M001", "M002", "M003"]

def get_shift(dt):
    hour = dt.hour
    return "A" if 8 <= hour < 20 else "B"

def load_csv(name):
    file = DATA_DIR / name
    return pd.read_csv(file) if file.exists() else pd.DataFrame()

def save_csv(name, df):
    file = DATA_DIR / name
    df.to_csv(file, index=False)

def prepare_time_columns(df):
    if df.empty or "DateTime" not in df.columns:
        return df
    df["DateTime"] = pd.to_datetime(df["DateTime"], errors="coerce")
    df["Date"] = df["DateTime"].dt.date
    df["Month"] = df["DateTime"].dt.to_period("M").astype(str)
    return df

def show_shift_and_monthly(df, numeric_cols, title_prefix, shift_filename, month_filename):
    if df.empty:
        st.info(f"No {title_prefix.lower()} data available.")
        return
    df = prepare_time_columns(df)
    st.subheader(f"{title_prefix} – Shift-wise")
    shift_df = df.groupby(["Date", "Shift"])[numeric_cols].sum().reset_index()
    st.dataframe(shift_df, use_container_width=True)
    st.download_button(f"Download Shift-wise {title_prefix} CSV", shift_df.to_csv(index=False).encode("utf-8"), shift_filename)
    st.subheader(f"{title_prefix} – Monthly")
    month_df = df.groupby("Month")[numeric_cols].sum().reset_index()
    st.dataframe(month_df, use_container_width=True)
    st.download_button(f"Download Monthly {title_prefix} CSV", month_df.to_csv(index=False).encode("utf-8"), month_filename)

st.title("One-Page ERP – Entry + Dashboard")
now = datetime.now()
auto_datetime = now.strftime("%Y-%m-%d %H:%M")
auto_shift = get_shift(now)

st.write(f"**Date & Time (auto):** {auto_datetime}")
st.write(f"**Shift (auto):** {auto_shift}")
st.markdown("---")
st.header("Data Entry")

with st.form("one_page_form"):
    machine = st.selectbox("Machine", MACHINES)
    bottle_type = st.text_input("Bottle Type")
    item = st.text_input("Item")
    bottle_weight = st.number_input("Bottle Weight (grams)", min_value=1.0, step=0.1)
    out_bottles = st.number_input("Output (bottles)", min_value=0)
    auto_out_kg = (out_bottles * bottle_weight) / 1000
    out_kg = st.number_input("Output (kg) – auto calculated (override allowed)", value=float(auto_out_kg), step=0.01)
    material_type = st.text_input("Material Type")
    colour = st.text_input("Colour")
    mb_type = st.text_input("MB Type")
    mb_kg = st.number_input("MB KG Used", min_value=0.0, step=0.01)
    rej_bottles = st.number_input("Rejection (bottles)", min_value=0)
    auto_rej_kg = (rej_bottles * bottle_weight) / 1000
    rej_kg = st.number_input("Rejection (kg) – auto calculated (override allowed)", value=float(auto_rej_kg), step=0.01)
    rej_reason = st.text_input("Rejection Reason")
    auto_material_used = out_kg + rej_kg
    material_kg = st.number_input("Material KG Used – auto calculated (override allowed)", value=float(auto_material_used), step=0.01)
    submitted = st.form_submit_button("SAVE ENTRY")

if submitted:
    missing = []
    for label, value in {
        "Bottle Type": bottle_type,
        "Item": item,
        "Material Type": material_type,
        "Colour": colour,
        "MB Type": mb_type,
        "Rejection Reason": rej_reason,
    }.items():
        if value.strip() == "":
            missing.append(label)
    if bottle_weight <= 0: missing.append("Bottle Weight")
    if out_bottles <= 0: missing.append("Output (bottles)")
    if out_kg <= 0: missing.append("Output (kg)")
    if material_kg <= 0: missing.append("Material KG Used")
    if missing:
        st.error("Please fill all fields: " + ", ".join(missing))
    else:
        # OUTPUT
        df_out = load_csv("output.csv")
        df_out = pd.concat([df_out, pd.DataFrame([{
            "DateTime": auto_datetime,
            "Shift": auto_shift,
            "Machine": machine,
            "Bottle Type": bottle_type,
            "Item": item,
            "Bottle Weight (g)": bottle_weight,
            "Output (kg)": out_kg,
            "Output (bottles)": out_bottles
        }])], ignore_index=True)
        save_csv("output.csv", df_out)

        # RAW MATERIAL
        df_rm = load_csv("raw_material.csv")
        df_rm = pd.concat([df_rm, pd.DataFrame([{
            "DateTime": auto_datetime,
            "Shift": auto_shift,
            "Machine": machine,
            "Material Type": material_type,
            "Material KG Used": material_kg
        }])], ignore_index=True)
        save_csv("raw_material.csv", df_rm)

        # COLOUR
        df_col = load_csv("bottle_colour.csv")
        df_col = pd.concat([df_col, pd.DataFrame([{
            "DateTime": auto_datetime,
            "Date": now.date(),
            "Shift": auto_shift,
            "Machine": machine,
            "Bottle Type": bottle_type,
            "Item": item,
            "Colour": colour
        }])], ignore_index=True)
        save_csv("bottle_colour.csv", df_col)

        # MASTERBATCH
        df_mb = load_csv("masterbatch.csv")
        df_mb = pd.concat([df_mb, pd.DataFrame([{
            "DateTime": auto_datetime,
            "Shift": auto_shift,
            "Machine": machine,
            "MB Type": mb_type,
            "MB KG Used": mb_kg
        }])], ignore_index=True)
        save_csv("masterbatch.csv", df_mb)

        # REJECTION
        df_rej = load_csv("rejection.csv")
        df_rej = pd.concat([df_rej, pd.DataFrame([{
            "DateTime": auto_datetime,
            "Shift": auto_shift,
            "Machine": machine,
            "Bottle Type": bottle_type,
            "Item": item,
            "Rejection (kg)": rej_kg,
            "Rejection (bottles)": rej_bottles,
            "Rejection Reason": rej_reason
        }])], ignore_index=True)
        save_csv("rejection.csv", df_rej)

        st.success("All entries saved successfully!")

# ------------------ DASHBOARD ------------------
st.markdown("---")
st.header("Dashboard – Shift-wise & Monthly Summary")

df_out = load_csv("output.csv")
show_shift_and_monthly(df_out, ["Output (kg)", "Output (bottles)"], "Output", "shift_output.csv", "monthly_output.csv")

st.markdown("---")
df_rm = load_csv("raw_material.csv")
show_shift_and_monthly(df_rm, ["Material KG Used"], "Raw Material", "shift_raw_material.csv", "monthly_raw_material.csv")

st.markdown("---")
df_col = load_csv("bottle_colour.csv")
if not df_col.empty:
    df_col["DateTime"] = pd.to_datetime(df_col["DateTime"], errors="coerce")
    df_col["Month"] = df_col["DateTime"].dt.to_period("M").astype(str)
    st.subheader("Bottle Colour – Shift-wise")
    shift_df = df_col.groupby(["Date", "Shift", "Colour", "Bottle Type", "Item"]).size().reset_index(name="Entries")
    st.dataframe(shift_df, use_container_width=True)
    st.download_button("Download Shift-wise Bottle Colour CSV", shift_df.to_csv(index=False).encode("utf-8"), "shift_bottle_colour.csv")
    st.subheader("Bottle Colour – Monthly")
    month_df = df_col.groupby(["Month", "Colour", "Bottle Type", "Item"]).size().reset_index(name="Entries")
    st.dataframe(month_df, use_container_width=True)
    st.download_button("Download Monthly Bottle Colour CSV", month_df.to_csv(index=False).encode("utf-8"), "monthly_bottle_colour.csv")
else:
    st.info("No bottle colour data available.")

st.markdown("---")
