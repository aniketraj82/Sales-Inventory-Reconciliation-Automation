# Technical Specification

## Objective

Automate the daily reconciliation of sales orders against inventory snapshots and warehouse adjustments so finance and operations teams can review exceptions instead of manually rebuilding spreadsheet checks.

## Inputs

| File | Grain | Purpose |
| --- | --- | --- |
| `sales_orders.csv` | One row per order line | Completed sales quantity and value by SKU |
| `inventory_snapshot.csv` | One row per SKU per day | Opening stock, receipts, system close, and physical count |
| `warehouse_adjustments.csv` | One row per warehouse adjustment | Posted and unposted inventory corrections |

## Business Rules

1. Cancelled sales are excluded from sold quantity and sales value.
2. Expected closing stock equals opening stock plus receipts minus completed sales plus posted adjustments.
3. Unposted warehouse adjustments are surfaced separately because they may explain operational variances but should not change ERP stock.
4. SKUs sold without inventory records are classified as `MISSING_INVENTORY_RECORD`.
5. SKUs with sales greater than available stock are classified as `OVERSELL_RISK`.
6. Physical warehouse counts that differ from system closing stock are classified as `WAREHOUSE_COUNT_MISMATCH`.
7. Records with no exception are classified as `MATCHED`.

## Output Reports

| Report | Audience | Description |
| --- | --- | --- |
| `daily_reconciliation_summary.csv` | Managers | Count of SKUs and value by reconciliation status |
| `reconciliation_exceptions.csv` | Operations and finance | Row-level exceptions requiring review |
| `reconciliation_summary.md` | Business stakeholders | Human-readable daily summary |

## Implementation Notes

- Python handles file validation, database loading, report generation, and automation orchestration.
- SQL owns reconciliation logic so rules can be reviewed by analysts and developers.
- SQLite is used locally for portability; the SQL can be adapted to SQL Server, PostgreSQL, Snowflake, or BigQuery.

