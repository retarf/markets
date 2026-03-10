from pyspark.sql.types import StructType, StructField, DateType, DoubleType

from warehouse.snowflake.session import get_spark_session


APP_NAME = "STOCK_DATA_APP"
DATA_DIR = f"/project/datalake/{APP_NAME}"
PYSPARK_DATE_FORMAT = "yyyy-MM-dd"


class Column:
    date = "TRADING_DATE"
    open = "OPEN"
    high = "HIGH"
    low = "LOW"
    close = "CLOSE"
    volume = "VOLUME"


schema = StructType(
    [
        StructField(Column.date, DateType(), True),
        StructField(Column.open, DoubleType(), True),
        StructField(Column.high, DoubleType(), True),
        StructField(Column.low, DoubleType(), True),
        StructField(Column.close, DoubleType(), True),
        StructField(Column.volume, DoubleType(), True)
    ]
)


spark = get_spark_session(APP_NAME)