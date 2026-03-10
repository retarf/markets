import os


def get_sfOptions():
    return {
        'sfURL': f'{os.environ.get('SNOWFLAKE_ACCOUNT')}.snowflakecomputing.com',
        'sfUser': os.environ.get('PYSPARK_USER'),
        'sfRole': 'TRANSFORM',
        "pem_private_key": get_private_key(),
        'sfSchema': os.environ.get('SNOWFLAKE_SCHEMA'),
        'sfDatabase': os.environ.get('SNOWFLAKE_DATABASE'),
        'sfWarehouse': os.environ.get('SNOWFLAKE_WAREHOUSE'),
    }