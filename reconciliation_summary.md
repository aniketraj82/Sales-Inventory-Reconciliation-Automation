# Daily Reconciliation Summary

## Pipeline Run

- Sales rows loaded: 16
- Inventory rows loaded: 15
- Warehouse adjustment rows loaded: 4
- SKUs reconciled: 16
- Exceptions found: 4
- Reconciled sales value: $8,808.57

## Status Summary

| Status | SKU Count | Sales Value | System Variance | Warehouse Variance |
| --- | ---: | ---: | ---: | ---: |
| MATCHED | 12 | $6,168.15 | 0 | 0 |
| MISSING_INVENTORY_RECORD | 1 | $60.00 | 5 | 0 |
| OVERSELL_RISK | 1 | $639.92 | 0 | 0 |
| SYSTEM_STOCK_MISMATCH | 1 | $626.50 | 2 | 2 |
| UNPOSTED_WAREHOUSE_ADJUSTMENT | 1 | $1,314.00 | 0 | 1 |

## Recommended Follow-Up

- Review missing inventory records before the next stock close.
- Post approved warehouse adjustments in ERP.
- Investigate oversell risks and negative system stock.
- Confirm physical count mismatches with warehouse operations.
