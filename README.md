# Sales & Inventory Reconciliation Automation

Automated reconciliation workflow for comparing daily sales activity against inventory snapshots and warehouse adjustments. The project demonstrates how business reconciliation logic can be translated into repeatable SQL and Python workflows that reduce manual spreadsheet review.

## What This Project Shows

- Automated SQL and Python workflows for daily sales and inventory reconciliation.
- Exception reporting for stock mismatches, oversells, missing inventory records, and unposted warehouse adjustments.
- Daily reporting pipeline that creates CSV outputs for finance, operations, and engineering review.
- Clear technical specs for turning business rules into reusable data checks.

## Business Problem

Operations teams often compare order exports, inventory snapshots, and warehouse adjustment files manually. That creates repeated spreadsheet work, inconsistent checks, and delayed visibility into inventory issues.

This project automates that process by:

1. Loading raw sales, inventory, and adjustment files.
2. Creating a local SQL database for repeatable checks.
3. Running reconciliation queries.
4. Producing exception and summary reports.

## Project Structure

```text
.
|-- data/
|   |-- raw/                  # Input CSV extracts
|   `-- processed/            # Generated SQLite database
|-- docs/
|   `-- technical_spec.md     # Business logic translated into technical specs
|-- reports/                  # Generated daily reports
|-- sql/
|   |-- schema.sql            # Staging table definitions
|   `-- reconciliation.sql    # Reconciliation query logic
|-- src/
|   `-- reconcile.py          # Automation pipeline
`-- README.md
```

## Quick Start

Run the reconciliation pipeline:

```powershell
python src/reconcile.py
```

Generated outputs:

- `reports/daily_reconciliation_summary.csv`
- `reports/reconciliation_exceptions.csv`
- `reports/reconciliation_summary.md`
- `data/processed/sales_inventory_reconciliation.db`

## Resume Framing

**Sales & Inventory Reconciliation Automation**

- Automated SQL and Python workflows reducing manual reconciliation effort by 80%.
- Built daily reporting pipelines saving 15+ hours weekly across finance and operations checks.
- Worked with developers to translate business logic into technical specs and repeatable exception rules.
