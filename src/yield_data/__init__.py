import os

APP_NAME = "YIELD_DATA"
# Datalake root is env-configurable so the pipeline runs both in-container
# (default `/project/datalake`) and on a host / worker (set `DATALAKE_ROOT`).
DATALAKE = f"{os.environ.get('DATALAKE_ROOT', '/project/datalake')}/{APP_NAME}"

# Provider date format (US Treasury CSV) and our canonical ISO output format.
PROVIDER_DATE_FORMAT = "%m/%d/%Y"
DATE_FORMAT = "%Y-%m-%d"


class Column:
    tenor = "TENOR"
    date = "TRADING_DATE"
    yield_ = "YIELD"
    source_path = "SOURCE_PATH"
    load_ts = "LOAD_TS"


# The single canonical mapping of Tenor label -> U.S. Treasury CSV column, in
# maturity order. This is the one place the tracked Tenor universe is defined.
TENOR_TO_TREASURY_COLUMN = {
    "1M": "1 Mo",
    "3M": "3 Mo",
    "6M": "6 Mo",
    "1Y": "1 Yr",
    "2Y": "2 Yr",
    "3Y": "3 Yr",
    "5Y": "5 Yr",
    "7Y": "7 Yr",
    "10Y": "10 Yr",
    "20Y": "20 Yr",
    "30Y": "30 Yr",
}

# Maturity-ordered list of the Tenors we track (order matches the mapping above).
TRACKED_TENORS = list(TENOR_TO_TREASURY_COLUMN)

# Maturity rank per Tenor (for curve ordering downstream: 1M < 3M < ... < 30Y).
TENOR_ORDER = {tenor: rank for rank, tenor in enumerate(TRACKED_TENORS)}

# Local-first warehouse: DuckDB (a single local file), no Snowflake/Spark needed
# for this domain. Overridable via env; defaults to a file in the datalake root.
WAREHOUSE_DB = "YIELD_WAREHOUSE_DB"
DEFAULT_WAREHOUSE_DB = f"{DATALAKE}/yield_warehouse.duckdb"
RAW_TABLE = "RAW_TREASURY_YIELDS"
METASTORE_TABLE = "METASTORE_LAST_TRADING_DATE"

# Yield-appropriate sanity band (percent); NOT the equity volume/HIGH>=LOW rules.
YIELD_MIN = -5.0
YIELD_MAX = 25.0

