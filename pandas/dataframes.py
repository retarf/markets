from connection import get_cursor, fetch_dataframe


def get_stg_stock_data():
    sql = 'select * from stg_stock_data'
    cursor = get_cursor()
    return fetch_dataframe(cursor, sql)

