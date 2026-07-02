"""Read-only query helpers over the DuckDB dbt models (curve + 2s10s spread).

Gaps are preserved everywhere: these only return rows that exist in the models —
a missing Tenor or a non-trading day is simply absent, never zero-filled.
"""

import re
import calendar
from datetime import date

import duckdb

from services.yields_query_service.config import CURVE_TABLE, SPREAD_TABLE


def latest_trading_date(con: duckdb.DuckDBPyConnection) -> date | None:
    row = con.execute(f"select max(trading_date) from {CURVE_TABLE}").fetchone()
    return row[0] if row and row[0] else None


def window_start(latest: date, window: str) -> date | None:
    """Resolve a window label (`6M`, `1Y`, `2Y`, `5Y`, `max`) to a start date."""
    w = (window or "").lower()
    if w in ("", "max", "all"):
        return None
    m = re.fullmatch(r"(\d+)\s*([my])", w)
    if not m:
        return None
    n, unit = int(m.group(1)), m.group(2)
    if unit == "y":
        try:
            return latest.replace(year=latest.year - n)
        except ValueError:  # Feb 29
            return latest.replace(year=latest.year - n, day=28)
    idx = latest.year * 12 + (latest.month - 1) - n
    y, mo = divmod(idx, 12)
    mo += 1
    day = min(latest.day, calendar.monthrange(y, mo)[1])
    return date(y, mo, day)


def resolve_available_date(con: duckdb.DuckDBPyConnection, target: date) -> date | None:
    """Nearest available Trading Date on or before `target` (honest gap handling)."""
    row = con.execute(
        f"select max(trading_date) from {CURVE_TABLE} where trading_date <= ?",
        [target],
    ).fetchone()
    return row[0] if row and row[0] else None


def comparison_target(base: date, vs: str) -> date:
    """Interpret a comparison selector: an ISO date, or a `1M`/`1Y`-style offset."""
    try:
        return date.fromisoformat(vs)
    except (ValueError, TypeError):
        pass
    return window_start(base, vs) or base


def curve_points(con: duckdb.DuckDBPyConnection, trading_date: date):
    rows = con.execute(
        f"select tenor, tenor_order, yield from {CURVE_TABLE} "
        f"where trading_date = ? order by tenor_order",
        [trading_date],
    ).fetchall()
    return [{"tenor": t, "tenor_order": o, "yield_": y} for t, o, y in rows]


def spread_series(con: duckdb.DuckDBPyConnection, start: date | None):
    sql = f"select trading_date, spread_bps, is_inverted from {SPREAD_TABLE}"
    params: list = []
    if start is not None:
        sql += " where trading_date >= ?"
        params.append(start)
    sql += " order by trading_date"
    rows = con.execute(sql, params).fetchall()
    return [{"trading_date": d, "spread_bps": s, "is_inverted": inv} for d, s, inv in rows]


def tenor_series(con: duckdb.DuckDBPyConnection, tenor: str, start: date | None):
    sql = f"select trading_date, yield from {CURVE_TABLE} where tenor = ?"
    params: list = [tenor]
    if start is not None:
        sql += " and trading_date >= ?"
        params.append(start)
    sql += " order by trading_date"
    rows = con.execute(sql, params).fetchall()
    return [{"trading_date": d, "yield_": y} for d, y in rows]
