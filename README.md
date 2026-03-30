# E-Commerce Sales Analysis

An end-to-end data analysis project built with MySQL, Python, and Streamlit.

## Tech Stack
- MySQL — database & SQL analysis
- Python (Faker, Pandas) — data generation
- Streamlit + Plotly — interactive dashboard
- SQLAlchemy — database connection

## Features
- 10 SQL queries covering JOINs, CTEs, Window Functions
- KPI cards: Revenue, Orders, Customers, Avg Order Value
- 6 interactive charts: Category revenue, Monthly trend,
  Top products, Order status, Payment methods, MoM growth

## Setup
1. Clone the repo
2. Create `.env` file with your DB credentials
3. Run `pip install -r requirements.txt`
4. Run `python generate_data.py`
5. Run `streamlit run dashboard.py`

## Dashboard Preview
![Dashboard](screenshots/dashboard.png)
