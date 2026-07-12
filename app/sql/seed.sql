--- Seed Sql For Trace

CREATE TABLE IF NOT EXISTS agent_logs (
    trace_id        UUID PRIMARY KEY,
    session_id      TEXT,
    user_query      TEXT,
    selected_agent  TEXT,
    routing_reason  TEXT,
    agent_content   TEXT,
    final_response  TEXT,
    guardrail_flags TEXT[],
    latency_ms      JSONB,
    error           TEXT,
    created_at      TIMESTAMPTZ DEFAULT now()
);

-- sql/seed.sql
-- Seed data for local testing of the SQL Agent.

CREATE TABLE IF NOT EXISTS customers (
    id         SERIAL PRIMARY KEY,
    name       TEXT,
    email      TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS products (
    id       SERIAL PRIMARY KEY,
    name     TEXT,
    category TEXT,
    price    NUMERIC(10,2),
    stock    INTEGER
);

CREATE TABLE IF NOT EXISTS orders (
    id           SERIAL PRIMARY KEY,
    customer_id  INTEGER REFERENCES customers(id),
    order_date   DATE,
    total_amount NUMERIC(10,2),
    status       TEXT
);

CREATE TABLE IF NOT EXISTS order_items (
    id         SERIAL PRIMARY KEY,
    order_id   INTEGER REFERENCES orders(id),
    product_id INTEGER REFERENCES products(id),
    quantity   INTEGER,
    unit_price NUMERIC(10,2)
);

-- Sample data
INSERT INTO customers (name, email) VALUES
  ('Anand Kumar', 'anand@example.com'),
  ('Priya Raj', 'priya@example.com'),
  ('Vijay S', 'vijay@example.com');

INSERT INTO products (name, category, price, stock) VALUES
  ('Vitamin E', 'Tablet', 599.00, 120),
  ('Vitamin A', 'Gel', 2499.00, 45),
  ('ENO', 'drinks', 299.00, 300);

-- Orders: some yesterday, some today, some older
INSERT INTO orders (customer_id, order_date, total_amount, status) VALUES
  (1, CURRENT_DATE - INTERVAL '1 day', 599.00, 'completed'),
  (2, CURRENT_DATE - INTERVAL '1 day', 2499.00, 'completed'),
  (3, CURRENT_DATE - INTERVAL '1 day', 299.00, 'pending'),
  (1, CURRENT_DATE, 2798.00, 'completed'),
  (2, CURRENT_DATE - INTERVAL '5 days', 599.00, 'completed');

INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES
  (1, 1, 1, 599.00),
  (2, 2, 1, 2499.00),
  (3, 3, 1, 299.00),
  (4, 2, 1, 2499.00),
  (4, 1, 1, 299.00);
