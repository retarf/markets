import os
import snowflake.connector as sc

params = {
    'account': os.environ.get('SNOWFLAKE_ACCOUNT'),
    'user': os.environ.get('SNOWFLAKE_USER'),
    'authenticator': 'SNOWFLAKE_JWT',
    'private_key_file': os.environ.get('SNOWFLAKE_PRIVATE_KEY_FILE'),
    'private_key_file_pwd': os.environ.get('SNOWFLAKE_PRIVATE_KEY_FILE_PWD'),
    'warehouse': os.environ.get('SNOWFLAKE_WAREHOUSE'),
    'database': os.environ.get('SNOWFLAKE_DATABASE'),
    'schema': os.environ.get('SNOWFLAKE_SCHEMA')
}

def connect():
    return sc.connect(**params)