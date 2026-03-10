SNOWFLAKE_SOURCE_NAME = "net.snowflake.spark.snowflake"
SNOWFLAKE_JDBC_DRIVER = "/project/src/warehouse/snowflake/libs/snowflake-jdbc-3.28.0.jar"
SNOWFLAKE_CONNECTOR = "/project/src/warehouse/snowflake/libs/spark-snowflake_2.13-3.1.7.jar"
JARS_LIST = [SNOWFLAKE_JDBC_DRIVER, SNOWFLAKE_CONNECTOR]
JARS = ','.join(JARS_LIST)