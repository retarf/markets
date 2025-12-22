import os
from typing import List

import snowflake.connector as sc


connection_params = {
    'account': os.environ.get('SNOWFLAKE_ACCOUNT'),
    'user': os.environ.get('SNOWFLAKE_USER'),
    'authenticator': 'SNOWFLAKE_JWT',
    'private_key_file': os.environ.get('SNOWFLAKE_PRIVATE_KEY_FILE'),
    'private_key_file_pwd': os.environ.get('SNOWFLAKE_PRIVATE_KEY_FILE_PWD'),
    'warehouse': os.environ.get('SNOWFLAKE_WAREHOUSE'),
    'database': os.environ.get('SNOWFLAKE_DATABASE'),
    # 'schema': os.environ.get('SNOWFLAKE_SCHEMA')
}

SCHEMA = 'RAW'
TABLE_NAME = 'RAW_STOCK_DATA'
TABLE_SCHEMA = '''
    TICKER VARCHAR(3), 
    DATE DATE,
    OPEN DOUBLE PRECISION, 
    HIGH DOUBLE PRECISION, 
    LOW DOUBLE PRECISION,
    CLOSE DOUBLE PRECISION, 
    VOLUME DOUBLE PRECISION, 
    SOURCE_FILE VARCHAR(18), 
    LOAD_TS TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
'''

def execute_queries(queries: List) -> None:
    connection = sc.connect(**connection_params)
    cursor = connection.cursor()
    for query in queries:
        cursor.execute(query)
    cursor.close()

permissions = [
    'GRANT ROLE TRANSFORM TO USER dbt;',
    'GRANT ALL ON WAREHOUSE COMPUTE_WH TO ROLE TRANSFORM;',
    'GRANT ALL ON DATABASE MARKETS TO ROLE TRANSFORM;',
    'GRANT ALL ON ALL SCHEMAS IN DATABASE TO MARKETS TO ROLE TRANSFORM;',
    'GRANT ALL ON FUTURE SCHEMAS IN DATABASE MARKETS TO ROLE TRANSFORM;',
    'GRANT ALL ON ALL TABLES IN SCHEMA MARKETS.RAW TO ROLE TRANSFORM;',
    'GRANT ALL ON FUTURE TABLES IN SCHEMA MARKETS.RAW TO ROLE TRANSFORM;',
]


def upgrade() -> None:
    queries = [
        'CREATE SCHEMA IF NOT EXISTS {};'.format(SCHEMA),
        'CREATE TABLE IF NOT EXISTS {}.{} ({});'.format(SCHEMA, TABLE_NAME, TABLE_SCHEMA),
    ]
    execute_queries(queries)


def downgrade() -> None:
    queries = [
        'DROP TABLE IF EXISTS {}.{} CASCADE;'.format(SCHEMA, TABLE_NAME),
        'DROP SCHEMA IF EXISTS {};'.format(SCHEMA),
    ]
    execute_queries(queries)
