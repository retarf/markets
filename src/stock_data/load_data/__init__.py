from pyspark.sql.types import StructType, StructField, DateType, StringType

from stock_data import APP_NAME, SCHEMA, METASTORE_SCHEMA, Column

MODULE_NAME = "PUSH_DATA"
METASTORE__LAST_DATA = f"{METASTORE_SCHEMA}.{APP_NAME}__{MODULE_NAME}__LAST_DATA"
METASTORE__LAST_DATA_SCHEMA = '''
    TICKER VARCHAR(3),
    TRADING_DATE DATE
'''


metastore__last_data__schema = StructType(
    [
        StructField(Column.ticker, StringType(), True),
        StructField(Column.date, DateType(), True),
    ]
)