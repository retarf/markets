import os
from typing import List

import snowflake.connector as sc


class COLORS:
    RESET = '\033[0m'
    OK = '\033[32m'
    FAIL = '\033[31m'


DATABASE = os.environ.get('SNOWFLAKE_DATABASE')
user = os.environ.get('SNOWFLAKE_ADMIN_USER')

# connection_params = {
#     'account': os.environ.get('SNOWFLAKE_ACCOUNT'),
#     'user': os.environ.get('SNOWFLAKE_USER'),
#     'authenticator': 'SNOWFLAKE_JWT',
#     'private_key_file': os.environ.get('SNOWFLAKE_PRIVATE_KEY_FILE'),
#     'private_key_file_pwd': os.environ.get('SNOWFLAKE_PRIVATE_KEY_FILE_PWD'),
#     'warehouse': os.environ.get('SNOWFLAKE_WAREHOUSE'),
#     'database': os.environ.get('SNOWFLAKE_DATABASE'),
#     # 'schema': os.environ.get('SNOWFLAKE_SCHEMA')
# }


connection_params = {
    'account': os.environ.get('SNOWFLAKE_ACCOUNT'),
    'user': user,
    'password': os.environ.get('SNOWFLAKE_ADMIN_PASSWORD'),
    # 'authenticator': 'SNOWFLAKE_JWT',
    # 'warehouse': os.environ.get('SNOWFLAKE_WAREHOUSE'),
    # 'database': os.environ.get('SNOWFLAKE_DATABASE'),
    # 'schema': os.environ.get('SNOWFLAKE_SCHEMA')
}

RAW_SCHEMA = 'RAW'
DEV_SCHEMA = 'DEV'
TABLE_NAME = 'RAW_STOCK_DATA'
TABLE_SCHEMA = '''
    TICKER VARCHAR(3), 
    TRADING_DATE DATE,
    OPEN DOUBLE PRECISION, 
    HIGH DOUBLE PRECISION, 
    LOW DOUBLE PRECISION,
    CLOSE DOUBLE PRECISION, 
    VOLUME DOUBLE PRECISION, 
    SOURCE_FILE VARCHAR(18), 
    LOAD_TS TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
'''

permissions = [
    'DROP ROLE IF EXISTS TRANSFORM;',
    'CREATE ROLE TRANSFORM;',
    'GRANT ROLE TRANSFORM TO USER dbt;',
    'GRANT ROLE TRANSFORM TO ROLE ACCOUNTADMIN;',
    'GRANT OPERATE ON WAREHOUSE COMPUTE_WH TO ROLE TRANSFORM;',
    'GRANT ALL ON WAREHOUSE COMPUTE_WH TO ROLE TRANSFORM;',
    'GRANT ALL ON DATABASE MARKETS TO ROLE TRANSFORM;',
    'GRANT ALL ON ALL SCHEMAS IN DATABASE MARKETS TO ROLE TRANSFORM;',
    'GRANT ALL ON FUTURE SCHEMAS IN DATABASE MARKETS TO ROLE TRANSFORM;',
    'GRANT ALL ON ALL TABLES IN SCHEMA RAW TO ROLE TRANSFORM;',
    'GRANT ALL ON FUTURE TABLES IN SCHEMA RAW TO ROLE TRANSFORM;',
]


def get_public_key_string(public_key_line_list: List[str]) -> str:
    return ''.join([line.rstrip('\n') for line in public_key_line_list if not 'PUBLIC KEY' in line])


def get_public_key():
    public_key = None
    with open(os.environ.get('SNOWFLAKE_PUBLIC_KEY_FILE'), 'r') as f:
        public_key = get_public_key_string(f.readlines())
    return public_key


def execute_queries(queries: List) -> None:
    ctx = sc.connect(**connection_params)
    print(f'IS CONNECTION VALID: {ctx.is_valid()}')
    cursor = ctx.cursor()
    for query in queries:
        try:
            print(f'QUERY: {query}')
            cursor.execute(query)
            results = cursor.fetchall()
            print(f'{COLORS.OK}RESULT: {results[0]}{COLORS.RESET}')
        except Exception:
            results = cursor.fetchall()
            print(f'{COLORS.FAIL}ERROR RESULT: {results}{COLORS.RESET}')
    cursor.close()



def upgrade() -> None:
    queries = [
        # 'USE ROLE USERADMIN',
        'USE ROLE ACCOUNTADMIN',
        "CREATE OR REPLACE USER dbt LOGIN_NAME = 'dbt' DEFAULT_WAREHOUSE = COMPUTE_WH DEFAULT_ROLE=TRANSFORM TYPE=SERVICE;",
        "ALTER USER dbt SET RSA_PUBLIC_KEY = '{}';".format(get_public_key()),
        #'USE ROLE TRANSFORM',
        'CREATE DATABASE IF NOT EXISTS {};'.format(DATABASE),
        'USE DATABASE {};'.format(DATABASE),
        'CREATE SCHEMA IF NOT EXISTS {};'.format(RAW_SCHEMA),
        'CREATE SCHEMA IF NOT EXISTS {};'.format(DEV_SCHEMA),
        'CREATE TABLE IF NOT EXISTS {}.{} ({});'.format(RAW_SCHEMA, TABLE_NAME, TABLE_SCHEMA),
        *permissions,
    ]
    execute_queries(queries)


def downgrade() -> None:
    queries = [
        'DROP TABLE IF EXISTS {}.{} CASCADE;'.format(RAW_SCHEMA, TABLE_NAME),
        'DROP SCHEMA IF EXISTS {};'.format(RAW_SCHEMA),
    ]
    execute_queries(queries)

upgrade()