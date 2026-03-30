import random
import os
from dotenv import load_dotenv
from faker import Faker
import mysql.connector
from datetime import date, timedelta

fake = Faker('en_IN')  # Indian names/cities since you're in India 🇮🇳
load_dotenv()  # reads your .env file

# ── DB CONNECTION ──────────────────────────────────────────
conn = mysql.connector.connect(
  host=os.getenv("DB_HOST"),
  user=os.getenv("DB_USER"),
  password=os.getenv("DB_PASSWORD"),
  database=os.getenv("DB_NAME")
)
cursor = conn.cursor()

# ── 1. CATEGORIES ──────────────────────────────────────────
categories = ["Electronics", "Clothing", "Books", "Home & Kitchen", "Sports", "Beauty", "Toys"]

cursor.executemany(
    "INSERT INTO categories (category_name) VALUES (%s)",
    [(c,) for c in categories]
)
print(f"✅ {len(categories)} categories inserted")

# ── 2. PRODUCTS ────────────────────────────────────────────
products = [
    # Electronics
    ("iPhone 15",         1, 79999, 50),
    ("Samsung TV 43inch", 1, 34999, 30),
    ("Boat Earbuds",      1,  2999, 200),
    ("Laptop HP 15",      1, 55000, 40),
    ("USB-C Hub",         1,  1499, 150),
    # Clothing
    ("Men's Casual Shirt",  2,  899, 300),
    ("Women's Kurti",       2,  599, 400),
    ("Running Shoes Nike",  2, 4999, 100),
    ("Denim Jeans",         2, 1299, 250),
    ("Winter Jacket",       2, 2499, 120),
    # Books
    ("Atomic Habits",          3,  399, 500),
    ("Python Crash Course",    3,  549, 300),
    ("The Alchemist",          3,  299, 600),
    ("Clean Code",             3,  649, 200),
    ("Data Science Handbook",  3,  799, 180),
    # Home & Kitchen
    ("Prestige Cooker 5L",  4, 1899, 150),
    ("Mixer Grinder",       4, 3499, 100),
    ("Bed Sheet Set",       4,  999, 200),
    ("Air Fryer",           4, 5999,  80),
    ("Water Bottle Steel",  4,  449, 350),
    # Sports
    ("Cricket Bat SS",       5, 2999, 80),
    ("Yoga Mat",             5,  799, 200),
    ("Badminton Racket Set", 5, 1499, 150),
    ("Protein Whey 1kg",     5, 1999, 120),
    ("Cycling Gloves",       5,  399, 180),
    # Beauty
    ("Lakme Foundation",   6,  599, 300),
    ("Himalaya Face Wash", 6,  199, 500),
    ("Hair Serum LOreal",  6,  899, 200),
    ("Sunscreen SPF50",    6,  449, 350),
    ("Lipstick Maybelline",6,  499, 400),
    # Toys
    ("Lego Classic Set",   7, 2499,  80),
    ("Remote Car",         7,  999, 150),
    ("Barbie Doll",        7,  799, 200),
    ("Board Game Cluedo",  7, 1299,  90),
    ("Rubiks Cube",        7,  299, 300),
]

cursor.executemany(
    "INSERT INTO products (product_name, category_id, price, stock_quantity) VALUES (%s, %s, %s, %s)",
    products
)
print(f"✅ {len(products)} products inserted")

# ── 3. CUSTOMERS ───────────────────────────────────────────
customer_data = []
for _ in range(300):
    customer_data.append((
        fake.name(),
        fake.unique.email(),
        fake.city(),
        fake.state(),
        fake.date_between(start_date=date(2022, 1, 1), end_date=date(2024, 6, 30))
    ))

cursor.executemany(
    "INSERT INTO customers (name, email, city, state, signup_date) VALUES (%s, %s, %s, %s, %s)",
    customer_data
)
print(f"✅ 300 customers inserted")

# ── 4 & 5. ORDERS + ORDER ITEMS ────────────────────────────
statuses        = ["Delivered", "Delivered", "Delivered", "Shipped", "Pending", "Cancelled"]
payment_methods = ["UPI", "Credit Card", "Debit Card", "Net Banking", "Cash on Delivery"]
product_ids     = list(range(1, len(products) + 1))
product_prices  = {i+1: p[2] for i, p in enumerate(products)}

orders_inserted     = 0
order_items_inserted = 0

for order_id in range(1, 1001):  # 1000 orders
    customer_id    = random.randint(1, 300)
    order_date     = fake.date_between(start_date=date(2023, 1, 1), end_date=date(2024, 12, 31))
    status         = random.choice(statuses)
    payment_method = random.choice(payment_methods)

    # pick 1–4 products per order
    num_items     = random.randint(1, 4)
    chosen_prods  = random.sample(product_ids, num_items)

    items     = []
    total     = 0
    for pid in chosen_prods:
        qty        = random.randint(1, 3)
        unit_price = product_prices[pid]
        items.append((order_id, pid, qty, unit_price))
        total     += qty * unit_price

    cursor.execute(
        "INSERT INTO orders (customer_id, order_date, status, total_amount, payment_method) VALUES (%s, %s, %s, %s, %s)",
        (customer_id, order_date, status, round(total, 2), payment_method)
    )

    cursor.executemany(
        "INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (%s, %s, %s, %s)",
        items
    )

    orders_inserted      += 1
    order_items_inserted += len(items)

conn.commit()
print(f"✅ {orders_inserted} orders inserted")
print(f"✅ {order_items_inserted} order items inserted")
print("\n🎉 Database ready! All data loaded successfully.")

cursor.close()
conn.close()