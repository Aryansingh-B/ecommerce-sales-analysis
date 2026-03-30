-- ── Q1: Overall business KPIs ─────────────────────────────
SELECT
    COUNT(DISTINCT order_id)                        AS total_orders,
    COUNT(DISTINCT customer_id)                     AS unique_customers,
    ROUND(SUM(total_amount), 2)                     AS total_revenue,
    ROUND(AVG(total_amount), 2)                     AS avg_order_value,
    ROUND(SUM(total_amount) / COUNT(DISTINCT customer_id), 2) AS revenue_per_customer
FROM orders
WHERE status != 'Cancelled';

-- ── Q2: Revenue breakdown by product category ─────────────
SELECT
    c.category_name,
    COUNT(DISTINCT o.order_id)          AS total_orders,
    SUM(oi.quantity)                    AS units_sold,
    ROUND(SUM(oi.quantity * oi.unit_price), 2) AS category_revenue,
    ROUND(SUM(oi.quantity * oi.unit_price) * 100.0
          / SUM(SUM(oi.quantity * oi.unit_price)) OVER (), 2) AS revenue_pct
FROM order_items oi
JOIN orders o       ON oi.order_id   = o.order_id
JOIN products p     ON oi.product_id = p.product_id
JOIN categories c   ON p.category_id = c.category_id
WHERE o.status != 'Cancelled'
GROUP BY c.category_name
ORDER BY category_revenue DESC;

-- ── Q3: Top 5 products by revenue with RANK() ─────────────
WITH product_sales AS (
    SELECT
        p.product_name,
        c.category_name,
        SUM(oi.quantity)                           AS units_sold,
        ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue,
        RANK() OVER (ORDER BY SUM(oi.quantity * oi.unit_price) DESC) AS revenue_rank
    FROM order_items oi
    JOIN products p   ON oi.product_id = p.product_id
    JOIN categories c ON p.category_id = c.category_id
    JOIN orders o     ON oi.order_id   = o.order_id
    WHERE o.status != 'Cancelled'
    GROUP BY p.product_name, c.category_name
)
SELECT * FROM product_sales
WHERE revenue_rank <= 5;

-- ── Q4: Monthly revenue trend + MoM change ────────────────
WITH monthly AS (
    SELECT
        DATE_FORMAT(order_date, '%Y-%m')        AS month,
        ROUND(SUM(total_amount), 2)             AS revenue
    FROM orders
    WHERE status != 'Cancelled'
    GROUP BY DATE_FORMAT(order_date, '%Y-%m')
)
SELECT
    month,
    revenue,
    LAG(revenue) OVER (ORDER BY month)         AS prev_month_revenue,
    ROUND(revenue - LAG(revenue) OVER (ORDER BY month), 2) AS mom_change
FROM monthly
ORDER BY month;

-- ── Q5: Repeat customers (ordered more than once) ─────────
WITH customer_orders AS (
    SELECT
        customer_id,
        COUNT(order_id)             AS order_count,
        ROUND(SUM(total_amount), 2) AS total_spent
    FROM orders
    WHERE status != 'Cancelled'
    GROUP BY customer_id
    HAVING COUNT(order_id) > 1
)
SELECT
    c.name,
    c.city,
    c.state,
    co.order_count,
    co.total_spent
FROM customer_orders co
JOIN customers c ON co.customer_id = c.customer_id
ORDER BY co.total_spent DESC
LIMIT 10;

-- ── Q6: Top 10 customers by lifetime value ────────────────
WITH customer_stats AS (
    SELECT
        c.customer_id,
        c.name,
        c.city,
        c.state,
        COUNT(DISTINCT o.order_id)          AS total_orders,
        ROUND(SUM(o.total_amount), 2)       AS lifetime_value,
        ROUND(AVG(o.total_amount), 2)       AS avg_order_value,
        MIN(o.order_date)                   AS first_order,
        MAX(o.order_date)                   AS last_order
    FROM customers c
    JOIN orders o ON c.customer_id = o.customer_id
    WHERE o.status != 'Cancelled'
    GROUP BY c.customer_id, c.name, c.city, c.state
),
ranked AS (
    SELECT *,
        RANK() OVER (ORDER BY lifetime_value DESC) AS clv_rank
    FROM customer_stats
)
SELECT * FROM ranked
WHERE clv_rank <= 10;

-- ── Q7: Order status summary with revenue impact ──────────
SELECT
    status,
    COUNT(order_id)                             AS total_orders,
    ROUND(SUM(total_amount), 2)                 AS total_revenue,
    ROUND(AVG(total_amount), 2)                 AS avg_order_value,
    CASE
        WHEN status = 'Delivered'  THEN 'Revenue realized'
        WHEN status = 'Shipped'    THEN 'Revenue in transit'
        WHEN status = 'Pending'    THEN 'Revenue at risk'
        WHEN status = 'Cancelled'  THEN 'Revenue lost'
    END                                         AS business_impact
FROM orders
GROUP BY status
ORDER BY total_revenue DESC;

-- ── Q8: #1 spending customer in each state ────────────────
WITH state_spending AS (
    SELECT
        c.state,
        c.name,
        c.city,
        ROUND(SUM(o.total_amount), 2)   AS total_spent,
        COUNT(o.order_id)               AS total_orders,
        ROW_NUMBER() OVER (
            PARTITION BY c.state
            ORDER BY SUM(o.total_amount) DESC
        )                               AS rn
    FROM customers c
    JOIN orders o ON c.customer_id = o.customer_id
    WHERE o.status != 'Cancelled'
    GROUP BY c.state, c.name, c.city
)
SELECT
    state,
    name,
    city,
    total_spent,
    total_orders
FROM state_spending
WHERE rn = 1
ORDER BY total_spent DESC;

-- ── Q9: Most common product pairs bought in same order ────
SELECT
    p1.product_name        AS product_1,
    p2.product_name        AS product_2,
    COUNT(*)               AS times_bought_together
FROM order_items oi1
JOIN order_items oi2 ON oi1.order_id   = oi2.order_id
                     AND oi1.product_id < oi2.product_id
JOIN products p1     ON oi1.product_id = p1.product_id
JOIN products p2     ON oi2.product_id = p2.product_id
GROUP BY p1.product_name, p2.product_name
ORDER BY times_bought_together DESC
LIMIT 10;

-- ── Q10: MoM revenue growth percentage ───────────────────
WITH monthly_revenue AS (
    SELECT
        DATE_FORMAT(order_date, '%Y-%m')    AS month,
        ROUND(SUM(total_amount), 2)         AS revenue
    FROM orders
    WHERE status != 'Cancelled'
    GROUP BY DATE_FORMAT(order_date, '%Y-%m')
),
with_lag AS (
    SELECT
        month,
        revenue,
        LAG(revenue) OVER (ORDER BY month)  AS prev_revenue
    FROM monthly_revenue
)
SELECT
    month,
    revenue,
    prev_revenue,
    ROUND(
        (revenue - prev_revenue) / prev_revenue * 100
    , 2)                                    AS mom_growth_pct,
    CASE
        WHEN revenue > prev_revenue THEN 'Growth'
        WHEN revenue < prev_revenue THEN 'Decline'
        ELSE 'Flat'
    END                                     AS trend
FROM with_lag
WHERE prev_revenue IS NOT NULL
ORDER BY month;