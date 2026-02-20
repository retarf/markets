from connection import get_cursor, fetch_dataframe


def get_mart_trend_data():
    return fetch_dataframe('mart_trend_data')


def get_data_for_ticker(df, ticker):
    return df[df['TICKER'] == ticker].sort_values(['TICKER', 'TRADING_DATE'])


def get_trend_start_data(df, ticker):
    pass




