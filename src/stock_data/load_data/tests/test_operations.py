import pytest

from datetime import date

from stock_data import APP_NAME, spark, input_schema, output_schema
from stock_data.load_data import metastore__last_data__schema
from stock_data.load_data.operations import (
    get_last_data_date_from_metastore,
    get_recent_data,
    get_current_last_date_dataframe,
    add_ticker_column
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


def test__get_recent_data__should_returns_appropriate_result():
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

    df = get_recent_data(test_df, last_data_date, ds)

    assert df.collect() == expected_df.collect()


def test__get_current_last_date_dataframe__returns_last_date():
    test_data = [
        (date(2021, 1, 1), 2.0, 3.0, 2.0, 3.0, 5.0),
        (date(2021, 1, 2), 3.0, 4.0, 3.0, 4.0, 5.0),
        (date(2021, 1, 3), 4.0, 5.0, 4.0, 5.0, 5.0),
        (date(2021, 1, 4), 5.0, 6.0, 5.0, 6.0, 5.0),
        (date(2021, 1, 5), 6.0, 7.0, 6.0, 7.0, 5.0),
        (date(2021, 1, 6), 7.0, 8.0, 7.0, 8.0, 5.0),
    ]
    test_df = spark.createDataFrame(test_data, input_schema)
    expected_df = spark.createDataFrame([{"TRADING_DATE": date(2021, 1, 6)}])

    result_df = get_current_last_date_dataframe(test_df)

    assert expected_df.first() == result_df.first()


def test__add_ticker_column__returns_appropriate_df():
    test_data = [
        (date(2021, 1, 1), 2.0, 3.0, 2.0, 3.0, 5.0),
        (date(2021, 1, 2), 3.0, 4.0, 3.0, 4.0, 5.0),
        (date(2021, 1, 3), 4.0, 5.0, 4.0, 5.0, 5.0),
        (date(2021, 1, 4), 5.0, 6.0, 5.0, 6.0, 5.0),
        (date(2021, 1, 5), 6.0, 7.0, 6.0, 7.0, 5.0),
        (date(2021, 1, 6), 7.0, 8.0, 7.0, 8.0, 5.0),
    ]
    expected_data = [
        ("TST", date(2021, 1, 1), 2.0, 3.0, 2.0, 3.0, 5.0),
        ("TST", date(2021, 1, 2), 3.0, 4.0, 3.0, 4.0, 5.0),
        ("TST", date(2021, 1, 3), 4.0, 5.0, 4.0, 5.0, 5.0),
        ("TST", date(2021, 1, 4), 5.0, 6.0, 5.0, 6.0, 5.0),
        ("TST", date(2021, 1, 5), 6.0, 7.0, 6.0, 7.0, 5.0),
        ("TST", date(2021, 1, 6), 7.0, 8.0, 7.0, 8.0, 5.0),
    ]
    test_df = spark.createDataFrame(test_data, input_schema)
    expected_df = spark.createDataFrame(expected_data, output_schema)

    result_df = add_ticker_column(test_df, "TST")

    assert expected_df.collect() == result_df.collect()