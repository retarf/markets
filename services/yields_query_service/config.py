import os

from yield_data import WAREHOUSE_DB, DEFAULT_WAREHOUSE_DB


# dbt model (table) names in the local DuckDB warehouse.
CURVE_TABLE = "fct_yield_curve"
SPREAD_TABLE = "fct_2s10s_spread"


def db_path() -> str:
    """Path to the local DuckDB warehouse the query service reads (read-only)."""
    return os.environ.get(WAREHOUSE_DB) or DEFAULT_WAREHOUSE_DB
