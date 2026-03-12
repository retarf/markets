import os
from pyspark.sql.types import StructType, StructField, DateType, DoubleType, StringType

from warehouse.snowflake.session import get_spark_session


APP_NAME = "STOCK_DATA_APP"
SCHEMA = f"MARKETS.{os.environ.get("ENVIRONMENT")}"
METASTORE_SCHEMA = f"MARKETS.{os.environ.get("ENVIRONMENT")}_METASTORE"
DATA_DIR = f"/project/datalake/{APP_NAME}"
PYSPARK_DATE_FORMAT = "yyyy-MM-dd"
RAW_STOCK_DATA = "MARKETS.RAW.RAW_STOCK_DATA"
DATE_FORMAT = "%Y-%m-%d"


class Column:
    ticker = "TICKER"
    date = "TRADING_DATE"
    open = "OPEN"
    high = "HIGH"
    low = "LOW"
    close = "CLOSE"
    volume = "VOLUME"


input_schema = StructType(
    [
        StructField(Column.date, DateType(), True),
        StructField(Column.open, DoubleType(), True),
        StructField(Column.high, DoubleType(), True),
        StructField(Column.low, DoubleType(), True),
        StructField(Column.close, DoubleType(), True),
        StructField(Column.volume, DoubleType(), True)
    ]
)


output_schema = StructType(
    [
        StructField(Column.ticker, StringType(), True),
        StructField(Column.date, DateType(), True),
        StructField(Column.open, DoubleType(), True),
        StructField(Column.high, DoubleType(), True),
        StructField(Column.low, DoubleType(), True),
        StructField(Column.close, DoubleType(), True),
        StructField(Column.volume, DoubleType(), True)
    ]
)


spark = get_spark_session(APP_NAME)