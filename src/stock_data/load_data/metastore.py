from datetime import date

from pyspark.sql.functions import col

from warehouse.snowflake.session import get_spark_session
from warehouse.snowflake.table import save_table, load_table

from stock_data import APP_NAME, Column



METASTORE_SCHEMA = "METASTORE"
LAST_DATA_DATE_TABLE = "LAST_TRADING_DATE_TABLE"
TABLE_PATH = f"MARKETS.{METASTORE_SCHEMA}.{LAST_DATA_DATE_TABLE}"


spark = get_spark_session(APP_NAME)


schema = StructType(
    [
        StructField(Column.ticker, StringType(), False),
        StructField(Column.date, DateType(), False),
    ]
)


def save_last_trading_date(ticker: str, last_trading_date: date) -> None:
    '''
        Saves the last trading date for given ticker in metastore.
    '''
    last_date_df = spark.createDataFrame([(ticker, last_trading_date)], schema)
    #TODO: MARKETS db should be replaced by {APP_NAME}
    save_table(last_date_df, table_name=TABLE_PATH)


def load_last_trading_date(ticker: str) -> date | None:
    '''
        loads last trading date for given ticker from metastore. 
        Returns None if no data exists.
    '''
    last_date_df = load_table(spark=TABLE_PATH)
    row = last_date_df.filter( col(Column.ticker) == ticker ).orderBy( col(Column.date).desc() ).first()
    return row[Column.date] if row else None