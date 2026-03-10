import logging

from pyspark.sql.types import StructType, StructField, StringType, DateType, DoubleType

from stock_data import spark, Column, PYSPARK_DATE_FORMAT, schema


# last_successful_run = None

# def get_last_dated_directory():
#     pass

logger = logging.getLogger()
logger.setLevel(logging.INFO)





def read_csv_to_dataframe(csv_file_path):
    return spark.read.schema(schema).option("header", True).option("dateFormat", PYSPARK_DATE_FORMAT).csv(csv_file_path)


