WITH completed_sales AS (
    SELECT
        sku,
        MAX(product_name) AS product_name,
        SUM(quantity_sold) AS sold_qty,
        ROUND(SUM(quantity_sold * unit_price), 2) AS sales_value
    FROM sales_orders
    WHERE status = 'Completed'
    GROUP BY sku
),
posted_adjustments AS (
    SELECT
        sku,
        SUM(adjustment_qty) AS posted_adjustment_qty
    FROM warehouse_adjustments
    WHERE posted_to_erp = 'Yes'
    GROUP BY sku
),
unposted_adjustments AS (
    SELECT
        sku,
        SUM(adjustment_qty) AS unposted_adjustment_qty,
        GROUP_CONCAT(reason, '; ') AS unposted_reasons
    FROM warehouse_adjustments
    WHERE posted_to_erp = 'No'
    GROUP BY sku
),
sku_union AS (
    SELECT sku FROM inventory_snapshot
    UNION
    SELECT sku FROM completed_sales
)
SELECT
    u.sku,
    COALESCE(i.product_name, s.product_name, 'Unknown SKU') AS product_name,
    COALESCE(i.opening_stock, 0) AS opening_stock,
    COALESCE(i.received_qty, 0) AS received_qty,
    COALESCE(s.sold_qty, 0) AS sold_qty,
    COALESCE(pa.posted_adjustment_qty, 0) AS posted_adjustment_qty,
    COALESCE(i.system_closing_stock, 0) AS system_closing_stock,
    COALESCE(i.warehouse_count, 0) AS warehouse_count,
    COALESCE(s.sales_value, 0) AS sales_value,
    COALESCE(ua.unposted_adjustment_qty, 0) AS unposted_adjustment_qty,
    COALESCE(ua.unposted_reasons, '') AS unposted_reasons,
    COALESCE(i.opening_stock, 0)
        + COALESCE(i.received_qty, 0)
        - COALESCE(s.sold_qty, 0)
        + COALESCE(pa.posted_adjustment_qty, 0) AS expected_closing_stock,
    COALESCE(i.system_closing_stock, 0)
        - (
            COALESCE(i.opening_stock, 0)
            + COALESCE(i.received_qty, 0)
            - COALESCE(s.sold_qty, 0)
            + COALESCE(pa.posted_adjustment_qty, 0)
        ) AS system_variance,
    COALESCE(i.warehouse_count, 0) - COALESCE(i.system_closing_stock, 0) AS warehouse_variance,
    CASE
        WHEN i.sku IS NULL THEN 'MISSING_INVENTORY_RECORD'
        WHEN COALESCE(i.opening_stock, 0) + COALESCE(i.received_qty, 0) + COALESCE(pa.posted_adjustment_qty, 0) < COALESCE(s.sold_qty, 0) THEN 'OVERSELL_RISK'
        WHEN COALESCE(ua.unposted_adjustment_qty, 0) <> 0 THEN 'UNPOSTED_WAREHOUSE_ADJUSTMENT'
        WHEN COALESCE(i.system_closing_stock, 0) <> (
            COALESCE(i.opening_stock, 0)
            + COALESCE(i.received_qty, 0)
            - COALESCE(s.sold_qty, 0)
            + COALESCE(pa.posted_adjustment_qty, 0)
        ) THEN 'SYSTEM_STOCK_MISMATCH'
        WHEN COALESCE(i.warehouse_count, 0) <> COALESCE(i.system_closing_stock, 0) THEN 'WAREHOUSE_COUNT_MISMATCH'
        ELSE 'MATCHED'
    END AS reconciliation_status
FROM sku_union u
LEFT JOIN inventory_snapshot i ON u.sku = i.sku
LEFT JOIN completed_sales s ON u.sku = s.sku
LEFT JOIN posted_adjustments pa ON u.sku = pa.sku
LEFT JOIN unposted_adjustments ua ON u.sku = ua.sku
ORDER BY reconciliation_status DESC, ABS(system_variance) DESC, u.sku;

