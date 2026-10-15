
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(
    page_title="Interactive Analytics Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("Interactive Analytics Dashboard")
st.write("Explore sales and profitability across categories and regions.")

@st.cache_data
def load_data(file):
    return pd.read_csv(file, encoding="latin1")

uploaded_file = st.sidebar.file_uploader(
    "Upload Superstore CSV",
    type=["csv"]
)

if uploaded_file is not None:
    df = load_data(uploaded_file)
elif Path("Sample - Superstore.csv").exists():
    df = pd.read_csv("Sample - Superstore.csv", encoding="latin1")
else:
    st.error("Please upload the Superstore CSV dataset.")
    st.stop()

df.columns = df.columns.str.strip()

required = [
    "Sales", "Profit", "Order ID",
    "Category", "Region", "Order Date"
]

missing = [col for col in required if col not in df.columns]

if missing:
    st.error("Missing columns: " + ", ".join(missing))
    st.write("Available columns:", df.columns.tolist())
    st.stop()

df["Sales"] = pd.to_numeric(df["Sales"], errors="coerce")
df["Profit"] = pd.to_numeric(df["Profit"], errors="coerce")
df["Order Date"] = pd.to_datetime(df["Order Date"], errors="coerce")

if "Discount" in df.columns:
    df["Discount"] = pd.to_numeric(df["Discount"], errors="coerce")

df = df.dropna(subset=["Sales", "Profit", "Order Date"])

st.sidebar.header("Dashboard Filters")

regions = sorted(df["Region"].dropna().unique().tolist())
categories = sorted(df["Category"].dropna().unique().tolist())

selected_regions = st.sidebar.multiselect(
    "Choose Region",
    regions,
    default=regions
)

selected_categories = st.sidebar.multiselect(
    "Choose Category",
    categories,
    default=categories
)

min_date = df["Order Date"].min().date()
max_date = df["Order Date"].max().date()

date_range = st.sidebar.date_input(
    "Choose Order Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

filtered_df = df[
    df["Region"].isin(selected_regions)
    & df["Category"].isin(selected_categories)
].copy()

if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start_date, end_date = date_range
    filtered_df = filtered_df[
        filtered_df["Order Date"].dt.date.between(start_date, end_date)
    ]

if filtered_df.empty:
    st.warning("No data found for these filters. Please change your selection.")
    st.stop()

total_sales = filtered_df["Sales"].sum()
total_profit = filtered_df["Profit"].sum()
total_orders = filtered_df["Order ID"].nunique()

if "Discount" in filtered_df.columns:
    avg_discount = filtered_df["Discount"].mean()
else:
    avg_discount = 0

st.subheader("Business Performance")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Sales", f"${total_sales:,.2f}")
col2.metric("Total Profit", f"${total_profit:,.2f}")
col3.metric("Total Orders", f"{total_orders:,}")
col4.metric("Average Discount", f"{avg_discount:.1%}")

st.divider()

category_data = filtered_df.groupby(
    "Category", as_index=False
).agg(
    Sales=("Sales", "sum"),
    Profit=("Profit", "sum")
)

region_data = filtered_df.groupby(
    "Region", as_index=False
).agg(
    Sales=("Sales", "sum"),
    Profit=("Profit", "sum")
)

left, right = st.columns(2)

with left:
    st.subheader("Sales by Category")
    fig1 = px.bar(
        category_data,
        x="Category",
        y="Sales",
        color="Category",
        title="Total Sales by Category"
    )
    st.plotly_chart(fig1, use_container_width=True)

with right:
    st.subheader("Profit by Region")
    fig2 = px.bar(
        region_data,
        x="Region",
        y="Profit",
        color="Region",
        title="Total Profit by Region"
    )
    st.plotly_chart(fig2, use_container_width=True)

st.subheader("Monthly Sales Trend")

monthly_data = (
    filtered_df.assign(
        Month=filtered_df["Order Date"].dt.to_period("M").astype(str)
    )
    .groupby("Month", as_index=False)
    .agg(
        Sales=("Sales", "sum"),
        Profit=("Profit", "sum")
    )
)

fig3 = px.line(
    monthly_data,
    x="Month",
    y="Sales",
    markers=True,
    title="Monthly Sales Trend"
)

st.plotly_chart(fig3, use_container_width=True)

st.subheader("Filtered Sales Records")
st.dataframe(filtered_df, use_container_width=True)

st.download_button(
    "Download Filtered Data",
    data=filtered_df.to_csv(index=False).encode("utf-8"),
    file_name="filtered_sales_data.csv",
    mime="text/csv"
)

st.success("Dashboard loaded successfully!")
