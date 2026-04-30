DROP TABLE IF EXISTS sales_orders;
DROP TABLE IF EXISTS inventory_snapshot;
DROP TABLE IF EXISTS warehouse_adjustments;

CREATE TABLE sales_orders (
    order_id TEXT PRIMARY KEY,
    order_date TEXT NOT NULL,
    sku TEXT NOT NULL,
    product_name TEXT NOT NULL,
    quantity_sold INTEGER NOT NULL,
    unit_price REAL NOT NULL,
    channel TEXT NOT NULL,
    status TEXT NOT NULL
);

CREATE TABLE inventory_snapshot (
    snapshot_date TEXT NOT NULL,
    sku TEXT PRIMARY KEY,
    product_name TEXT NOT NULL,
    opening_stock INTEGER NOT NULL,
    received_qty INTEGER NOT NULL,
    system_closing_stock INTEGER NOT NULL,
    warehouse_count INTEGER NOT NULL
);

CREATE TABLE warehouse_adjustments (
    adjustment_id TEXT PRIMARY KEY,
    adjustment_date TEXT NOT NULL,
    sku TEXT NOT NULL,
    adjustment_qty INTEGER NOT NULL,
    reason TEXT NOT NULL,
    posted_to_erp TEXT NOT NULL
);

