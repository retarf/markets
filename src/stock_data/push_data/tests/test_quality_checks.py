import pytest

from datetime import date

from warehouse.snowflake.session import get_spark_session

from stock_data import APP_NAME, schema, spark
from stock_data.push_data.quality_checks import (
    QualityError, 
    not_null_quality_check,
    greater_than_zero_quality_check,
    low_greater_than_high_quality_check
)


@pytest.mark.parametrize(
    "test_data",
    [
        ([(None, 2.0, 3.0, 2.0, 3.0, 5.0)]),
        ([(date(2021, 1, 1), None, 3.0, 2.0, 3.0, 5.0)]),
        ([(date(2021, 1, 1), 2.0, None, 2.0, 3.0, 5.0)]),
        ([(date(2021, 1, 1), 2.0, 3.0, None, 3.0, 5.0)]),
        ([(date(2021, 1, 1), 2.0, 3.0, 2.0, None, 5.0)]),
        ([(date(2021, 1, 1), 2.0, 3.0, 2.0, 3.0, None)]),
    ]
)
def test__not_null_quality_check__with_nulls_should_raise_exception(test_data):
    df = spark.createDataFrame(test_data, schema)
    with pytest.raises(QualityError, match=f"{APP_NAME}: Not null quality check failed"):
        not_null_quality_check(df)


@pytest.mark.parametrize(
    "test_data",
    [
        ([(date(2021, 1, 1), 0.0, 3.0, 2.0, 3.0, 5.0)]),
        ([(date(2021, 1, 1), 2.0, 0.0, 2.0, 3.0, 5.0)]),
        ([(date(2021, 1, 1), 2.0, 3.0, 0.0, 3.0, 5.0)]),
        ([(date(2021, 1, 1), 2.0, 3.0, 2.0, 0.0, 5.0)]),
        ([(date(2021, 1, 1), 2.0, 3.0, 2.0, 3.0, 0.0)]),
    ]
)
def test__greater_than_zero_quality_check__with_zero_should_raise_exception(test_data):
    df = spark.createDataFrame(test_data, schema)
    with pytest.raises(QualityError, match=f"{APP_NAME}: Greater than zero quality check failed"):
        greater_than_zero_quality_check(df)


@pytest.mark.parametrize(
    "test_data",
    [
        ([(date(2021, 1, 1), 2.0, 2.0, 3.0, 3.0, 5.0)]),
    ]
)
def test__low_grater_then_high_quality_check__with_low_greater_than_high_raise_exception(test_data):
    df = spark.createDataFrame(test_data, schema)
    with pytest.raises(QualityError, match=f"{APP_NAME}: Low greater than high quality check failed"):
        low_greater_than_high_quality_check(df)