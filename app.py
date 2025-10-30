import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# --- PAGE CONFIG ---
st.set_page_config(page_title="Technician KPI Dashboard", layout="wide")

# --- LOAD DATA ---
@st.cache_data
def load_data():
    df = pd.read_csv("rawdat.csv")
    df["Submission_Date"] = pd.to_datetime(df["Submission_Date"])
    df["Month"] = df["Submission_Date"].dt.strftime("%Y-%m")
    return df

df = load_data()

st.title("📊 Technician Submission & KPI Dashboard")

# --- FILTERS ---
col1, col2, col3 = st.columns(3)
with col1:
    selected_location = st.selectbox("📍 Select Location", ["All"] + sorted(df["Location"].unique().tolist()))
with col2:
    selected_technician = st.selectbox("👷 Select Technician", ["All"] + sorted(df["Technician_Name"].unique().tolist()))
with col3:
    selected_discipline = st.selectbox("🛠️ Select Discipline", ["All"] + sorted(df["Discipline"].unique().tolist()))

# Apply filters
filtered_df = df.copy()
if selected_location != "All":
    filtered_df = filtered_df[filtered_df["Location"] == selected_location]
if selected_technician != "All":
    filtered_df = filtered_df[filtered_df["Technician_Name"] == selected_technician]
if selected_discipline != "All":
    filtered_df = filtered_df[filtered_df["Discipline"] == selected_discipline]

# --- SUBMISSION TREND ---
st.subheader("📈 Submission Trend Over Time (by Location)")
trend = filtered_df.groupby(["Month", "Location"]).size().reset_index(name="Submission_Count")
fig_trend = px.line(
    trend,
    x="Month",
    y="Submission_Count",
    color="Location",
    markers=True,
    title="Submission Trend Comparison by Location"
)
st.plotly_chart(fig_trend, use_container_width=True)

# --- KPI CALCULATION ---
kpi_df = (
    df.groupby("Location")
    .agg(
        Total_Submissions=("Work_Order_ID", "count"),
        Approved_Submissions=("Approval_Status", lambda x: (x == "Approved").sum())
    )
    .reset_index()
)
kpi_df["KPI (%)"] = (kpi_df["Approved_Submissions"] / kpi_df["Total_Submissions"]) * 100
kpi_df["Status"] = np.where(kpi_df["KPI (%)"] >= 80, "✅ Achieved", "❌ Not Achieved")

st.subheader("📍 KPI by Location")
st.dataframe(kpi_df.style.format({"KPI (%)": "{:.2f}"}), use_container_width=True)

# --- KPI BAR CHART ---
fig_kpi = px.bar(
    kpi_df,
    x="Location",
    y="KPI (%)",
    color="Status",
    color_discrete_map={"✅ Achieved": "green", "❌ Not Achieved": "red"},
    title="KPI Achievement by Location"
)
fig_kpi.add_hline(y=80, line_dash="dash", line_color="orange", annotation_text="Target 80%")
st.plotly_chart(fig_kpi, use_container_width=True)

# --- KPI PREDICTION (Simple Moving Average) ---
st.subheader("🔮 KPI Prediction (Next Month Estimate)")
kpi_trend = (
    df.groupby(["Month", "Location"])
    .agg(Approved=("Approval_Status", lambda x: (x == "Approved").sum()),
         Total=("Work_Order_ID", "count"))
    .reset_index()
)
kpi_trend["KPI (%)"] = (kpi_trend["Approved"] / kpi_trend["Total"]) * 100

# Predict next month using average trend
predictions = kpi_trend.groupby("Location")["KPI (%)"].mean().reset_index()
predictions.rename(columns={"KPI (%)": "Predicted_KPI (%)"}, inplace=True)
predictions["Predicted_Status"] = np.where(predictions["Predicted_KPI (%)"] >= 80, "✅ Achieved", "❌ Not Achieved")

st.dataframe(predictions.style.format({"Predicted_KPI (%)": "{:.2f}"}), use_container_width=True)

fig_pred = px.bar(
    predictions,
    x="Location",
    y="Predicted_KPI (%)",
    color="Predicted_Status",
    color_discrete_map={"✅ Achieved": "green", "❌ Not Achieved": "red"},
    title="Predicted KPI by Location"
)
fig_pred.add_hline(y=80, line_dash="dash", line_color="orange", annotation_text="Target 80%")
st.plotly_chart(fig_pred, use_container_width=True)

# --- DETAILED RECORD VIEW ---
st.subheader("📋 Detailed Submission Records")
st.dataframe(filtered_df, use_container_width=True)
