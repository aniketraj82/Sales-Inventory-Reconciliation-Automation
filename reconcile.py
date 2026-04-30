from __future__ import annotations

import csv
import sqlite3
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
REPORT_DIR = ROOT / "reports"
SQL_DIR = ROOT / "sql"
DB_PATH = PROCESSED_DIR / "sales_inventory_reconciliation.db"


@dataclass(frozen=True)
class SourceFile:
    table_name: str
    path: Path
    required_columns: tuple[str, ...]


SOURCE_FILES = (
    SourceFile(
        table_name="sales_orders",
        path=RAW_DIR / "sales_orders.csv",
        required_columns=(
            "order_id",
            "order_date",
            "sku",
            "product_name",
            "quantity_sold",
            "unit_price",
            "channel",
            "status",
        ),
    ),
    SourceFile(
        table_name="inventory_snapshot",
        path=RAW_DIR / "inventory_snapshot.csv",
        required_columns=(
            "snapshot_date",
            "sku",
            "product_name",
            "opening_stock",
            "received_qty",
            "system_closing_stock",
            "warehouse_count",
        ),
    ),
    SourceFile(
        table_name="warehouse_adjustments",
        path=RAW_DIR / "warehouse_adjustments.csv",
        required_columns=(
            "adjustment_id",
            "adjustment_date",
            "sku",
            "adjustment_qty",
            "reason",
            "posted_to_erp",
        ),
    ),
)


NUMERIC_COLUMNS = {
    "quantity_sold": int,
    "unit_price": float,
    "opening_stock": int,
    "received_qty": int,
    "system_closing_stock": int,
    "warehouse_count": int,
    "adjustment_qty": int,
}


def read_sql(file_name: str) -> str:
    return (SQL_DIR / file_name).read_text(encoding="utf-8")


def validate_source(source: SourceFile) -> list[dict[str, object]]:
    if not source.path.exists():
        raise FileNotFoundError(f"Missing input file: {source.path}")

    with source.path.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        if reader.fieldnames is None:
            raise ValueError(f"{source.path.name} has no header row")

        missing_columns = set(source.required_columns) - set(reader.fieldnames)
        if missing_columns:
            missing = ", ".join(sorted(missing_columns))
            raise ValueError(f"{source.path.name} is missing required columns: {missing}")

        rows = []
        for row_number, row in enumerate(reader, start=2):
            clean_row: dict[str, object] = {}
            for column in source.required_columns:
                value = row[column].strip()
                if value == "":
                    raise ValueError(
                        f"{source.path.name} row {row_number} has blank value for {column}"
                    )

                converter = NUMERIC_COLUMNS.get(column)
                clean_row[column] = converter(value) if converter else value
            rows.append(clean_row)

    return rows


def load_table(connection: sqlite3.Connection, source: SourceFile) -> int:
    rows = validate_source(source)
    if not rows:
        return 0

    columns = source.required_columns
    placeholders = ", ".join("?" for _ in columns)
    column_list = ", ".join(columns)
    values = [tuple(row[column] for column in columns) for row in rows]

    connection.executemany(
        f"INSERT INTO {source.table_name} ({column_list}) VALUES ({placeholders})",
        values,
    )
    return len(rows)


def rows_to_csv(path: Path, rows: list[sqlite3.Row]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return

    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(dict(row) for row in rows)


def summarize(reconciliation_rows: list[sqlite3.Row]) -> list[dict[str, object]]:
    summary: dict[str, dict[str, object]] = {}
    for row in reconciliation_rows:
        status = str(row["reconciliation_status"])
        bucket = summary.setdefault(
            status,
            {
                "reconciliation_status": status,
                "sku_count": 0,
                "sales_value": 0.0,
                "absolute_system_variance": 0,
                "absolute_warehouse_variance": 0,
            },
        )
        bucket["sku_count"] = int(bucket["sku_count"]) + 1
        bucket["sales_value"] = round(float(bucket["sales_value"]) + float(row["sales_value"]), 2)
        bucket["absolute_system_variance"] = int(bucket["absolute_system_variance"]) + abs(
            int(row["system_variance"])
        )
        bucket["absolute_warehouse_variance"] = int(bucket["absolute_warehouse_variance"]) + abs(
            int(row["warehouse_variance"])
        )

    return sorted(summary.values(), key=lambda item: str(item["reconciliation_status"]))


def write_summary_markdown(
    path: Path,
    loaded_counts: dict[str, int],
    summary_rows: list[dict[str, object]],
    exceptions: list[sqlite3.Row],
) -> None:
    total_skus = sum(int(row["sku_count"]) for row in summary_rows)
    total_exceptions = len(exceptions)
    total_sales_value = sum(float(row["sales_value"]) for row in summary_rows)

    lines = [
        "# Daily Reconciliation Summary",
        "",
        "## Pipeline Run",
        "",
        f"- Sales rows loaded: {loaded_counts['sales_orders']}",
        f"- Inventory rows loaded: {loaded_counts['inventory_snapshot']}",
        f"- Warehouse adjustment rows loaded: {loaded_counts['warehouse_adjustments']}",
        f"- SKUs reconciled: {total_skus}",
        f"- Exceptions found: {total_exceptions}",
        f"- Reconciled sales value: ${total_sales_value:,.2f}",
        "",
        "## Status Summary",
        "",
        "| Status | SKU Count | Sales Value | System Variance | Warehouse Variance |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]

    for row in summary_rows:
        lines.append(
            "| {status} | {sku_count} | ${sales_value:,.2f} | {system} | {warehouse} |".format(
                status=row["reconciliation_status"],
                sku_count=row["sku_count"],
                sales_value=float(row["sales_value"]),
                system=row["absolute_system_variance"],
                warehouse=row["absolute_warehouse_variance"],
            )
        )

    lines.extend(
        [
            "",
            "## Recommended Follow-Up",
            "",
            "- Review missing inventory records before the next stock close.",
            "- Post approved warehouse adjustments in ERP.",
            "- Investigate oversell risks and negative system stock.",
            "- Confirm physical count mismatches with warehouse operations.",
            "",
        ]
    )

    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode = MEMORY")
        connection.executescript(read_sql("schema.sql"))

        loaded_counts = {
            source.table_name: load_table(connection, source) for source in SOURCE_FILES
        }
        connection.commit()

        reconciliation_rows = connection.execute(read_sql("reconciliation.sql")).fetchall()

    exceptions = [
        row for row in reconciliation_rows if row["reconciliation_status"] != "MATCHED"
    ]
    summary_rows = summarize(reconciliation_rows)

    rows_to_csv(REPORT_DIR / "reconciliation_exceptions.csv", exceptions)

    summary_path = REPORT_DIR / "daily_reconciliation_summary.csv"
    with summary_path.open("w", newline="", encoding="utf-8") as csv_file:
        fieldnames = [
            "reconciliation_status",
            "sku_count",
            "sales_value",
            "absolute_system_variance",
            "absolute_warehouse_variance",
        ]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summary_rows)

    write_summary_markdown(
        REPORT_DIR / "reconciliation_summary.md",
        loaded_counts,
        summary_rows,
        exceptions,
    )

    print("Sales and inventory reconciliation complete.")
    print(f"Database: {DB_PATH}")
    print(f"Exception report: {REPORT_DIR / 'reconciliation_exceptions.csv'}")
    print(f"Summary report: {summary_path}")


if __name__ == "__main__":
    main()
