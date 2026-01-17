import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path

# -------------------------------
# Basic setup
# -------------------------------
st.set_page_config(page_title="Blow Moulding ERP", layout="wide")

DATA_DIR = Path(__file__).parent

MACHINES = {
    "M001": "Extruder A",
    "M002": "Extruder B",
    "M003": "Extruder C",
}

# -------------------------------
# Helpers
# -------------------------------
def get_shift(dt: datetime) -> str:
    """Return shift A or B based on time.
       A: 08:00–20:00, B: 20:00–08:00
    """
    hour = dt.hour
    if 8 <= hour < 20:
        return "A"
    else:
        return "B"


def load_csv(filename: str) -> pd.DataFrame:
    file = DATA_DIR / filename
    if file.exists():
        return pd.read_csv(file)
    return pd.DataFrame()


def save_csv(filename: str, df: pd.DataFrame):
    file = DATA_DIR / filename
    df.to_csv(file, index=False)


def ensure_datetime_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure DateTime, Date, Shift columns exist and are parsed."""
    if df.empty:
        return df

    # If DateTime column exists, parse it
    if "DateTime" in df.columns:
        df["DateTime"] = pd.to_datetime(df["DateTime"], errors="coerce")
    elif "Date & Time" in df.columns:
        df["DateTime"] = pd.to_datetime(df["Date & Time"], errors="coerce")
    else:
        # Try to build from Date + Time if present
        if "Date" in df.columns and "Time" in df.columns:
            df["DateTime"] = pd.to_datetime(
                df["Date"].astype(str) + " " + df["Time"].astype(str),
                errors="coerce",
            )

    # Derive Date
    if "DateTime" in df.columns:
        df["Date"] = df["DateTime"].dt.date

    # Ensure Shift
    if "Shift" not in df.columns and "DateTime" in df.columns:
        df["Shift"] = df["DateTime"].apply(get_shift)

    # Month for monthly summary
    if "DateTime" in df.columns:
        df["Month"] = df["DateTime"].dt.to_period("M").astype(str)

    return df


def shift_summary(df: pd.DataFrame, numeric_cols: list) -> pd.DataFrame:
    df = ensure_datetime_columns(df)
    if df.empty:
        return df
    group_cols = ["Date", "Shift"]
    existing_numeric = [c for c in numeric_cols if c in df.columns]
    if not existing_numeric:
        return pd.DataFrame()
    summary = df.groupby(group_cols)[existing_numeric].sum().reset_index()
    return summary


def monthly_summary(df: pd.DataFrame, numeric_cols: list) -> pd.DataFrame:
    df = ensure_datetime_columns(df)
    if df.empty:
        return df
    if "Month" not in df.columns:
        return pd.DataFrame()
    existing_numeric = [c for c in numeric_cols if c in df.columns]
    if not existing_numeric:
        return pd.DataFrame()
    summary = df.groupby("Month")[existing_numeric].sum().reset_index()
    return summary


def download_button_for_df(label: str, df: pd.DataFrame, filename: str):
    if df is not None and not df.empty:
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(label, csv, file_name=filename, mime="text/csv")


# -------------------------------
# Generic entry form
# -------------------------------
def entry_form(title: str, fields: list, filename: str):
    st.subheader(title)

    now = datetime.now()
    auto_datetime_str = now.strftime("%Y-%m-%d %H:%M")
    auto_shift = get_shift(now)

    st.write("**Date & Time (auto)**:", auto_datetime_str)
    st.write("**Shift (auto)**:", auto_shift)

    data = {
        "DateTime": auto_datetime_str,
        "Shift": auto_shift,
    }

    with st.form(key=f"{title}_form"):
        for field in fields:
            name = field["name"]
            ftype = field["type"]

            if ftype == "machine":
                data[name] = st.selectbox(name, options=list(MACHINES.keys()))
            elif ftype == "text":
                data[name] = st.text_input(name)
            elif ftype == "number":
                data[name] = st.number_input(name, step=0.01)
            elif ftype == "select":
                options = field.get("options", [])
                data[name] = st.selectbox(name, options=options)

        submitted = st.form_submit_button("Save")

    if submitted:
        df = load_csv(filename)
        new_row = pd.DataFrame([data])
        df = pd.concat([df, new_row], ignore_index=True)
        save_csv(filename, df)
        st.success("Entry saved.")


# -------------------------------
# UI Layout
# -------------------------------
st.title("Blow Moulding ERP")

menu = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Output",
        "Raw Material",
        "Masterbatch",
        "Bottle Colour",
        "Rejection",
        "Downtime",
    ],
)

# -------------------------------
# Dashboard
# -------------------------------
if menu == "Dashboard":
    st.header("Dashboard")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Output – Shift-wise")
        df_out = load_csv("output.csv")
        df_out = ensure_datetime_columns(df_out)
        out_shift = shift_summary(df_out, ["Output (kg)", "Output (bottles)"])
        if not out_shift.empty:
            st.dataframe(out_shift, use_container_width=True)
            download_button_for_df(
                "Download Shift-wise Output CSV", out_shift, "shift_output.csv"
            )
        else:
            st.info("No output data available.")

    with col2:
        st.subheader("Output – Monthly")
        out_month = monthly_summary(df_out, ["Output (kg)", "Output (bottles)"])
        if not out_month.empty:
            st.dataframe(out_month, use_container_width=True)
            download_button_for_df(
                "Download Monthly Output CSV", out_month, "monthly_output.csv"
            )
        else:
            st.info("No monthly output data available.")

    st.markdown("---")

    col3, col4 = st.columns(2)

    with col3:
        st.subheader("Rejection – Shift-wise")
        df_rej = load_csv("rejection.csv")
        df_rej = ensure_datetime_columns(df_rej)
        rej_shift = shift_summary(df_rej, ["Rejection (kg)", "Rejection (bottles)"])
        if not rej_shift.empty:
            st.dataframe(rej_shift, use_container_width=True)
            download_button_for_df(
                "Download Shift-wise Rejection CSV",
                rej_shift,
                "shift_rejection.csv",
            )
        else:
            st.info("No rejection data available.")

    with col4:
        st.subheader("Rejection – Monthly")
        rej_month = monthly_summary(df_rej, ["Rejection (kg)", "Rejection (bottles)"])
        if not rej_month.empty:
            st.dataframe(rej_month, use_container_width=True)
            download_button_for_df(
                "Download Monthly Rejection CSV",
                rej_month,
                "monthly_rejection.csv",
            )
        else:
            st.info("No monthly rejection data available.")

# -------------------------------
# Output
# -------------------------------
elif menu == "Output":
    entry_form(
        "Output Entry",
        [
            {"name": "Machine", "type": "machine"},
            {"name": "Output (kg)", "type": "number"},
            {"name": "Output (bottles)", "type": "number"},
            {"name": "Remarks", "type": "text"},
        ],
        "output.csv",
    )

    st.markdown("---")
    st.subheader("Shift-wise Output Summary")
    df = load_csv("output.csv")
    df = ensure_datetime_columns(df)
    summary = shift_summary(df, ["Output (kg)", "Output (bottles)"])
    if not summary.empty:
        st.dataframe(summary, use_container_width=True)
        download_button_for_df(
            "Download Shift-wise Output CSV", summary, "shift_output.csv"
        )
    else:
        st.info("No data available.")

    st.subheader("Monthly Output Summary")
    msum = monthly_summary(df, ["Output (kg)", "Output (bottles)"])
    if not msum.empty:
        st.dataframe(msum, use_container_width=True)
        download_button_for_df(
            "Download Monthly Output CSV", msum, "monthly_output.csv"
        )
    else:
        st.info("No monthly data available.")

# -------------------------------
# Raw Material
# -------------------------------
elif menu == "Raw Material":
    entry_form(
        "Raw Material Entry",
        [
            {"name": "Machine", "type": "machine"},
            {"name": "Material Type", "type": "text"},
            {"name": "KG Used", "type": "number"},
            {"name": "Remarks", "type": "text"},
        ],
        "raw_material.csv",
    )

    st.markdown("---")
    st.subheader("Shift-wise Raw Material Summary")
    df = load_csv("raw_material.csv")
    df = ensure_datetime_columns(df)
    summary = shift_summary(df, ["KG Used"])
    if not summary.empty:
        st.dataframe(summary, use_container_width=True)
        download_button_for_df(
            "Download Shift-wise Raw Material CSV",
            summary,
            "shift_raw_material.csv",
        )
    else:
        st.info("No data available.")

    st.subheader("Monthly Raw Material Summary")
    msum = monthly_summary(df, ["KG Used"])
    if not msum.empty:
        st.dataframe(msum, use_container_width=True)
        download_button_for_df(
            "Download Monthly Raw Material CSV",
            msum,
            "monthly_raw_material.csv",
        )
    else:
        st.info("No monthly data available.")

# -------------------------------
# Masterbatch
# -------------------------------
elif menu == "Masterbatch":
    entry_form(
        "Masterbatch Entry",
        [
            {"name": "Machine", "type": "machine"},
            {"name": "MB Type", "type": "text"},
            {"name": "KG Used", "type": "number"},
            {"name": "Remarks", "type": "text"},
        ],
        "masterbatch.csv",
    )

    st.markdown("---")
    st.subheader("Shift-wise Masterbatch Summary")
    df = load_csv("masterbatch.csv")
    df = ensure_datetime_columns(df)
    summary = shift_summary(df, ["KG Used"])
    if not summary.empty:
        st.dataframe(summary, use_container_width=True)
        download_button_for_df(
            "Download Shift-wise Masterbatch CSV",
            summary,
            "shift_masterbatch.csv",
        )
    else:
        st.info("No data available.")

    st.subheader("Monthly Masterbatch Summary")
    msum = monthly_summary(df, ["KG Used"])
    if not msum.empty:
        st.dataframe(msum, use_container_width=True)
        download_button_for_df(
            "Download Monthly Masterbatch CSV",
            msum,
            "monthly_masterbatch.csv",
        )
    else:
        st.info("No monthly data available.")

# -------------------------------
# Bottle Colour
# -------------------------------
elif menu == "Bottle Colour":
    entry_form(
        "Bottle Colour Entry",
        [
            {"name": "Machine", "type": "machine"},
            {"name": "Colour", "type": "text"},
            {"name": "Batches", "type": "number"},
            {"name": "Remarks", "type": "text"},
        ],
        "bottle_colour.csv",
    )

    st.markdown("---")
    st.subheader("Shift-wise Bottle Colour Summary")
    df = load_csv("bottle_colour.csv")
    df = ensure_datetime_columns(df)
    summary = shift_summary(df, ["Batches"])
    if not summary.empty:
        st.dataframe(summary, use_container_width=True)
        download_button_for_df(
            "Download Shift-wise Bottle Colour CSV",
            summary,
            "shift_bottle_colour.csv",
        )
    else:
        st.info("No data available.")

    st.subheader("Monthly Bottle Colour Summary")
    msum = monthly_summary(df, ["Batches"])
    if not msum.empty:
        st.dataframe(msum, use_container_width=True)
        download_button_for_df(
            "Download Monthly Bottle Colour CSV",
            msum,
            "monthly_bottle_colour.csv",
        )
    else:
        st.info("No monthly data available.")

# -------------------------------
# Rejection
# -------------------------------
elif menu == "Rejection":
    entry_form(
        "Rejection Entry",
        [
            {"name": "Machine", "type": "machine"},
            {"name": "Rejection (kg)", "type": "number"},
            {"name": "Rejection (bottles)", "type": "number"},
            {"name": "Reason", "type": "text"},
        ],
        "rejection.csv",
    )

    st.markdown("---")
    st.subheader("Shift-wise Rejection Summary")
    df = load_csv("rejection.csv")
    df = ensure_datetime_columns(df)
    summary = shift_summary(df, ["Rejection (kg)", "Rejection (bottles)"])
    if not summary.empty:
        st.dataframe(summary, use_container_width=True)
        download_button_for_df(
            "Download Shift-wise Rejection CSV",
            summary,
            "shift_rejection.csv",
        )
    else:
        st.info("No data available.")

    st.subheader("Monthly Rejection Summary")
    msum = monthly_summary(df, ["Rejection (kg)", "Rejection (bottles)"])
    if not msum.empty:
        st.dataframe(msum, use_container_width=True)
        download_button_for_df(
            "Download Monthly Rejection CSV",
            msum,
            "monthly_rejection.csv",
        )
    else:
        st.info("No monthly data available.")

# -------------------------------
# Downtime
# -------------------------------
elif menu == "Downtime":
    entry_form(
        "Downtime Entry",
        [
            {"name": "Machine", "type": "machine"},
            {"name": "Downtime (minutes)", "type": "number"},
            {"name": "Reason", "type": "text"},
        ],
        "downtime.csv",
    )

    st.markdown("---")
    st.subheader("Shift-wise Downtime Summary")
    df = load_csv("downtime.csv")
    df = ensure_datetime_columns(df)
    summary = shift_summary(df, ["Downtime (minutes)"])
    if not summary.empty:
        st.dataframe(summary, use_container_width=True)
        download_button_for_df(
            "Download Shift-wise Downtime CSV",
            summary,
            "shift_downtime.csv",
        )
    else:
        st.info("No data available.")

    st.subheader("Monthly Downtime Summary")
    msum = monthly_summary(df, ["Downtime (minutes)"])
    if not msum.empty:
        st.dataframe(msum, use_container_width=True)
        download_button_for_df(
            "Download Monthly Downtime CSV",
            msum,
            "monthly_downtime.csv",
        )
    else:
        st.info("No monthly data available.")
