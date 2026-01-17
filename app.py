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
SHIFTS = ["A", "B"]

# ---------------------------------------------------
# CSV HELPERS
# ---------------------------------------------------
def load_csv(name):
    file = DATA_DIR / name
    return pd.read_csv(file) if file.exists() else pd.DataFrame()

def save_csv(name, df):
    file = DATA_DIR / name
    df.to_csv(file, index=False)

# ---------------------------------------------------
# TIME COLUMNS
# ---------------------------------------------------
def prepare_time_columns(df):
    if df.empty or "DateTime" not in df.columns:
        return df
    df["DateTime"] = pd.to_datetime(df["DateTime"], errors="coerce")
    df["Date"] = df["DateTime"].dt.date
    df["Month"] = df["DateTime"].dt.to_period("M").astype(str)
    return df

# ---------------------------------------------------
# GENERIC DASHBOARD BLOCK
# ---------------------------------------------------
def show_shift_and_monthly(df, numeric_cols, title_prefix, shift_filename, month_filename):
    if df.empty:
        st.info(f"No {title_prefix.lower()} data available.")
        return

    df = prepare_time_columns(df)

    st.subheader(f"{title_prefix} – Shift‑wise")
    shift_df = df.groupby(["Date", "Shift"])[numeric_cols].sum().reset_index()
    st.dataframe(shift_df, use_container_width=True)
    st.download_button(
        f"Download Shift-wise {title_prefix} CSV",
        shift_df.to_csv(index=False).encode("utf-8"),
        shift_filename
    )

    st.subheader(f"{title_prefix} – Monthly")
    month_df = df.groupby("Month")[numeric_cols].sum().reset_index()
    st.dataframe(month_df, use_container_width=True)
    st.download_button(
        f"Download Monthly {title_prefix} CSV",
        month_df.to_csv(index=False).encode("utf-8"),
        month_filename
    )

# ---------------------------------------------------
# PAGE HEADER
# ---------------------------------------------------
st.title("One‑Page ERP – Entry + Dashboard")

now = datetime.now()
auto_datetime = now.strftime("%Y-%m-%d %H:%M")
st.write(f"**Date & Time (auto):** {auto_datetime}")

st.markdown("---")
st.header("Data Entry")

# ---------------------------------------------------
# ENTRY FORM
# ---------------------------------------------------
with st.form("one_page_form"):

    machine = st.selectbox("Machine", MACHINES)

    # MANUAL SHIFT
    shift = st.selectbox("Shift", SHIFTS)

    # Bottle Details
    bottle_type = st.text_input("Bottle Type")
    item = st.text_input("Item")
    bottle_weight = st.number_input("Bottle Weight (grams)", min_value=1.0, step=0.1)

    # Output
    out_bottles = st.number_input("Output (bottles)", min_value=0)
    auto_out_kg = (out_bottles * bottle_weight) / 1000
    out_kg = st.number_input(
        "Output (kg) – auto calculated (override allowed)",
        value=float(auto_out_kg),
        step=0.01,
    )

    # Material
    material_type = st.text_input("Material Type")

    # Masterbatch
    mb_type = st.text_input("MB Type")
    mb_kg = st.number_input("MB KG Used", min_value=0.0, step=0.01)

    # Rejection
    rej_bottles = st.number_input("Rejection (bottles)", min_value=0)
    auto_rej_kg = (rej_bottles * bottle_weight) / 1000
    rej_kg = st.number_input(
        "Rejection (kg) – auto calculated (override allowed)",
        value=float(auto_rej_kg),
        step=0.01,
    )
    rej_reason = st.text_input("Rejection Reason")

    # Material Used
    auto_material_used = out_kg + rej_kg
    material_kg = st.number_input(
        "Material KG Used – auto calculated (override allowed)",
        value=float(auto_material_used),
        step=0.01,
    )

    submitted = st.form_submit_button("SAVE ENTRY")

# ---------------------------------------------------
# VALIDATION + SAVE
# ---------------------------------------------------
if submitted:

    missing = []
    for label, value in {
        "Bottle Type": bottle_type,
        "Item": item,
        "Material Type": material_type,
        "MB Type": mb_type,
        "Rejection Reason": rej_reason,
    }.items():
        if value.strip() == "":
            missing.append(label)

    if bottle_weight <= 0:
        missing.append("Bottle Weight")
    if out_bottles <= 0:
        missing.append("Output (bottles)")
    if out_kg <= 0:
        missing.append("Output (kg)")
    if material_kg <= 0:
        missing.append("Material KG Used")

    if missing:
        st.error("Please fill all fields: " + ", ".join(missing))

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
                            "Shift": shift,
                            "Machine": machine,
                            "Bottle Type": bottle_type,
                            "Item": item,
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
                            "Shift": shift,
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

        # MASTERBATCH
        df_mb = load_csv("masterbatch.csv")
        df_mb = pd.concat(
            [
                df_mb,
                pd.DataFrame(
                    [
                        {
                            "DateTime": auto_datetime,
                            "Shift": shift,
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
                            "Shift": shift,
                            "Machine": machine,
                            "Bottle Type": bottle_type,
                            "Item": item,
                            "Rejection (kg)": rej_kg,
                            "Rejection (bottles)": rej_bottles,
                            "Rejection Reason": rej_reason,
                        }
                    ]
                ),
            ],
            ignore_index=True,
        )
        save_csv("rejection.csv", df_rej)

        st.success("All entries saved successfully!")

# ---------------------------------------------------
# DASHBOARD
# ---------------------------------------------------
st.markdown("---")
st.header("Dashboard – Shift‑wise & Monthly Summary")

# OUTPUT
df_out = load_csv("output.csv")
show_shift_and_monthly(
    df_out,
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
    ["Material KG Used"],
    "Raw Material",
    "shift_raw_material.csv",
    "monthly_raw_material.csv",
)

st.markdown("---")

# MASTERBATCH
df_mb = load_csv("masterbatch.csv")
show_shift_and_monthly(
    df_mb,
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
    ["Rejection (kg)", "Rejection (bottles)"],
    "Rejection",
    "shift_rejection.csv",
    "monthly_rejection.csv",
)

# ---------------------------------------------------
# DELETE WRONG ENTRY SECTION
# ---------------------------------------------------
st.markdown("---")
st.header("Delete Wrong Entry")

MODULE_MAP = {
    "Output": ("output.csv", ["DateTime", "Shift", "Machine", "Bottle Type", "Item", "Output (kg)", "Output (bottles)"]),
    "Raw Material": ("raw_material.csv", ["DateTime", "Shift", "Machine", "Material Type", "Material KG Used"]),
    "Masterbatch": ("masterbatch.csv", ["DateTime", "Shift", "Machine", "MB Type", "MB KG Used"]),
    "Rejection": ("rejection.csv", ["DateTime", "Shift", "Machine", "Bottle Type", "Item", "Rejection (kg)", "Rejection (bottles)", "Rejection Reason"]),
}

module = st.selectbox("Select Module", list(MODULE_MAP.keys()))
csv_name, cols = MODULE_MAP[module]

df_mod = load_csv(csv_name)

if df_mod.empty:
    st.info(f"No data available in {module} to delete.")
else:
    df_mod = prepare_time_columns(df_mod)

    # Filter by Date, Shift, Machine
    available_dates = sorted(df_mod["Date"].dropna().unique())
    sel_date = st.selectbox("Select Date", available_dates)

    filtered = df_mod[df_mod["Date"] == sel_date]

    sel_shift = st.selectbox("Select Shift", SHIFTS)
    filtered = filtered[filtered["Shift"] == sel_shift]

    available_machines = sorted(filtered["Machine"].dropna().unique())
    if len(available_machines) == 0:
        st.info("No entries for this Date and Shift.")
    else:
        sel_machine = st.selectbox("Select Machine", available_machines)
        filtered = filtered[filtered["Machine"] == sel_machine]

        if filtered.empty:
            st.info("No entries match the selected filters.")
        else:
            st.write("Tap any row to select it for deletion.")

            # Add an index column for display
            filtered_display = filtered.reset_index(drop=False)
            filtered_display.rename(columns={"index": "RowID"}, inplace=True)

            # Show table
            selected_row_id = st.session_state.get("selected_row_id", None)

            # Use st.dataframe; selection simulated via a selectbox of RowID
            st.dataframe(filtered_display[cols + ["RowID"]], use_container_width=True)

            # Row selection (by RowID) – simulating "click any cell"
            row_ids = filtered_display["RowID"].tolist()
            if row_ids:
                sel_rowid = st.selectbox("Select Row to delete (simulates row click)", row_ids)
                st.session_state["selected_row_id"] = sel_rowid

                # Highlight info
                st.markdown(
                    f"<div style='background-color: #fff3cd; padding: 10px; border-radius: 5px;'>"
                    f"<b>Warning:</b> You have selected RowID <b>{sel_rowid}</b> for deletion.</div>",
                    unsafe_allow_html=True,
                )

                # Show selected row details
                sel_row = df_mod.loc[sel_rowid]
                st.write("Selected Entry Details:")
                st.json(sel_row.to_dict())

                if st.button("DELETE ENTRY", type="primary"):
                    df_mod = df_mod.drop(index=sel_rowid)
                    save_csv(csv_name, df_mod)
                    st.success("Entry deleted successfully. Refresh the page to see updated data.")
