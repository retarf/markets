import pytest

from datetime import date

from stock_data import Column, spark, input_schema
from stock_data.load_data import metastore__last_data__schema
from stock_data.load_data.operations import (
    get_last_data_date_from_metastore,
    select_incremental_data,
    get_current_last_date_dataframe,
    add_ticker_column,
    get_ticker_from_path,
    get_ds_from_path,
)


# @pytest.mark.parametrize(
#     "test_data",
#     [
#         ([(None, 2.0, 3.0, 2.0, 3.0, 5.0)]),
#         ([(date(2021, 1, 1), None, 3.0, 2.0, 3.0, 5.0)]),
#         ([(date(2021, 1, 1), 2.0, None, 2.0, 3.0, 5.0)]),
#         ([(date(2021, 1, 1), 2.0, 3.0, None, 3.0, 5.0)]),
#         ([(date(2021, 1, 1), 2.0, 3.0, 2.0, None, 5.0)]),
#         ([(date(2021, 1, 1), 2.0, 3.0, 2.0, 3.0, None)]),
#     ]
# )
# def inny_test():
#     pass


@pytest.mark.parametrize(
    "test_data,test_date,result",
    [
        ([
            ("TST", date(2021, 1, 1) ),
            ("TST", date(2021, 1, 2) ),
            ("TST", date(2021, 1, 5) ),
            ("DST", date(2021, 1, 9) ),
            ("DST", date(2021, 1, 3) ),
            ("TST", date(2021, 1, 7) )
        ], 
        "2021-01-06",
        date(2021, 1, 5)),
        ([
            ("TST", date(2021, 1, 1) ),
            ("TST", date(2021, 1, 2) ),
            ("TST", date(2021, 1, 5) ),
            ("DST", date(2021, 1, 9) ),
            ("DST", date(2021, 1, 3) ),
            ("TST", date(2021, 1, 7) )
        ], 
        "2021-01-08",
        date(2021, 1, 7)),
        ([], "2021-01-08", None),
    ]
)
def test__get_last_data_date__with_backfil_should_returns_appropriate_result(test_data, test_date, result):
    test_metastore = spark.createDataFrame(test_data, metastore__last_data__schema)
    metastore_last_date = get_last_data_date_from_metastore(test_metastore, "TST", test_date)

    assert metastore_last_date == result


def test__select_incremental_data__returns_rows_strictly_between_dates():
    test_data = [
        (date(2021, 1, 1), 2.0, 3.0, 2.0, 3.0, 5.0),
        (date(2021, 1, 2), 3.0, 4.0, 3.0, 4.0, 5.0),
        (date(2021, 1, 3), 4.0, 5.0, 4.0, 5.0, 5.0),
        (date(2021, 1, 4), 5.0, 6.0, 5.0, 6.0, 5.0),
        (date(2021, 1, 5), 6.0, 7.0, 6.0, 7.0, 5.0),
        (date(2021, 1, 6), 7.0, 8.0, 7.0, 8.0, 5.0),
    ]
    expected_data = [
        (date(2021, 1, 4), 5.0, 6.0, 5.0, 6.0, 5.0),
        (date(2021, 1, 5), 6.0, 7.0, 6.0, 7.0, 5.0),
    ]
    test_df = spark.createDataFrame(test_data, input_schema)
    expected_df = spark.createDataFrame(expected_data, input_schema)
    last_data_date = date(2021, 1, 3)
    ds = "2021-01-06"

    df = select_incremental_data(test_df, last_data_date, ds)

    assert df.collect() == expected_df.collect()


def test__select_incremental_data__without_start_date_returns_all():
    test_data = [
        (date(2021, 1, 1), 2.0, 3.0, 2.0, 3.0, 5.0),
        (date(2021, 1, 2), 3.0, 4.0, 3.0, 4.0, 5.0),
    ]
    test_df = spark.createDataFrame(test_data, input_schema)

    df = select_incremental_data(test_df, None, "2021-01-06")

    assert df.collect() == test_df.collect()


def test__get_current_last_date_dataframe__returns_last_date():
    test_data = [
        (date(2021, 1, 1), 2.0, 3.0, 2.0, 3.0, 5.0),
        (date(2021, 1, 2), 3.0, 4.0, 3.0, 4.0, 5.0),
        (date(2021, 1, 3), 4.0, 5.0, 4.0, 5.0, 5.0),
        (date(2021, 1, 4), 5.0, 6.0, 5.0, 6.0, 5.0),
        (date(2021, 1, 5), 6.0, 7.0, 6.0, 7.0, 5.0),
        (date(2021, 1, 6), 7.0, 8.0, 7.0, 8.0, 5.0),
    ]
    # get_current_last_date_dataframe selects TICKER + TRADING_DATE, so the
    # input needs a ticker column.
    test_df = add_ticker_column(spark.createDataFrame(test_data, input_schema), "TST")

    result_df = get_current_last_date_dataframe(test_df)

    result = result_df.first()
    assert result[Column.ticker] == "TST"
    assert result[Column.date] == date(2021, 1, 6)


def test__add_ticker_column__returns_appropriate_df():
    test_data = [
        (date(2021, 1, 1), 2.0, 3.0, 2.0, 3.0, 5.0),
        (date(2021, 1, 2), 3.0, 4.0, 3.0, 4.0, 5.0),
        (date(2021, 1, 3), 4.0, 5.0, 4.0, 5.0, 5.0),
        (date(2021, 1, 4), 5.0, 6.0, 5.0, 6.0, 5.0),
        (date(2021, 1, 5), 6.0, 7.0, 6.0, 7.0, 5.0),
        (date(2021, 1, 6), 7.0, 8.0, 7.0, 8.0, 5.0),
    ]
    test_df = spark.createDataFrame(test_data, input_schema)

    result_df = add_ticker_column(test_df, "TST")

    assert Column.ticker in result_df.columns
    assert result_df.count() == len(test_data)
    assert [row[Column.ticker] for row in result_df.collect()] == ["TST"] * len(test_data)


@pytest.mark.parametrize(
    "path,expected",
    [
        ("/project/datalake/STOCK_DATA/dt=2026-06-24/XTB.WA.csv", "XTB.WA"),
        ("/project/datalake/STOCK_DATA/dt=2026-06-24/PKN.WA.csv", "PKN.WA"),
        ("/project/datalake/STOCK_DATA/dt=2026-06-24/xtb.wa.csv", "XTB.WA"),
    ],
)
def test__get_ticker_from_path__preserves_market_suffix(path, expected):
    assert get_ticker_from_path(path) == expected


def test__get_ds_from_path__extracts_partition_date():
    path = "/project/datalake/STOCK_DATA/dt=2026-06-24/XTB.WA.csv"

    assert get_ds_from_path(path) == "2026-06-24"