import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------
# BASIC SETUP
# ---------------------------------------------------
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
# PAGE TITLE
# ---------------------------------------------------
st.title("One‑Page ERP – Entry + Dashboard")

now = datetime.now()
auto_datetime = now.strftime("%Y-%m-%d %H:%M")
auto_shift = get_shift(now)

st.write(f"**Date & Time (auto):** {auto_datetime}")
st.write(f"**Shift (auto):** {auto_shift}")

st.markdown("---")
st.header("Data Entry")

# ---------------------------------------------------
# ONE‑PAGE ENTRY FORM
# ---------------------------------------------------
with st.form("one_page_form"):

    # MACHINE
    machine = st.selectbox("Machine", MACHINES)

    # BOTTLE WEIGHT
    bottle_weight = st.number_input("Bottle Weight (grams)", min_value=1.0, step=0.1)

    # OUTPUT
    out_bottles = st.number_input("Output (bottles)", min_value=0)
    auto_out_kg = (out_bottles * bottle_weight) / 1000
    out_kg = st.number_input(
        "Output (kg) – auto calculated (override allowed)",
        value=float(auto_out_kg),
        step=0.01,
    )

    # MATERIAL TYPE
    material_type = st.text_input("Material Type")

    # COLOUR
    colour = st.text_input("Colour")
    batches = st.number_input("Batches", min_value=0)

    # MASTERBATCH
    mb_type = st.text_input("MB Type")
    mb_kg = st.number_input("MB KG Used", min_value=0.0, step=0.01)

    # REJECTION
    rej_bottles = st.number_input("Rejection (bottles)", min_value=0)
    auto_rej_kg = (rej_bottles * bottle_weight) / 1000
    rej_kg = st.number_input(
        "Rejection (kg) – auto calculated (override allowed)",
        value=float(auto_rej_kg),
        step=0.01,
    )
    rej_reason = st.text_input("Rejection Reason")

    # MATERIAL USED (AUTO = OUT KG + REJ KG, OVERRIDE ALLOWED)
    auto_material_used = out_kg + rej_kg
    material_kg = st.number_input(
        "Material KG Used – auto calculated (override allowed)",
        value=float(auto_material_used),
        step=0.01,
    )

    submitted = st.form_submit_button("SAVE ENTRY")

# ---------------------------------------------------
# VALIDATION (MANDATORY FIELDS)
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

    if bottle_weight <= 0:
        missing.append("Bottle Weight (grams)")
    if out_bottles <= 0:
        missing.append("Output (bottles)")
    if out_kg <= 0:
        missing.append("Output (kg)")
    if material_kg <= 0:
        missing.append("Material KG Used")
    if rej_bottles < 0:
        missing.append("Rejection (bottles)")
    if rej_kg < 0:
        missing.append("Rejection (kg)")

    if missing:
        st.error("Please fill all fields correctly: " + ", ".join(missing))
    else:
        # OUTPUT
        df_out = load_csv("output.csv")
        df_out = pd.concat(
            [
                df_out,
                pd.DataFrame(
                    [
                        {
                            "DateTime": auto_datetime,
                            "Shift": auto_shift,
                            "Machine": machine,
                            "Bottle Weight (g)": bottle_weight,
                            "Output (kg)": out_kg,
                            "Output (bottles)": out_bottles,
                        }
                    ]
                ),
            ],
            ignore_index=True,
        )
        save_csv("output.csv", df_out)

        # RAW MATERIAL
        df_rm = load_csv("raw_material.csv")
        df_rm = pd.concat(
            [
                df_rm,
                pd.DataFrame(
                    [
                        {
                            "DateTime": auto_datetime,
                            "Shift": auto_shift,
                            "Machine": machine,
                            "Material Type": material_type,
                            "Material KG Used": material_kg,
                        }
                    ]
                ),
            ],
            ignore_index=True,
        )
        save_csv("raw_material.csv", df_rm)

        # BOTTLE COLOUR
        df_col = load_csv("bottle_colour.csv")
        df_col = pd.concat(
            [
                df_col,
                pd.DataFrame(
                    [
                        {
                            "DateTime": auto_datetime,
                            "Shift": auto_shift,
                            "Machine": machine,
                            "Colour": colour,
                            "Batches": batches,
                        }
                    ]
                ),
            ],
            ignore_index=True,
        )
        save_csv("bottle_colour.csv", df_col)

        # MASTERBATCH
        df_mb = load_csv("masterbatch.csv")
        df_mb = pd.concat(
            [
                df_mb,
                pd.DataFrame(
                    [
                        {
                            "DateTime": auto_datetime,
                            "Shift": auto_shift,
                            "Machine": machine,
                            "MB Type": mb_type,
                            "MB KG Used": mb_kg,
                        }
                    ]
                ),
            ],
            ignore_index=True,
        )
        save_csv("masterbatch.csv", df_mb)

        # REJECTION
        df_rej = load_csv("rejection.csv")
        df_rej = pd.concat(
            [
                df_rej,
                pd.DataFrame(
                    [
                        {
                            "DateTime": auto_datetime,
                            "Shift": auto_shift,
                            "Machine": machine,
                            "Rejection (kg)": rej_kg,
                            "Rejection (bottles)": rej_bottles,
                            "Rejection Reason": rej_reason,
                            "Bottle Weight (g)": bottle_weight,
                        }
                    ]
                ),
            ],
            ignore_index=True,
        )
        save_csv("rejection.csv", df_rej)

        st.success("All entries saved successfully!")

# ---------------------------------------------------
# DASHBOARD HELPERS
# ---------------------------------------------------
def prepare_time_columns(df):
    if df.empty:
        return df
    if "DateTime" in df.columns:
        df["DateTime"] = pd.to_datetime(df["DateTime"], errors="coerce")
        df["Date"] = df["DateTime"].dt.date
        df["Month"] = df["DateTime"].dt.to_period("M").astype(str)
    return df

def show_shift_and_monthly(df, shift_group_cols, numeric_cols, title_prefix, shift_filename, month_filename):
    if df.empty:
        st.info(f"No {title_prefix.lower()} data available.")
        return

    df = prepare_time_columns(df)

    # SHIFT‑WISE
    st.subheader(f"{title_prefix} – Shift‑wise")
    shift_df = df.groupby(["Date", "Shift"])[numeric_cols].sum().reset_index()
    st.dataframe(shift_df, use_container_width=True)
    csv_shift = shift_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        f"Download Shift‑wise {title_prefix} CSV",
        csv_shift,
        shift_filename,
        mime="text/csv",
    )

    # MONTHLY
    st.subheader(f"{title_prefix} – Monthly")
    month_df = df.groupby("Month")[numeric_cols].sum().reset_index()
    st.dataframe(month_df, use_container_width=True)
    csv_month = month_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        f"Download Monthly {title_prefix} CSV",
        csv_month,
        month_filename,
        mime="text/csv",
    )

# ---------------------------------------------------
# DASHBOARD SECTION (ON SAME PAGE)
# ---------------------------------------------------
st.markdown("---")
st.header("Dashboard – Shift‑wise & Monthly Summary")

# OUTPUT
df_out = load_csv("output.csv")
show_shift_and_monthly(
    df_out,
    ["Date", "Shift"],
    ["Output (kg)", "Output (bottles)"],
    "Output",
    "shift_output.csv",
    "monthly_output.csv",
)

st.markdown("---")

# RAW MATERIAL
df_rm = load_csv("raw_material.csv")
show_shift_and_monthly(
    df_rm,
    ["Date", "Shift"],
    ["Material KG Used"],
    "Raw Material",
    "shift_raw_material.csv",
    "monthly_raw_material.csv",
)

st.markdown("---")

# BOTTLE COLOUR
df_col = load_csv("bottle_colour.csv")
show_shift_and_monthly(
    df_col,
    ["Date", "Shift"],
    ["Batches"],
    "Bottle Colour",
    "shift_bottle_colour.csv",
    "monthly_bottle_colour.csv",
)

st.markdown("---")

# MASTERBATCH
df_mb = load_csv("masterbatch.csv")
show_shift_and_monthly(
    df_mb,
    ["Date", "Shift"],
    ["MB KG Used"],
    "Masterbatch",
    "shift_masterbatch.csv",
    "monthly_masterbatch.csv",
)

st.markdown("---")

# REJECTION
df_rej = load_csv("rejection.csv")
show_shift_and_monthly(
    df_rej,
    ["Date", "Shift"],
    ["Rejection (kg)", "Rejection (bottles)"],
    "Rejection",
    "shift_rejection.csv",
    "monthly_rejection.csv",
)
