import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()

# ── PAGE CONFIG ───────────────────────────────────────────
st.set_page_config(
    page_title="E-Commerce Sales Dashboard",
    page_icon="🛒",
    layout="wide"
)

# ── DB CONNECTION ─────────────────────────────────────────
@st.cache_resource
def get_engine():
    url = (
        f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
    )
    return create_engine(url)

engine = get_engine()

def run_query(sql):
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn)

# ── QUERIES ───────────────────────────────────────────────
kpi_query = """
    SELECT
        COUNT(DISTINCT order_id)                                    AS total_orders,
        COUNT(DISTINCT customer_id)                                 AS unique_customers,
        ROUND(SUM(total_amount), 2)                                 AS total_revenue,
        ROUND(AVG(total_amount), 2)                                 AS avg_order_value
    FROM orders WHERE status != 'Cancelled'
"""

category_query = """
    SELECT
        c.category_name,
        ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue,
        SUM(oi.quantity)                            AS units_sold
    FROM order_items oi
    JOIN orders o     ON oi.order_id   = o.order_id
    JOIN products p   ON oi.product_id = p.product_id
    JOIN categories c ON p.category_id = c.category_id
    WHERE o.status != 'Cancelled'
    GROUP BY c.category_name
    ORDER BY revenue DESC
"""

monthly_query = """
    WITH monthly AS (
        SELECT DATE_FORMAT(order_date, '%Y-%m') AS month,
               ROUND(SUM(total_amount), 2)      AS revenue
        FROM orders WHERE status != 'Cancelled'
        GROUP BY DATE_FORMAT(order_date, '%Y-%m')
    )
    SELECT month, revenue,
           ROUND(revenue - LAG(revenue) OVER (ORDER BY month), 2) AS mom_change
    FROM monthly ORDER BY month
"""

top_products_query = """
    SELECT p.product_name,
           SUM(oi.quantity)                            AS units_sold,
           ROUND(SUM(oi.quantity * oi.unit_price), 2)  AS revenue
    FROM order_items oi
    JOIN products p ON oi.product_id = p.product_id
    JOIN orders o   ON oi.order_id   = o.order_id
    WHERE o.status != 'Cancelled'
    GROUP BY p.product_name
    ORDER BY revenue DESC
    LIMIT 10
"""

status_query = """
    SELECT status,
           COUNT(order_id)             AS total_orders,
           ROUND(SUM(total_amount), 2) AS total_revenue
    FROM orders
    GROUP BY status
"""

payment_query = """
    SELECT payment_method,
           COUNT(order_id)             AS total_orders,
           ROUND(SUM(total_amount), 2) AS total_revenue
    FROM orders WHERE status != 'Cancelled'
    GROUP BY payment_method
    ORDER BY total_revenue DESC
"""

# ── LOAD DATA ─────────────────────────────────────────────
kpi_df          = run_query(kpi_query)
category_df     = run_query(category_query)
monthly_df      = run_query(monthly_query)
top_products_df = run_query(top_products_query)
status_df       = run_query(status_query)
payment_df      = run_query(payment_query)

# ── HEADER ────────────────────────────────────────────────
st.title("🛒 E-Commerce Sales Dashboard")
st.markdown("**Powered by MySQL + Python + Streamlit**")
st.divider()

# ── KPI CARDS ─────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Orders",     f"{int(kpi_df['total_orders'][0]):,}")
k2.metric("Unique Customers", f"{int(kpi_df['unique_customers'][0]):,}")
k3.metric("Total Revenue",    f"₹{float(kpi_df['total_revenue'][0]):,.0f}")
k4.metric("Avg Order Value",  f"₹{float(kpi_df['avg_order_value'][0]):,.0f}")

st.divider()

# ── ROW 1: Category Revenue + Monthly Trend ───────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("Revenue by Category")
    fig1 = px.bar(
        category_df,
        x="revenue", y="category_name",
        orientation="h",
        color="revenue",
        color_continuous_scale="Blues",
        text="revenue",
        labels={"revenue": "Revenue (₹)", "category_name": "Category"}
    )
    fig1.update_traces(texttemplate="₹%{text:,.0f}", textposition="outside")
    fig1.update_layout(showlegend=False, coloraxis_showscale=False,
                       yaxis=dict(autorange="reversed"), height=400)
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.subheader("Monthly Revenue Trend")
    fig2 = px.line(
        monthly_df, x="month", y="revenue",
        markers=True,
        labels={"revenue": "Revenue (₹)", "month": "Month"},
        color_discrete_sequence=["#2563eb"]
    )
    fig2.update_layout(height=400)
    st.plotly_chart(fig2, use_container_width=True)

# ── ROW 2: Top Products + Order Status ────────────────────
col3, col4 = st.columns(2)

with col3:
    st.subheader("Top 10 Products by Revenue")
    fig3 = px.bar(
        top_products_df,
        x="revenue", y="product_name",
        orientation="h",
        color="units_sold",
        color_continuous_scale="Teal",
        labels={"revenue": "Revenue (₹)", "product_name": "Product"}
    )
    fig3.update_layout(yaxis=dict(autorange="reversed"),
                       height=420, coloraxis_showscale=False)
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    st.subheader("Order Status Distribution")
    fig4 = px.pie(
        status_df,
        names="status", values="total_orders",
        color_discrete_sequence=px.colors.qualitative.Set2,
        hole=0.4
    )
    fig4.update_layout(height=420)
    st.plotly_chart(fig4, use_container_width=True)

# ── ROW 3: Payment Method + MoM Growth ───────────────────
col5, col6 = st.columns(2)

with col5:
    st.subheader("Revenue by Payment Method")
    fig5 = px.bar(
        payment_df,
        x="payment_method", y="total_revenue",
        color="payment_method",
        color_discrete_sequence=px.colors.qualitative.Pastel,
        labels={"total_revenue": "Revenue (₹)", "payment_method": "Payment Method"}
    )
    fig5.update_layout(showlegend=False, height=380)
    st.plotly_chart(fig5, use_container_width=True)

with col6:
    st.subheader("Month-over-Month Revenue Change")
    colors = ["green" if x >= 0 else "red"
              for x in monthly_df["mom_change"].fillna(0)]
    fig6 = go.Figure(go.Bar(
        x=monthly_df["month"],
        y=monthly_df["mom_change"],
        marker_color=colors
    ))
    fig6.update_layout(
        height=380,
        xaxis_title="Month",
        yaxis_title="MoM Change (₹)"
    )
    st.plotly_chart(fig6, use_container_width=True)

# ── FOOTER ────────────────────────────────────────────────
st.divider()
st.caption("Built by Aryansingh Bais | E-Commerce Sales Analysis Project")