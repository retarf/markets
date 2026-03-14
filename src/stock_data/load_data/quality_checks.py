from pyspark.sql.functions import col

from stock_data import APP_NAME, Column


class QualityError(Exception):

    def __init__(self, msg):
        self.msg = f"{APP_NAME}: {msg}"
        super().__init__(self.msg)


def not_null_quality_check(df):
    df = df.filter(
        col(Column.date).isNull() | 
        col(Column.open).isNull() | 
        col(Column.high).isNull() | 
        col(Column.low).isNull() | 
        col(Column.close).isNull() | 
        col(Column.volume).isNull()
    )

    if df.head(1):
        raise QualityError("Not null quality check failed")


def greater_than_zero_quality_check(df):
    df = df.filter(
        (col(Column.open) <= 0) | 
        (col(Column.high) <= 0) | 
        (col(Column.low) <= 0) | 
        (col(Column.close) <= 0) | 
        (col(Column.volume) <= 0) 
    )

    if df.head(1):
        raise QualityError("Greater than zero quality check failed")


def low_greater_than_high_quality_check(df):
    df = df.filter(
        col(Column.high) < col(Column.low)
    )

    if df.head(1):
        raise QualityError("Low greater than high quality check failed")