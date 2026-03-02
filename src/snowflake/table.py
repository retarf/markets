from pyspark.sql import SparkSession
from src.snowflake.session import get_spark_session, sfOptions, SNOWFLAKE_SOURCE_NAME


def load_table(spark: SparkSession, table_name: str):
    return spark.read.format(SNOWFLAKE_SOURCE_NAME).options(**sfOptions).option("dbtable", table_name).load()

def save_table(df, table_name: str) -> None:
    df.write.format(SNOWFLAKE_SOURCE_NAME).options(**sfOptions).option("dbtable", table_name).save()