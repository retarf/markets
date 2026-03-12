from pyspark.sql import SparkSession

from warehouse.snowflake import SNOWFLAKE_SOURCE_NAME
from warehouse.snowflake.session import get_sfOptions, get_spark_session


def load_table(spark: SparkSession, table_name: str):
    return spark.read.format(SNOWFLAKE_SOURCE_NAME).options(**get_sfOptions()).option("dbtable", table_name).load()


def save_table(df, table_name: str, mode: str = "append") -> None:
    df.write.format(SNOWFLAKE_SOURCE_NAME).options(**get_sfOptions()).option("dbtable", table_name).mode(mode).save()