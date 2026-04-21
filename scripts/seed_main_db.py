#!/usr/bin/env python3
"""
Загрузка anonymized incity orders (train.csv) в Postgres main_db.
Запуск с хоста: docker compose up -d main-db, затем pip install -r scripts/requirements-seed.txt
и python scripts/seed_main_db.py --limit 5000
"""
from __future__ import annotations

import argparse
import csv
import sys
import time
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CSV = REPO_ROOT / "dataset" / "train.csv"
DEFAULT_DSN = "postgresql://postgres:postgres@localhost:5447/main_db"

COLS = [
    "city_id",
    "order_id",
    "tender_id",
    "user_id",
    "driver_id",
    "offset_hours",
    "status_order",
    "status_tender",
    "order_timestamp",
    "tender_timestamp",
    "driveraccept_timestamp",
    "driverarrived_timestamp",
    "driverstarttheride_timestamp",
    "driverdone_timestamp",
    "clientcancel_timestamp",
    "drivercancel_timestamp",
    "order_modified_local",
    "cancel_before_accept_local",
    "distance_in_meters",
    "duration_in_seconds",
    "price_order_local",
    "price_tender_local",
    "price_start_local",
]

DDL = """
CREATE TABLE IF NOT EXISTS public.drivee_orders (
    city_id BIGINT,
    order_id TEXT,
    tender_id TEXT,
    user_id TEXT,
    driver_id TEXT,
    offset_hours INTEGER,
    status_order TEXT,
    status_tender TEXT,
    order_timestamp TIMESTAMPTZ,
    tender_timestamp TIMESTAMPTZ,
    driveraccept_timestamp TIMESTAMPTZ,
    driverarrived_timestamp TIMESTAMPTZ,
    driverstarttheride_timestamp TIMESTAMPTZ,
    driverdone_timestamp TIMESTAMPTZ,
    clientcancel_timestamp TIMESTAMPTZ,
    drivercancel_timestamp TIMESTAMPTZ,
    order_modified_local TIMESTAMPTZ,
    cancel_before_accept_local TIMESTAMPTZ,
    distance_in_meters BIGINT,
    duration_in_seconds BIGINT,
    price_order_local NUMERIC(20, 6),
    price_tender_local NUMERIC(20, 6),
    price_start_local NUMERIC(20, 6)
);
"""


def _strip(s: Optional[str]) -> str:
    return (s or "").strip()


def _parse_ts(raw: Optional[str]) -> Any:
    s = _strip(raw)
    if not s:
        return None
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        return datetime.fromisoformat(s)
    except ValueError:
        return None


def _parse_int(raw: Optional[str]) -> Any:
    s = _strip(raw)
    if not s:
        return None
    try:
        return int(s)
    except ValueError:
        return None


def _parse_bigint(raw: Optional[str]) -> Any:
    s = _strip(raw)
    if not s:
        return None
    try:
        return int(float(s))
    except ValueError:
        return None


def _parse_numeric(raw: Optional[str]) -> Any:
    s = _strip(raw)
    if not s:
        return None
    try:
        return Decimal(s.replace(",", "."))
    except (InvalidOperation, ValueError):
        return None


def _wait_for_db(dsn: str, seconds: int) -> bool:
    if seconds <= 0:
        return True
    try:
        import psycopg
    except ImportError:
        print("Install: pip install -r scripts/requirements-seed.txt", file=sys.stderr)
        return False
    deadline = time.monotonic() + seconds
    last_err: Optional[BaseException] = None
    while time.monotonic() < deadline:
        try:
            with psycopg.connect(dsn, connect_timeout=5) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
            return True
        except Exception as e:
            last_err = e
            time.sleep(1)
    print(f"Timeout waiting for database ({seconds}s): {last_err}", file=sys.stderr)
    return False


def _row_tuple(row: dict[str, str]) -> tuple[Any, ...]:
    return (
        _parse_bigint(row.get("city_id")),
        _strip(row.get("order_id")) or None,
        _strip(row.get("tender_id")) or None,
        _strip(row.get("user_id")) or None,
        _strip(row.get("driver_id")) or None,
        _parse_int(row.get("offset_hours")),
        _strip(row.get("status_order")) or None,
        _strip(row.get("status_tender")) or None,
        _parse_ts(row.get("order_timestamp")),
        _parse_ts(row.get("tender_timestamp")),
        _parse_ts(row.get("driveraccept_timestamp")),
        _parse_ts(row.get("driverarrived_timestamp")),
        _parse_ts(row.get("driverstarttheride_timestamp")),
        _parse_ts(row.get("driverdone_timestamp")),
        _parse_ts(row.get("clientcancel_timestamp")),
        _parse_ts(row.get("drivercancel_timestamp")),
        _parse_ts(row.get("order_modified_local")),
        _parse_ts(row.get("cancel_before_accept_local")),
        _parse_bigint(row.get("distance_in_meters")),
        _parse_bigint(row.get("duration_in_seconds")),
        _parse_numeric(row.get("price_order_local")),
        _parse_numeric(row.get("price_tender_local")),
        _parse_numeric(row.get("price_start_local")),
    )


def main() -> int:
    p = argparse.ArgumentParser(description="Load train.csv into main_db.drivee_orders")
    p.add_argument("--dsn", default=DEFAULT_DSN, help="PostgreSQL connection URL")
    p.add_argument(
        "--csv",
        type=Path,
        default=DEFAULT_CSV,
        help="Path to CSV (default: dataset/train.csv)",
    )
    p.add_argument("--limit", type=int, default=None, help="Max data rows after header")
    p.add_argument(
        "--skip-if-count-ge",
        type=int,
        default=None,
        metavar="N",
        help="If drivee_orders already has >= N rows, exit without inserting",
    )
    p.add_argument(
        "--replace",
        action="store_true",
        help="TRUNCATE drivee_orders before insert",
    )
    p.add_argument(
        "--wait-seconds",
        type=int,
        default=0,
        metavar="S",
        help="Retry DSN until a connection succeeds (0 = off)",
    )
    args = p.parse_args()

    csv_path = args.csv if args.csv.is_absolute() else (REPO_ROOT / args.csv).resolve()
    if not csv_path.is_file():
        print(f"CSV not found: {csv_path}", file=sys.stderr)
        return 1

    try:
        import psycopg
    except ImportError:
        print("Install: pip install -r scripts/requirements-seed.txt", file=sys.stderr)
        return 1

    if not _wait_for_db(args.dsn, args.wait_seconds):
        return 1

    placeholders = ", ".join(f"%({c})s" for c in COLS)
    insert_sql = (
        f"INSERT INTO public.drivee_orders ({', '.join(COLS)}) "
        f"VALUES ({placeholders})"
    )

    with psycopg.connect(args.dsn, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(DDL)
            if args.replace:
                cur.execute("TRUNCATE TABLE public.drivee_orders")
            if args.skip_if_count_ge is not None:
                cur.execute("SELECT count(*)::bigint FROM public.drivee_orders")
                row = cur.fetchone()
                cnt = int(row[0]) if row else 0
                if cnt >= args.skip_if_count_ge:
                    print(
                        f"Skipping seed: drivee_orders has {cnt} rows "
                        f"(>= {args.skip_if_count_ge})"
                    )
                    return 0

        batch: list[dict[str, Any]] = []
        batch_size = 2000
        n = 0

        with csv_path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                print("CSV has no header", file=sys.stderr)
                return 1
            missing = [c for c in COLS if c not in reader.fieldnames]
            if missing:
                print(f"CSV header missing columns: {missing}", file=sys.stderr)
                return 1

            with conn.cursor() as cur:
                for row in reader:
                    if args.limit is not None and n >= args.limit:
                        break
                    batch.append(dict(zip(COLS, _row_tuple(row))))
                    if len(batch) >= batch_size:
                        if args.limit is not None:
                            over = n + len(batch) - args.limit
                            if over > 0:
                                batch = batch[: len(batch) - over]
                        if batch:
                            cur.executemany(insert_sql, batch)
                            n += len(batch)
                            batch.clear()
                        if args.limit is not None and n >= args.limit:
                            break

                if batch and (args.limit is None or n < args.limit):
                    if args.limit is not None:
                        batch = batch[: args.limit - n]
                    if batch:
                        cur.executemany(insert_sql, batch)
                        n += len(batch)

    print(f"Inserted rows: {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
