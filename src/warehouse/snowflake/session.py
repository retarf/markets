import os
from pyspark.sql import SparkSession
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
import re

from warehouse.snowflake import JARS


def get_private_key():
    key_path = os.environ.get('PYSPARK_PRIVATE_KEY_FILE')
    with open(key_path, "rb") as key_file:
        p_key = serialization.load_pem_private_key(
            key_file.read(),
            password = os.environ.get('PYSPARK_PRIVATE_KEY_FILE_PWD').encode(),
            backend = default_backend()
        )
        pkb = p_key.private_bytes(
            encoding = serialization.Encoding.PEM,
            format = serialization.PrivateFormat.PKCS8,
            encryption_algorithm = serialization.NoEncryption()
        )
        pkb = pkb.decode("UTF-8")
        return re.sub("-*(BEGIN|END) PRIVATE KEY-*\n","",pkb).replace("\n","")


def get_spark_session(app_name):
    return SparkSession.builder \
        .config("spark.jars", JARS) \
        .appName(app_name) \
        .getOrCreate()
