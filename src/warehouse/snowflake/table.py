from pyspark.sql import SparkSession

from warehouse.snowflake import SNOWFLAKE_SOURCE_NAME
from warehouse.snowflake.session import get_spark_session
from warehouse.snowflake.utils import get_sfOptions


def load_table(spark: SparkSession, table_name: str):
    return spark.read.format(SNOWFLAKE_SOURCE_NAME).options(**get_sfOptions()).option("dbtable", table_name).load()

def save_table(df, table_name: str) -> None:
    df.write.format(SNOWFLAKE_SOURCE_NAME).options(**get_sfOptions()).option("dbtable", table_name).save()